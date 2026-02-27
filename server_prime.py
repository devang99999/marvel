import os
import time
import json
import uuid
import requests
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
app = Flask(__name__)

# CORS: allow all origins so frontend (Vercel, localhost) never gets CORS/405
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept"
    response.headers["Access-Control-Expose-Headers"] = "Content-Type"
    return response

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def cors_preflight(path):
    return "", 204

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed", "path": request.path, "method": request.method}), 405

# MongoDB Setup
MONGO_URI = os.getenv("mongo")
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
SEARCH_LIMIT = 5

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
        "model": "llama3-8b-8192",
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
        "model": "llama3-8b-8192",
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

# 🚀 Chat route
@app.route("/chat", methods=["POST"])
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

# Chat response (frontend: messages + userId + chatId) — same contract as marvel/server_prime
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
    keywords = extract_keywords(question)
    matched_chunks = search_chunks(keywords)
    answer = generate_answer(question, matched_chunks)
    source = "database" if matched_chunks else "groq_only"
    if not chat_id:
        chat_id = str(uuid.uuid4())
    if user_id:
        now = datetime.now(timezone.utc)
        title = (question[:50] + "…") if len(question) > 50 else question
        chat_sessions_collection.update_one(
            {"chat_id": chat_id, "user_id": user_id},
            {"$set": {"chat_id": chat_id, "user_id": user_id, "title": title, "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        chat_history_collection.insert_one({"chat_id": chat_id, "user_id": user_id, "question": question, "answer": answer, "timestamp": now})
    return jsonify({"answer": answer, "chat_id": chat_id, "source": source, "chunks_used": len(matched_chunks)})

@app.route("/chats/<user_id>", methods=["GET"])
def get_chats(user_id):
    try:
        sessions = list(chat_sessions_collection.find({"user_id": user_id}).sort("updated_at", -1))
        return jsonify([{"chat_id": s["chat_id"], "title": s.get("title", "Untitled"), "last_updated": s.get("updated_at")} for s in sessions])
    except Exception as e:
        print(f"❌ get_chats: {e}")
        return jsonify([])

@app.route("/history/<chat_id>", methods=["GET"])
def get_history(chat_id):
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

# 🌐 Root route (GET only)
@app.route("/", methods=["GET"])
def home():
    return "🚀 Welcome to the Marvel Chatbot API!"

# 🔐 Auth routes (for frontend login/register)
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    email = (data.get("email") or "").strip()
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User with this email already exists"}), 400
    hashed = generate_password_hash(password)
    user_id = users_collection.insert_one({"email": email, "password": hashed}).inserted_id
    return jsonify({"message": "User registered successfully", "user": {"email": email, "id": str(user_id)}}), 201

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
        return jsonify({"error": "Invalid email or password"}), 401
    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    return jsonify({
        "message": "Login successful",
        "user": {"email": user["email"], "id": str(user["_id"])},
    })

# Run the Flask app
if __name__ == "__main__":
    app.run(port=5001, debug=True)
