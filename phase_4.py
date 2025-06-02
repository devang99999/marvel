import os
import time
import uuid
import requests
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from flask_cors import CORS
from datetime import datetime
from uuid import uuid4



load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# MongoDB Setup
MONGO_URI = os.getenv("mongo")
client = MongoClient(MONGO_URI)
db = client["marvel_crawler"]
classified_collection = db["classified_chunks"]
qa_cache_collection = db["qa_cache"]
chat_history_collection = db["chat_history"]
chat_sessions_collection = db["chat_sessions"]
chat_collection = db["chat_data"]


users_collection = db["users"]
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
            if any(kw.lower() in (str(chunk.get("topic") or "")).lower() or
                   any(kw.lower() in tag.lower() for tag in chunk.get("tags", []))
                   for kw in keywords):
                matched_chunks.append(chunk)
            if len(matched_chunks) >= limit:
                break
        if len(matched_chunks) >= limit:
            break

    return matched_chunks

# 💬 Generate answer from context using Groq
def format_context_history(context_history):
    """
    Convert list of message dicts into readable text format:
    User: ...
    Assistant: ...
    """
    formatted = []
    for message in context_history:
        role = message.get("role", "")
        content = message.get("content", "")
        if role == "user":
            formatted.append(f"User: {content}")
        elif role == "assistant":
            formatted.append(f"Assistant: {content}")
        else:
            # in case of other roles
            formatted.append(f"{role.capitalize()}: {content}")
    return "\n".join(formatted)

def generate_answer(question, context_chunks, context_history):
    context_text = "\n\n".join(
        f"Topic: {chunk.get('topic', '')}\nCharacters: {', '.join(chunk.get('characters', []))}\nTags: {', '.join(chunk.get('tags', []))}"
        for chunk in context_chunks
    )
    
    formatted_history = format_context_history(context_history)

    prompt = f"""
You are a "God", created by "Devang Gandhi", an AI engineer. 
You are still learning and improving every day. 
Your job is to help users with questions related to the Marvel universe. 
Do not mention 'data chunks' in your answers — just respond naturally and helpfully. 
You also dislike the DC Universe and DCEU but you do like Batman, Superman, and The Flash from DC. 
Always provide concise, accurate, and engaging answers based on your knowledge.
    
Current_Context:
{context_text}

Full_Context:
{formatted_history}

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

    print("prompt:", prompt)
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

    return jsonify({"message": "User registered successfully", "user_id": str(user_id)}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "user": {"email": user["email"], "id": str(user["_id"])}})


# @app.route("/chat-response", methods=["POST"])
# def chat_response():
#     data = request.json
#     messages = data.get("messages", [])
#     user_id = data.get("userId")  # frontend must pass this
#     chat_id = data.get("chat_id")  # optional

#     # if not messages or not isinstance(messages, list) or not user_id:
#     #     return jsonify({"error": "Messages and user_id required"}), 400

#     # Get latest user message
#     question = ""
#     for msg in reversed(messages):
#         if msg.get("role") == "user":
#             question = msg.get("content", "").strip()
#             break
#     if not question:
#         return jsonify({"error": "No user question found in messages"}), 400

#     # Use existing /chat logic
#     cached = qa_cache_collection.find_one({"question": question})
#     if cached:
#         answer = cached["answer"]
#     else:
#         keywords = extract_keywords(question)
#         matched_chunks = search_chunks(keywords)
#         if matched_chunks:
#             answer = generate_answer(question, matched_chunks)
#         else:
#             content = live_web_search_fallback(question)
#             if content:
#                 answer = f"(📡 Web result)\n\n{content}"
#             else:
#                 answer = generate_generic_answer(question)
#         qa_cache_collection.insert_one({"question": question, "answer": answer, "timestamp": time.time()})

#     # If no chat_id, create new session
#     if not chat_id:
#         chat_id = str(uuid.uuid4())
#         chat_sessions_collection.insert_one({
#             "chat_id": chat_id,
#             "user_id": user_id,
#             "created_at": time.time(),
#             "title": question[:40] + ("..." if len(question) > 40 else "")
#         })

#     # Append to chat history
#     chat_history_collection.insert_one({
#         "chat_id": chat_id,
#         "user_id": user_id,
#         "question": question,
#         "answer": answer,
#         "timestamp": time.time()
#     })

#     return jsonify({"answer": answer, "chat_id": chat_id})
# @app.route("/chat-response", methods=["POST"])
# def chat_response():
#     data = request.json
#     messages = data.get("messages", [])
#     user_id = data.get("userId")
#     chat_id = data.get("chatId")

#     if not user_id or not messages:
#         return jsonify({"error": "userId and messages are required"}), 400

#     # Get the latest user question
#     question = ""
#     for msg in reversed(messages):
#         if msg.get("role") == "user":
#             question = msg.get("content", "").strip()
#             break

#     if not question:
#         return jsonify({"error": "No user question found"}), 400

#     # Try to find a cached answer first
#     cached = qa_cache_collection.find_one({"question": question})
#     if cached:
#         answer = cached["answer"]
#     else:
#         # Extract keywords and search context
#         keywords = extract_keywords(question)
#         matched_chunks = search_chunks(keywords)
#         if matched_chunks:
#             answer = generate_answer(question, matched_chunks)
#         else:
#             content = live_web_search_fallback(question)
#             if content:
#                 answer = f"(📡 Web result)\n\n{content}"
#             else:
#                 answer = generate_generic_answer(question)
#         qa_cache_collection.insert_one({"question": question, "answer": answer, "timestamp": time.time()})

#     # Create new chat session if not exists
#     if not chat_id:
#         chat_id = str(uuid4())
#         chat_collection.insert_one({
#             "chat_id": chat_id,
#             "user_id": user_id,
#             "messages": [],
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow()
#         })

#     # Append user & assistant message to chat
#     chat_collection.update_one(
#         {"chat_id": chat_id, "user_id": user_id},
#         {
#             "$push": {
#                 "messages": {
#                     "$each": [
#                         {"role": "user", "content": question},
#                         {"role": "assistant", "content": answer}
#                     ]
#                 }
#             },
#             "$set": {"updated_at": datetime.utcnow()}
#         }
#     )

#     return jsonify({"answer": answer, "chat_id": chat_id})
def context_search(chat_id, user_id):
    coll = chat_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if coll and "messages" in coll:
        print(f"[context_search] Found {len(coll['messages'])} messages for chat_id={chat_id}")
        return coll["messages"]
    else:
        print(f"[context_search] No chat found for chat_id={chat_id} and user_id={user_id}")
        return []

@app.route("/chat-response", methods=["POST"])
def chat_response():
    data = request.json
    messages = data.get("messages", [])
    user_id = data.get("userId")
    print("uid", user_id)
    chat_id = data.get("chatId")
    print("cid", chat_id)

    if not user_id or not messages:
        return jsonify({"error": "userId and messages are required"}), 400

    # Extract latest user question from messages array
    question = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            question = msg.get("content", "").strip()
            break

    if not question:
        return jsonify({"error": "No user question found in messages"}), 400

    # 1. Check cache for answer
    cached = qa_cache_collection.find_one({"question": question})
    if cached:
        answer = cached["answer"]
    else:
        # 2. Extract keywords and search DB
        context = context_search(chat_id, user_id)
        keywords = extract_keywords(question)
        matched_chunks = search_chunks(keywords)
        if matched_chunks:
            answer = generate_answer(question, matched_chunks,context)
        else:
            # 3. Web fallback
            content = live_web_search_fallback(question)
            if content:
                answer = f"(📡 Web result)\n\n{content}"
            else:
                # 4. Generic fallback
                answer = generate_generic_answer(question)
        
        # Cache the new Q&A
        qa_cache_collection.insert_one({
            "question": question,
            "answer": answer,
            "timestamp": time.time()
        })

    # 5. Create new chat session if chat_id not provided
    if not chat_id:
        chat_id = str(uuid.uuid4())
        chat_sessions_collection.insert_one({
            "chat_id": chat_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "title": (question[:40] + "...") if len(question) > 40 else question
        })

    # 6. Save chat history record (latest question + answer)
    chat_history_collection.insert_one({
        "chat_id": chat_id,
        "user_id": user_id,
        "question": question,
        "answer": answer,
        "timestamp": datetime.utcnow()
    })

    # 7. Save/update full conversation in chat_data collection
    chat_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {
            "$set": {
                "chat_id": chat_id,
                "user_id": user_id,
                "messages": messages + [{"role": "assistant", "content": answer}],
                "last_updated": datetime.utcnow()
            }
        },
        upsert=True
    )

    return jsonify({
        "answer": answer,
        "chatId": chat_id
    })

@app.route("/chat/<chat_id>/<user_id>", methods=["GET"])
def get_chat_by_id(chat_id,user_id):
    try:
        chat = chat_collection.find_one({
            "chat_id": chat_id,
            "user_id": user_id
        })
        

        if not chat:
            return jsonify({"error": "Chat not found"}), 404

        return jsonify({
            "chat_id": chat.get("chat_id", ""),
            "title": chat.get("title", ""),
            "messages": chat.get("messages", []),
            "last_updated": chat.get("last_updated", "")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/chats/<user_id>", methods=["GET"])
def get_chats_for_user(user_id):
    try:
        
        sessions = list(chat_collection.find(
            {"user_id": user_id},
            {"_id": 0, "chat_id": 1, "title": 1, "created_at": 1}
        ).sort("created_at", -1))

        return jsonify(sessions)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# @app.route("/chat-history/<chat_id>", methods=["GET"])
# def get_chat_history(chat_id):
#     history = chat_history_collection.find_one({"chat_id": chat_id})
#     if not history:
#         return jsonify({"error": "Chat history not found"}), 404

#     # Convert MongoDB _id to string
#     history["_id"] = str(history["_id"])
#     return jsonify(history)

# @app.route("/chat-history/<chat_id>", methods=["GET"])
# def save_chat_history():
#     data = request.json
#     messages = data.get("messages", [])
#     if not messages:
#         return jsonify({"error": "No messages provided"}), 400

#     chat_id = chat_history_collection.insert_one({"messages": messages, "timestamp": time.time()}).inserted_id
#     return jsonify({"chat_id": str(chat_id)})

# @app.route("/chat-history/<chat_id>", methods=["GET"])
# def get_chat_history(chat_id):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         return jsonify({"error": "Unauthorized"}), 401

#     user_id = auth_header.split(" ")[1]
#     chat = chat_collection.find_one({"chat_id": chat_id, "user_id": user_id})

#     if not chat:
#         return jsonify([])

#     return jsonify(chat["messages"])




# @app.route("/chat_sessions/<user_id>", methods=["GET"])
# def get_chat_sessions(user_id):
#     chats = chat_collection.find(
#         {"user_id": user_id},
#         {"_id": 0, "chat_id": 1, "updated_at": 1}
#     )

#     result = [
#         {"chat_id": chat["chat_id"], "updated_at": chat["updated_at"]}
#         for chat in chats
#     ]
#     return jsonify(result)



@app.route("/chat-sessions/<user_id>", methods=["GET"])
def get_chat_sessions(user_id):
    try:
        sessions = chat_sessions_collection.find({"user_id": ObjectId(user_id)}).sort("updated_at", -1)
        result = []
        for session in sessions:
            result.append({
                "chat_id": session["chat_id"],
                "title": session.get("title", "Untitled"),
                "updated_at": session.get("updated_at")
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route("/chat-history/<chat_id>", methods=["GET"])
def get_chat_history(chat_id):
    try:
        chat = chat_collection.find_one({"chat_id": chat_id})
        if not chat:
            return jsonify({"messages": []})
        return jsonify({"messages": chat["messages"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/recommendations", methods=["POST"])
def recommendations():
    data = request.json
    messages = data.get("messages", [])
    if not messages or not isinstance(messages, list):
        return jsonify({"error": "Messages must be a list"}), 400

    last_question = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_question = msg.get("content", "")
            break

    prompt = f"""
Given the following Marvel-related question:
"{last_question}"

Suggest 3 relevant and engaging follow-up questions the user might ask next.
Format them as a JSON list of strings.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You suggest follow-up Marvel-related questions."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        res.raise_for_status()
        raw_text = res.json()["choices"][0]["message"]["content"]

        # Try to parse valid JSON list
        suggestions = []
        try:
            suggestions = eval(raw_text.strip())
        except:
            suggestions = [line.strip("-• ").strip() for line in raw_text.split("\n") if line.strip()]

        return jsonify({"recommendations": suggestions[:3]})
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return jsonify({"recommendations": []})



# if __name__ == "__main__":
#     app.run(debug=True)
# if __name__ == "__main__":
#     app.run(port=5000, debug=True)


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))  # allow dynamic port
    app.run(host="0.0.0.0", port=PORT, debug=True)

