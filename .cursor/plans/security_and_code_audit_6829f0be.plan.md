---
name: Security and code audit
overview: "A security audit and code review of the Marvel chatbot repo to harden it for public release: fix broken authorization, remove dangerous patterns, align docs with reality, and tighten config and dependencies."
todos: []
isProject: false
---

# Security Audit and Code Review Plan – Marvel Chatbot (Public Repo)

This plan addresses security issues, misleading documentation, and code-quality items so the project is safe and presentable for a public/LinkedIn launch.

---

## 1. Critical security issues

### 1.1 No server-side authorization on chat and history

**Problem:** The backend never validates that the requester is the owner of the data.

- `**[backend/server_prime.py](backend/server_prime.py)`**  
  - `GET /history/<chat_id>` (lines 227–234) and `GET /chat/<chat_id>/<user_id>` (206–214) return chat history for any `chat_id` with no check that the caller owns that chat.  
  - `GET /chats/<user_id>` (218–225) returns all sessions for any `user_id` (anyone can list any user’s chats by guessing/enumerating MongoDB ObjectIds).  
  - `POST /chat-response` (184–208) accepts any `userId`/`chatId` and writes to DB; no verification that the Bearer token (or any token) matches the claimed `userId`.

**Impact:** Any user can read or overwrite another user’s chats; full data breach and data corruption risk.

**Fix:**

- Introduce a minimal auth layer: e.g. signed JWT (or signed session token) issued at login containing `user_id` (and optional `chat_id` where relevant).  
- For every protected route (`/chat-response`, `/chats/<user_id>`, `/history/<chat_id>`, `/chat/<chat_id>/<user_id>`):  
  - Parse and verify the token from `Authorization: Bearer <token>`.  
  - Ensure the authenticated `user_id` matches the resource being accessed (for `/history/<chat_id>` and `/chat/<chat_id>/<user_id>`, verify the chat belongs to that user via DB).
- Do not rely on the client sending `userId` in the body or path as the only “auth”; the server must derive identity from a verified token.

### 1.2 “Auth token” is just the raw MongoDB ObjectId

**Problem:** The frontend sends `userId` (MongoDB `_id` string) as the “token” in `Authorization: Bearer <userId>`. There is no signature or secret; anyone who knows or can guess an ObjectId can impersonate that user.

**Location:**  

- Frontend: `[frontend/src/api/chatapi.js](frontend/src/api/chatapi.js)` (lines 6–11, 46–50), `[frontend/src/contexts/AuthContext.jsx](frontend/src/contexts/AuthContext.jsx)` (localStorage `userId`).  
- Backend: no validation of this “token” on protected routes.

**Fix:**  

- Issue a real token at login (e.g. JWT with `user_id`, expiry, signed with a server secret).  
- Store that token in localStorage (or httpOnly cookie if you add cookie support).  
- Send that token in `Authorization: Bearer <token>` and validate it on the server for all protected routes.  
- Optionally keep a short-lived session in DB and bind `chat_id` to `user_id` server-side so `/history/<chat_id>` can be authorized by “chat belongs to current user”.

### 1.3 Dangerous use of `eval()` in backend

**Problem:** `[backend/phase_4.py](backend/phase_4.py)` line 692: `suggestions = eval(raw_text.strip())`. The input is LLM output. If the model or an attacker can influence that output, this is remote code execution.

**Fix:**  

- Replace with safe parsing: e.g. `json.loads(...)` for JSON, or a strict regex/parser for a small allowed format.  
- If `phase_4.py` is not used in production, document that and consider removing or guarding this path so it is never exposed.

### 1.4 User input used in MongoDB `$regex` without sanitization

**Problem:** In `[backend/server_prime.py](backend/server_prime.py)` (lines 94–96), `keywords` from `extract_keywords(question)` are interpolated into `$regex`. Keywords are LLM-derived, but if they ever contain regex metacharacters (e.g. `.`*, `(.)`, `+`, `{}`), you risk ReDoS or unexpected matching.

**Fix:**  

- Escape regex metacharacters in each keyword before building the query (e.g. use `re.escape(kw)`), or restrict to a strict allowlist (e.g. alphanumeric + spaces).  
- Optionally cap length of each keyword and total number of keywords.

### 1.5 No rate limiting

**Problem:** Login, register, and chat endpoints have no rate limiting. This allows brute-force on passwords, signup abuse, and cost/DoS abuse of the Groq chat endpoint.

**Fix:**  

- Add rate limiting (e.g. Flask-Limiter or a simple in-memory/dict-based limiter per IP) for:  
  - `POST /login` and `POST /register` (stricter, e.g. 5–10/min per IP).  
  - `POST /chat`, `POST /chat-response` (e.g. per-IP and optionally per-user after auth).
- Document that production should use a shared store (e.g. Redis) if you scale to multiple instances.

### 1.6 Debug mode and production entrypoint

**Problem:** `[backend/server_prime.py](backend/server_prime.py)` line 306: `app.run(port=5001, debug=True)`. If someone runs the app with `python server_prime.py` in production, debug mode exposes stack traces and reloader.

**Fix:**  

- Use an environment variable (e.g. `FLASK_ENV=production` or `DEBUG=0`) and set `debug=False` when in production.  
- In README and any “run locally” instructions, state that production must use `gunicorn` (as in `[render.yaml](render.yaml)`) and never run `python server_prime.py` in production.

### 1.7 Password and email validation

**Problem:**  

- No minimum length or complexity for passwords (e.g. in `[backend/server_prime.py](backend/server_prime.py)` register route).  
- No email format validation; anything is stored as “email”.

**Fix:**  

- Enforce a minimum password length (e.g. 8 characters) and optionally complexity.  
- Validate email format (regex or a small library) and reject invalid addresses.  
- Return clear validation errors (e.g. “Password must be at least 8 characters”) without leaking whether the email exists (on login).

---

## 2. Configuration and secrets

### 2.1 Environment variable naming

**Problem:** Backend uses `os.getenv("mongo")` (`[backend/server_prime.py](backend/server_prime.py)` line 34) while README and many examples use `MONGO_URI`. This is confusing and error-prone.

**Fix:**  

- Use a single name everywhere, e.g. `MONGODB_URI` or `MONGO_URI`, and document it in README and `.env.example`.  
- Update all backend code (including `inspect_db.py`, `serp_helper.py`, phase_*.py if they are still referenced) to use the same variable name.

### 2.2 README and .env.example consistency

**Problem:**  

- README (e.g. around line 121) shows `MONGO_URI=...` but backend expects `mongo=...`.  
- Backend `[.env.example](backend/.env.example)` uses `mongo=...`; align with README and code.

**Fix:**  

- Standardize on one env name (e.g. `MONGO_URI`) in README, `.env.example`, and all Python code.  
- Ensure no real secrets or real URLs appear in README (only placeholders).

### 2.3 Hardcoded / wrong URLs in backend

**Problem:** In `[backend/server_prime.py](backend/server_prime.py)` line 264, the root route HTML contains a hardcoded link to `https://rag-model-by-devang.netlify.app` and text saying "marvel-nine-coral.vercel.app", which is inconsistent and may be wrong.

**Fix:**  

- Use a single config value (e.g. `FRONTEND_URL` or `PUBLIC_APP_URL`) for the link and label, or remove the link if not needed.  
- Avoid mixing different hostnames unless intentional (e.g. “try the app at …”).

---

## 3. Documentation vs implementation

### 3.1 JWT claim vs actual behavior

**Problem:** README states “JWT Authentication” and “Server issues secure JWT tokens”. The app does not use JWT; it uses a raw MongoDB ObjectId as “token”.

**Fix:**  

- Either implement proper JWT (or signed session tokens) as in 1.1/1.2 and then keep the README as-is, or change README to describe the current auth (e.g. “session token” or “user id–based auth”) and add a short “Security” or “Auth” section that matches the code.  
- Prefer implementing proper tokens so the README remains accurate and the system is secure.

### 3.2 API path documentation

**Problem:** README lists paths like `POST /api/register`, `GET /api/chat/history`, etc., but the actual routes are `/register`, `/chat-response`, `/history/<chat_id>`, `/chats/<user_id>`.

**Fix:**  

- Update README “API Endpoints” (and any Postman/example snippets) to match the real routes in `[backend/server_prime.py](backend/server_prime.py)`.  
- Optionally add a short “API” section that lists method, path, and purpose for each endpoint.

---

## 4. Code quality and cleanliness (for public repo)

### 4.1 Remove or gate debug logging in frontend

**Problem:** `[frontend/src/api/auth.js](frontend/src/api/auth.js)` uses `console.log` for parsed login/register data and stored `userId`. In production this can leak PII and look unprofessional.

**Fix:**  

- Remove these `console.log` calls or wrap them in a dev-only check (e.g. `import.meta.env.DEV` or a small logger that is no-op in production).

### 4.2 Duplicate / test-only code

**Problem:**  

- `AuthAndTheme.jsx` and `test.jsx` look like alternate or test implementations; `LoginRegister.jsx` and `AuthContext.jsx` appear to be the real auth flow.  
- Multiple backend entry points: `phase_1.py`–`phase_4.py`, `test.py`, `server_prime.py`. It’s unclear which is the canonical API and which are scripts or legacy.

**Fix:**  

- Remove or move test-only components (e.g. `test.jsx`, `AuthAndTheme.jsx`) so the main app and README describe a single, clear flow.  
- In README, state that the production API is `server_prime.py` (and gunicorn), and describe phase_*.py / test.py as scripts or deprecated so reviewers don’t assume they’re part of the live API.  
- If `phase_4.py` is never deployed, note that and fix or remove the `eval()` there.

### 4.3 Dependency versions

**Problem:**  

- `[backend/requirements.txt](backend/requirements.txt)` has no version pins; builds can pull different (potentially vulnerable) versions over time.  
- Frontend `package.json` uses ranges (e.g. `^`); acceptable but consider locking for reproducible builds.

**Fix:**  

- Pin backend dependencies to major.minor (or exact) versions and re-pin after a quick check for known CVEs (e.g. `pip list --outdated`, or a quick scan with `pip-audit` or similar).  
- Optionally add a one-line note in README on how to run a security check (e.g. `pip-audit`, `npm audit`).

---

## 5. Optional hardening (short list)

- **CORS:** If the frontend origin is known (e.g. Netlify URL), restrict `Access-Control-Allow-Origin` to that origin instead of `*`.  
- **Headers:** Add security headers (e.g. `X-Content-Type-Options: nosniff`, `X-Frame-Options`) on the Flask app if the same server ever serves HTML or is embedded.  
- **HTTPS:** Ensure Render/Netlify use HTTPS and that the app doesn’t force HTTP for API calls in production.  
- **render.yaml:** Document in README that secrets (`mongo`, `GROQ_API_KEY`, etc.) must be set in the Render dashboard (no secrets in `render.yaml`).

---

## 6. Suggested order of work

1. **Auth and authorization** (1.1, 1.2): Implement real tokens and enforce ownership on all chat/history endpoints.
2. **Remove eval and fix regex** (1.3, 1.4): Replace `eval()` in phase_4, escape regex in server_prime.
3. **Rate limiting and debug** (1.5, 1.6): Add rate limits; make debug conditional.
4. **Validation** (1.7): Password length and email format.
5. **Config and docs** (2.x, 3.x): Env names, README accuracy, API paths, hardcoded URLs.
6. **Cleanup** (4.x): Console logs, duplicate/test code, dependency pinning and optional audit.

This order fixes the highest-impact security issues first, then aligns the repo with documentation and polishes it for public visibility.