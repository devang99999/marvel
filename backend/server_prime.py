import os
import re
import time
import json
import uuid
import requests
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

load_dotenv()
app = Flask(__name__)

# JWT config (required for protected routes)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY or SECRET_KEY environment variable is not set.")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "168"))  # 7 days default

# Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "60 per minute"])

# CORS: allow all origins so frontend (Vercel, localhost) never gets CORS/405
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
    response.headers["Access-Control-Expose-Headers"] = "Content-Type"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def cors_preflight(path):
    return "", 204

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "path": request.path, "method": request.method}), 405

# MongoDB Setup (MONGO_URI; fallback to legacy "mongo" for backward compatibility)
MONGO_URI = os.getenv("MONGO_URI") or os.getenv("mongo")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set.")

client = MongoClient(MONGO_URI)
db = client["marvel_crawler"]
classified_collection = db["classified_chunks"]
users_collection = db["users"]
chat_sessions_collection = db["chat_sessions"]
chat_history_collection = db["chat_history"]

# Groq API Setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Use current production model (llama3-8b-8192 is deprecated)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
SEARCH_LIMIT = 5

# Auth: JWT helpers and validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
MIN_PASSWORD_LENGTH = 8

def get_user_id_from_token():
    """Extract and verify JWT from Authorization: Bearer <token>. Returns user_id string or None."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator: require valid JWT; inject user_id as first arg after request context."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        user_id = get_user_id_from_token()
        if not user_id:
            return jsonify({"error": "Unauthorized", "message": "Valid token required"}), 401
        return f(user_id, *args, **kwargs)
    return wrapped

def chat_belongs_to_user(chat_id: str, user_id: str) -> bool:
    """Return True if this chat_id is owned by user_id."""
    return chat_sessions_collection.find_one({"chat_id": chat_id, "user_id": user_id}) is not None

# 🧠 Extract keywords using Groq (LLM-based)
def extract_keywords(question):
    prompt = f"""
Extract the most important Marvel-related keywords from the following user question. Return a JSON list of 1-3 lowercase keywords only, without explanation.

Question:
"{question}"
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a keyword extractor for Marvel questions. Return only a JSON list of keywords."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }

    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
        res.raise_for_status()
        text = res.json()["choices"][0]["message"]["content"]
        keywords = json.loads(text.strip())
        if isinstance(keywords, list):
            return keywords
    except Exception as e:
        print(f"❌ Keyword extraction failed: {e}")
    return []

# 🔎 Search classified MongoDB chunks by keyword (regex-escaped to prevent ReDoS/injection)
def search_chunks(keywords, limit=SEARCH_LIMIT):
    if not keywords:
        return []
    # Cap and escape keywords for safe $regex use
    safe_keywords = [re.escape(str(kw).strip())[:100] for kw in keywords[:10] if kw]
    if not safe_keywords:
        return []
    query = {"$or": []}
    for kw in safe_keywords:
        query["$or"].append({"classified.topic": {"$regex": kw, "$options": "i"}})
        query["$or"].append({"classified.tags": {"$regex": kw, "$options": "i"}})

    results = classified_collection.find(query).limit(limit * 2)  # Oversample in case of bad matches
    matched_chunks = []

    for doc in results:
        for chunk in doc.get("classified", []):
            if any(kw.lower() in chunk.get("topic", "").lower() for kw in keywords) or \
               any(any(kw.lower() in tag.lower() for tag in chunk.get("tags", [])) for kw in keywords):
                matched_chunks.append(chunk)
            if len(matched_chunks) >= limit:
                return matched_chunks

    return matched_chunks

# 🤖 Generate an answer using Groq
def generate_answer(question, context_chunks):
    context_text = "\n\n".join(
        f"Topic: {chunk.get('topic', '')}\nCharacters: {', '.join(chunk.get('characters', []))}\nTags: {', '.join(chunk.get('tags', []))}"
        for chunk in context_chunks
    )

    prompt = f"""
You are a Marvel chatbot God. you are like a marvel god, you are created by Devang Gandhi who is an AI engineer, and you are still new and getting improver day by day, answer the question below in a helpful and concise way.

Context:
{context_text}

Question:
{question}

Answer:
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful Marvel chatbot assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 500
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        answer = response.json()["choices"][0]["message"]["content"]
        return answer.strip()
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
        return "Sorry, I couldn't generate an answer at this time."

# 🚀 Chat route (unauthenticated RAG-only; use /chat-response for session persistence)
@app.route("/chat", methods=["POST"])
@limiter.limit("60 per minute")
def chat():
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    print(f"🧾 Received question: {question}")
    keywords = extract_keywords(question)
    print(f"🔍 Extracted keywords: {keywords}")

    matched_chunks = search_chunks(keywords)
    if not matched_chunks:
        return jsonify({"answer": "I couldn't find relevant information to answer that."})

    answer = generate_answer(question, matched_chunks)
    return jsonify({"answer": answer})

# Chat response (frontend: messages + chatId) — user_id from JWT only
@app.route("/chat-response", methods=["POST"])
@limiter.limit("30 per minute")
@require_auth
def chat_response(user_id):
    data = request.json or {}
    messages = data.get("messages", [])
    chat_id = (data.get("chatId") or "").strip()
    if not messages:
        return jsonify({"error": "messages are required"}), 400
    question = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            question = (msg.get("content") or "").strip()
            break
    if not question:
        return jsonify({"error": "No user message in messages"}), 400
    keywords = extract_keywords(question)
    matched_chunks = search_chunks(keywords)
    answer = generate_answer(question, matched_chunks)
    source = "database" if matched_chunks else "groq_only"
    if not chat_id:
        chat_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    title = (question[:50] + "…") if len(question) > 50 else question
    chat_sessions_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"chat_id": chat_id, "user_id": user_id, "title": title, "updated_at": now}, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    chat_history_collection.insert_one({"chat_id": chat_id, "user_id": user_id, "question": question, "answer": answer, "timestamp": now})
    return jsonify({"answer": answer, "chat_id": chat_id, "source": source, "chunks_used": len(matched_chunks)})

# GET /chat/<chat_id>/<user_id> — alias for history; path user_id ignored, auth from token
@app.route("/chat/<chat_id>/<user_id>", methods=["GET"])
@require_auth
def get_chat_history_legacy(auth_user_id, chat_id, user_id_path):
    if not chat_belongs_to_user(chat_id, auth_user_id):
        return jsonify({"error": "Forbidden", "message": "Chat not found or access denied"}), 403
    try:
        docs = list(chat_history_collection.find({"chat_id": chat_id}).sort("timestamp", 1))
        return jsonify([{"question": d["question"], "answer": d["answer"]} for d in docs])
    except Exception as e:
        print(f"❌ get_chat_history_legacy: {e}")
        return jsonify([])


@app.route("/chats/<user_id>", methods=["GET"])
@require_auth
def get_chats(auth_user_id, user_id):
    if auth_user_id != user_id:
        return jsonify({"error": "Forbidden", "message": "Cannot list another user's chats"}), 403
    try:
        sessions = list(chat_sessions_collection.find({"user_id": user_id}).sort("updated_at", -1))
        return jsonify([{"chat_id": s["chat_id"], "title": s.get("title", "Untitled"), "last_updated": s.get("updated_at")} for s in sessions])
    except Exception as e:
        print(f"❌ get_chats: {e}")
        return jsonify([])

@app.route("/history/<chat_id>", methods=["GET"])
@require_auth
def get_history(user_id, chat_id):
    if not chat_belongs_to_user(chat_id, user_id):
        return jsonify({"error": "Forbidden", "message": "Chat not found or access denied"}), 403
    try:
        docs = list(chat_history_collection.find({"chat_id": chat_id}).sort("timestamp", 1))
        return jsonify([{"question": d["question"], "answer": d["answer"]} for d in docs])
    except Exception as e:
        print(f"❌ get_history: {e}")
        return jsonify([])

@app.route("/recommendations", methods=["POST"])
def recommendations():
    data = request.json or {}
    messages = data.get("messages", [])
    suggestions = []
    if messages:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user = (msg.get("content") or "").strip()
                if last_user:
                    kw = extract_keywords(last_user)
                    if kw:
                        suggestions = [f"More about {k}" for k in kw[:3]]
                break
    if not suggestions:
        suggestions = ["Iron Man", "Captain America", "Marvel Cinematic Universe"]
    return jsonify(suggestions)

# 🌐 Root route (GET only) — minimal HTML so visiting the URL doesn’t show a black/blank screen
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://rag-model-by-devang.netlify.app")

@app.route("/", methods=["GET"])
def home():
    label = (FRONTEND_URL or "").replace("https://", "").replace("http://", "").split("/")[0] or "the app"
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Marvel Chatbot API</title>
<style>body{{font-family:system-ui,sans-serif;max-width:32rem;margin:3rem auto;padding:0 1rem;background:#f5f5f5;color:#111;}}
h1{{font-size:1.25rem;}} a{{color:#0066cc;}} p{{color:#444;}}</style></head>
<body>
<h1>🚀 Marvel Chatbot API</h1>
<p>Backend is running. Use the app at <a href="{FRONTEND_URL or '#'}">{label}</a>.</p>
<p>If this took a while to load, the service was waking up (Render free tier).</p>
</body></html>"""
    return html

def _issue_jwt(user_id: str):
    """Issue a signed JWT for the given user_id (sub claim)."""
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=JWT_EXPIRY_HOURS)
    return jwt.encode(
        {"sub": user_id, "iat": now, "exp": exp},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )

# 🔐 Auth routes (for frontend login/register)
@app.route("/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    email = (data.get("email") or "").strip()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": f"Password must be at least {MIN_PASSWORD_LENGTH} characters"}), 400
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User with this email already exists"}), 400
    hashed = generate_password_hash(password)
    user_id = users_collection.insert_one({"email": email, "password": hashed}).inserted_id
    user_id_str = str(user_id)
    token = _issue_jwt(user_id_str)
    return jsonify({
        "message": "User registered successfully",
        "token": token,
        "user": {"email": email, "id": user_id_str},
    }), 201

@app.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    email = (data.get("email") or "").strip()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email or password"}), 401
    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    user_id_str = str(user["_id"])
    token = _issue_jwt(user_id_str)
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {"email": user["email"], "id": user_id_str},
    })

# Run the Flask app (use gunicorn in production; never run this script in production)
_debug = os.getenv("FLASK_ENV", "").lower() == "development" or os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "5001")), debug=_debug)
