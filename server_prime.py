import os
import time
import json
import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# CORS: allow Vercel frontend + local dev (required for browser requests from another origin)
CORS_ORIGINS = [
    "https://marvel-nine-coral.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

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

@app.route("/", defaults={"path": ""}, methods=["OPTIONS"])
@app.route("/<path:path>", methods=["OPTIONS"])
def cors_preflight(path):
    return "", 204

# MongoDB Setup
MONGO_URI = os.getenv("mongo")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set.")

client = MongoClient(MONGO_URI)
db = client["marvel_crawler"]
classified_collection = db["classified_chunks"]

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

# 🌐 Root route
@app.route("/")
def home():
    return "🚀 Welcome to the Marvel Chatbot API!"

# Run the Flask app
if __name__ == "__main__":
    app.run(port=5001, debug=True)
