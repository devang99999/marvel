import os
import time
import json
import uuid
import requests
import certifi
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

# Load .env from same directory as this script so CHATBOT_* and other vars are found no matter where you run from
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)
app = Flask(__name__)

# Allowed origins for CORS (frontend on Vercel + local dev)
CORS_ORIGINS = [
    "https://marvel-nine-coral.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# CORS on every response (including 404/405) so browser never shows "CORS error" instead of real status
@app.after_request
def add_cors_headers(response):
    origin = (request.headers.get("Origin") or "").rstrip("/")
    if origin in CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
    response.headers["Access-Control-Expose-Headers"] = "Content-Type"
    return response

# Handle preflight OPTIONS for any path (so missing routes still return 200 OPTIONS + CORS)
@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def cors_preflight(path):
    return "", 204

# MongoDB Setup (certifi fixes SSL cert verify failed on macOS)
MONGO_URI = os.getenv("mongo")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set.")

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["marvel_crawler"]
classified_collection = db["classified_chunks"]
users_collection = db["users"]
chat_sessions_collection = db["chat_sessions"]
chat_history_collection = db["chat_history"]
qa_cache_collection = db["qa_cache"]

# When to refresh cached external answers (Groq-only / web). After this many days we re-fetch so "internet updates" flow in.
CACHE_TTL_DAYS = int(os.environ.get("QA_CACHE_TTL_DAYS", "30"))

# Groq API Setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
SEARCH_LIMIT = 5

# Chat system prompt: fully dynamic from env. Avoid generic "you're a chatbot" fluff.
CHATBOT_CREATOR_NAME = os.environ.get("CHATBOT_CREATOR_NAME", "the developer")
CHATBOT_CREATOR_TITLE = os.environ.get("CHATBOT_CREATOR_TITLE", "creator")
CHATBOT_PROJECT_NAME = os.environ.get("CHATBOT_PROJECT_NAME", "Marvel Chatbot")
CHATBOT_EXTRA_RULES = os.environ.get("CHATBOT_EXTRA_RULES", "").strip()
# Full custom prompt: set CHATBOT_SYSTEM_PROMPT to override the default. Use \\n for newlines. Placeholders: {{CREATOR_NAME}}, {{CREATOR_TITLE}}, {{PROJECT_NAME}}
CHATBOT_SYSTEM_PROMPT_RAW = os.environ.get("CHATBOT_SYSTEM_PROMPT", "").strip()
# Optional section overrides (used only when CHATBOT_SYSTEM_PROMPT is not set)
CHATBOT_IDENTITY = os.environ.get("CHATBOT_IDENTITY", "").strip()
CHATBOT_TASK = os.environ.get("CHATBOT_TASK", "").strip()
CHATBOT_TONE = os.environ.get("CHATBOT_TONE", "").strip()


def _substitute_prompt(s):
    """Replace placeholders in prompt text."""
    if not s:
        return s
    return (
        s.replace("{{CREATOR_NAME}}", CHATBOT_CREATOR_NAME)
        .replace("{{CREATOR_TITLE}}", CHATBOT_CREATOR_TITLE)
        .replace("{{PROJECT_NAME}}", CHATBOT_PROJECT_NAME)
    )


def _build_chat_system_prompt():
    """Build the main chat system prompt: custom full prompt with placeholders, or dynamic sections from env."""
    if CHATBOT_SYSTEM_PROMPT_RAW:
        s = CHATBOT_SYSTEM_PROMPT_RAW.replace("\\n", "\n")
        return _substitute_prompt(s)

    identity = _substitute_prompt(CHATBOT_IDENTITY) or (
        f"You are {CHATBOT_PROJECT_NAME}. You were created by {CHATBOT_CREATOR_NAME}, {CHATBOT_CREATOR_TITLE}. "
        "You are knowledgeable about the Marvel universe and answer from that expertise."
    )
    task = _substitute_prompt(CHATBOT_TASK) or (
        "Answer the user's question using any context provided when it is relevant; otherwise use your knowledge. "
        "Be accurate and concise. Do not mention data chunks, context, or implementation details—answer naturally."
    )
    creator_rule = (
        f"When asked who made you, who created you, or who built you, answer clearly: {CHATBOT_CREATOR_NAME}, {CHATBOT_CREATOR_TITLE}."
    )
    tone = _substitute_prompt(CHATBOT_TONE) or "Concise, friendly, minimal or no markdown unless the user asks for it."

    parts = [identity, "", "Task: " + task, "", "Rules: " + creator_rule]
    if CHATBOT_EXTRA_RULES:
        parts.append(_substitute_prompt(CHATBOT_EXTRA_RULES))
    parts.extend(["", "Tone: " + tone])
    return "\n".join(parts)


def _normalize_question(q):
    """Normalize for cache lookup (lowercase, single spaces)."""
    if not q or not isinstance(q, str):
        return ""
    return " ".join(q.lower().strip().split())


def _get_cached_answer(question_norm, question_original=None):
    """Return (answer, source) if cache hit and fresh; else (None, None)."""
    if not question_norm and not question_original:
        return None, None
    query = {"question_norm": question_norm} if question_norm else {}
    if question_original:
        query = {"$or": [{"question_norm": question_norm}, {"question": question_original}]} if question_norm else {"question": question_original}
    doc = qa_cache_collection.find_one(query)
    if not doc:
        return None, None
    updated = doc.get("updated_at") or doc.get("timestamp")
    if updated is None:
        return doc.get("answer"), doc.get("source", "cached")  # no timestamp: treat as fresh
    if isinstance(updated, datetime):
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
    else:
        updated = datetime.fromtimestamp(updated, tz=timezone.utc)
    if datetime.now(timezone.utc) - updated > timedelta(days=CACHE_TTL_DAYS):
        return None, None  # stale: caller will refetch and update cache
    return doc.get("answer"), doc.get("source", "cached")


def _save_external_answer(question, question_norm, answer, source):
    """Store or refresh external (Groq-only / web) answer in qa_cache."""
    now = datetime.now(timezone.utc)
    filter_q = {"$or": [{"question_norm": question_norm}, {"question": question}]} if question_norm else {"question": question}
    qa_cache_collection.update_one(
        filter_q,
        {
            "$set": {
                "question": question,
                "question_norm": question_norm,
                "answer": answer,
                "source": source,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


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
        "model": "llama-3.3-70b-versatile",
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

# 🔎 Search classified MongoDB chunks by keyword
def search_chunks(keywords, limit=SEARCH_LIMIT):
    if not keywords:
        return []

    query = {"$or": []}
    for kw in keywords:
        query["$or"].append({"classified.topic": {"$regex": kw, "$options": "i"}})
        query["$or"].append({"classified.tags": {"$regex": kw, "$options": "i"}})

    results = classified_collection.find(query).limit(limit * 2)  # Oversample in case of bad matches
    matched_chunks = []

    for doc in results:
        for chunk in doc.get("classified", []):
            topic = (chunk.get("topic") or "").lower()
            tags = chunk.get("tags") or []
            if any(kw.lower() in topic for kw in keywords) or \
               any(any(kw.lower() in (tag or "").lower() for tag in tags) for kw in keywords):
                matched_chunks.append(chunk)
            if len(matched_chunks) >= limit:
                return matched_chunks

    return matched_chunks

# 🤖 Generate an answer using Groq (context_chunks can be empty — then answer from general knowledge)
def generate_answer(question, context_chunks):
    if context_chunks:
        context_text = "\n\n".join(
            f"Topic: {chunk.get('topic', '')}\nCharacters: {', '.join(chunk.get('characters', []))}\nTags: {', '.join(chunk.get('tags', []))}"
            for chunk in context_chunks
        )
        user_content = f"""Context:
{context_text}

Question:
{question}

Answer in a helpful and concise way:"""
    else:
        user_content = f"""Answer this question in a helpful, concise way. You are a Marvel expert chatbot; use your knowledge if the question is about Marvel. If the question is unclear or not about Marvel, give a short friendly response.

Question: {question}

Answer:"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": _build_chat_system_prompt()},
            {"role": "user", "content": user_content}
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

# 🚀 Chat route (legacy: single question)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required"}), 400

    print(f"🧾 Received question: {question}")
    keywords = extract_keywords(question)
    print(f"🔍 Extracted keywords: {keywords}")

    matched_chunks = search_chunks(keywords) if keywords else []
    num_chunks = len(matched_chunks)
    source = "database" if num_chunks > 0 else "groq_only"
    print(f"📚 DATABASE ({num_chunks} chunks)" if num_chunks else "🤖 GROQ ONLY")
    answer = generate_answer(question, matched_chunks)
    return jsonify({"answer": answer, "source": source, "chunks_used": num_chunks})


# 🚀 Chat response (frontend: messages + userId + chatId)
@app.route("/chat-response", methods=["POST"])
def chat_response():
    data = request.json or {}
    messages = data.get("messages", [])
    user_id = data.get("userId")
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

    print(f"🧾 chat-response question: {question}")
    question_norm = _normalize_question(question)

    # 1) Check cache for external answers (with TTL so we refresh when "internet" updates)
    cached_answer, cached_source = _get_cached_answer(question_norm, question)
    if cached_answer is not None:
        print(f"📦 Answer from CACHE (refreshes after {CACHE_TTL_DAYS} days)")
        answer = cached_answer
        source = cached_source
        num_chunks = 0
    else:
        keywords = extract_keywords(question)
        matched_chunks = search_chunks(keywords) if keywords else []
        num_chunks = len(matched_chunks)

        if num_chunks > 0:
            source = "database"
            print(f"📚 Answer from DATABASE (RAG): {num_chunks} chunk(s) → Groq with context")
        else:
            source = "groq_only"
            print(f"🤖 Answer from GROQ ONLY: no matching chunks → general knowledge")

        answer = generate_answer(question, matched_chunks)

        # 2) Store external answers so we reuse them and can refresh after TTL
        if source == "groq_only" and answer:
            _save_external_answer(question, question_norm, answer, source)

    # Persist chat session and history (user_id is string from frontend)
    if user_id:
        if not chat_id:
            chat_id = str(uuid.uuid4())
        title = (question[:50] + "…") if len(question) > 50 else question
        now = datetime.now(timezone.utc)
        chat_sessions_collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {
                "$set": {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "title": title,
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        chat_history_collection.insert_one({
            "chat_id": chat_id,
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "timestamp": now,
        })

    return jsonify({
        "answer": answer,
        "chat_id": chat_id or None,
        "source": source,
        "chunks_used": num_chunks,
    })


@app.route("/chats/<user_id>", methods=["GET"])
def get_chats(user_id):
    """List chat sessions for user. Frontend expects [{ chat_id, title, last_updated }]."""
    try:
        sessions = list(
            chat_sessions_collection.find({"user_id": user_id})
            .sort("updated_at", -1)
        )
        result = [
            {
                "chat_id": s["chat_id"],
                "title": s.get("title", "Untitled"),
                "last_updated": s.get("updated_at"),
            }
            for s in sessions
        ]
        return jsonify(result)
    except Exception as e:
        print(f"❌ get_chats: {e}")
        return jsonify([])


@app.route("/history/<chat_id>", methods=["GET"])
def get_history(chat_id):
    """Return chat history as [{ question, answer }, ...] for frontend to map to messages."""
    try:
        docs = list(
            chat_history_collection.find({"chat_id": chat_id})
            .sort("timestamp", 1)
        )
        return jsonify([{"question": d["question"], "answer": d["answer"]} for d in docs])
    except Exception as e:
        print(f"❌ get_history: {e}")
        return jsonify([])


@app.route("/recommendations", methods=["POST"])
def recommendations():
    """Return suggested topics based on chat messages. Frontend expects a JSON array."""
    data = request.json or {}
    messages = data.get("messages", [])
    suggestions = []
    if messages:
        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user = (msg.get("content") or "").strip()
                break
        if last_user:
            keywords = extract_keywords(last_user)
            if keywords:
                suggestions = [f"More about {kw}" for kw in keywords[:3]]
    if not suggestions:
        suggestions = ["Iron Man", "Captain America", "Marvel Cinematic Universe"]
    return jsonify(suggestions)


# 🌐 Root route
@app.route("/")
def home():
    return "🚀 Welcome to the Marvel Chatbot API!"


# 🔐 Auth routes (for frontend on port 5173)
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User with this email already exists"}), 400
    hashed_password = generate_password_hash(password)
    user_id = users_collection.insert_one({
        "email": email,
        "password": hashed_password,
    }).inserted_id
    user = {"email": email, "id": str(user_id)}
    return jsonify({"message": "User registered successfully", "user": user}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    email = (data.get("email") or "").strip()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    user = users_collection.find_one({"email": email})
    if not user:
        if os.environ.get("LOG_AUTH_FAILURES"):
            print(f"[auth] Login failed: no user for email={email!r}")
        return jsonify({"error": "Invalid email or password"}), 401
    if not check_password_hash(user["password"], password):
        if os.environ.get("LOG_AUTH_FAILURES"):
            print(f"[auth] Login failed: wrong password for email={email!r}")
        return jsonify({"error": "Invalid email or password"}), 401
    return jsonify({
        "message": "Login successful",
        "user": {"email": user["email"], "id": str(user["_id"])},
    })


# Run the Flask app (use PORT from env on Render; 0.0.0.0 so Render can reach it)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
