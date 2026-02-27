import os
import time
import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

load_dotenv()

app = Flask(__name__)

# MongoDB Setup
MONGO_URI = os.getenv("mongo")
client = MongoClient(MONGO_URI)
db = client["marvel_crawler"]
classified_collection = db["classified_chunks"]
qa_cache_collection = db["qa_cache"]

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

SEARCH_LIMIT = 5

# 🔑 Phase 5: Keyword Extraction using Groq
def extract_keywords(question):
    prompt = f"Extract 3 to 5 concise keywords from this Marvel-related question for search purposes:\n\n\"{question}\"\n\nReturn only a comma-separated list of keywords."
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You extract search keywords from Marvel-related questions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 60
    }
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        res.raise_for_status()
        keywords_raw = res.json()["choices"][0]["message"]["content"]
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        return keywords
    except Exception as e:
        print(f"Keyword extraction failed: {e}")
        return [question]  # Fallback to full question

# 🔍 Search DB using extracted keywords
def search_chunks(keywords, limit=SEARCH_LIMIT):
    or_clauses = []
    for kw in keywords:
        regex = {"$regex": kw, "$options": "i"}
        or_clauses.append({"classified.topic": regex})
        or_clauses.append({"classified.tags": regex})

    results = classified_collection.find({"$or": or_clauses}).limit(limit)

    matched_chunks = []
    for doc in results:
        for chunk in doc.get("classified", []):
            if any(kw.lower() in chunk.get("topic", "").lower() or
                   any(kw.lower() in tag.lower() for tag in chunk.get("tags", []))
                   for kw in keywords):
                matched_chunks.append(chunk)
            if len(matched_chunks) >= limit:
                break
        if len(matched_chunks) >= limit:
            break

    return matched_chunks

# 💬 Generate answer from context using Groq
def generate_answer(question, context_chunks):
    context_text = "\n\n".join(
        f"Topic: {chunk.get('topic', '')}\nCharacters: {', '.join(chunk.get('characters', []))}\nTags: {', '.join(chunk.get('tags', []))}"
        for chunk in context_chunks
    )

    prompt = f"""
You are a Marvel chatbot god, created by Devang Gandhi, an AI engineer. 
You are still learning and improving every day. 
Your job is to help users with questions related to the Marvel universe. 
Do not mention 'data chunks' in your answers — just respond naturally and helpfully. 
You also dislike the DC Universe and DCEU but you do like Batman, Superman, and The Flash from DC. 
Always provide concise, accurate, and engaging answers based on your knowledge.
    
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
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error generating answer: {e}")
        return None

# 🌐 Web fallback (scrape first link's paragraph)
def live_web_search_fallback(query):
    print(f"🌐 Web fallback triggered for: {query}")
    if not SERPAPI_KEY:
        return None

    search_url = f"https://serpapi.com/search.json?q={requests.utils.quote(query)}&num=1&api_key={SERPAPI_KEY}"
    try:
        res = requests.get(search_url)
        res.raise_for_status()
        results = res.json().get("organic_results", [])
        if not results:
            return None

        first_url = results[0].get("link")
        if not first_url:
            return None

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(first_url, timeout=15000)
            page.wait_for_load_state("domcontentloaded", timeout=10000)

            for sel in ["article p", "p"]:
                paras = page.query_selector_all(sel)
                for ptag in paras:
                    text = ptag.inner_text().strip()
                    if len(text) > 50:
                        browser.close()
                        return text
            browser.close()
        return None
    except Exception as e:
        print(f"Web scrape error: {e}")
        return None

# ✨ Fallback Groq answer
def generate_generic_answer(question):
    prompt = f"You are a Marvel chatbot assistant. Answer this clearly:\n\n{question}"
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
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"].strip()
    except:
        return "Sorry, I couldn't find an answer right now."

# 📡 Flask API
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Question is required"}), 400

    # 1. Cache lookup
    cached = qa_cache_collection.find_one({"question": question})
    if cached:
        print("🗃️ Using cached answer.")
        return jsonify({"answer": cached["answer"]})

    # 2. Extract keywords
    keywords = extract_keywords(question)
    print(f"🔍 Keywords: {keywords}")

    # 3. Search DB
    matched_chunks = search_chunks(keywords)
    if matched_chunks:
        print(f"📚 Found {len(matched_chunks)} DB chunks.")
        answer = generate_answer(question, matched_chunks)
        if answer:
            qa_cache_collection.insert_one({"question": question, "answer": answer, "timestamp": time.time()})
            return jsonify({"answer": answer})

    # 4. Web fallback
    content = live_web_search_fallback(question)
    if content:
        web_answer = f"(📡 That’s outside my database, so I searched the web for you.)\n\n{content}"
        qa_cache_collection.insert_one({"question": question, "answer": web_answer, "timestamp": time.time()})
        return jsonify({"answer": web_answer})

    # 5. Generic LLM fallback
    generic = generate_generic_answer(question)
    qa_cache_collection.insert_one({"question": question, "answer": generic, "timestamp": time.time()})
    return jsonify({"answer": generic})

@app.route('/')
def home():
    return "Welcome to the Marvel Chatbot Phase 5!"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
