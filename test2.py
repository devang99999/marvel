import os
import time
import json
import hashlib
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# DB setup
MONGO_URI = os.getenv("mongo")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(MONGO_URI)
db = client["marvel_crawler"]
classified_collection = db["classified_chunks"]
embedding_collection = db["embedded_chunks"]

# Groq API setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
EMBEDDING_PROMPT = """Convert the following content into a high-dimensional vector representation suitable for semantic search. 
Only return the embedding as a JSON list of floats.

Content:
\"\"\"{content}\"\"\"
"""

# Utilities
def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def generate_embedding(content, retries=4):
    prompt = EMBEDDING_PROMPT.format(content=content)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are an embedding generator. Return only a list of floats."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    delay = 2
    for attempt in range(retries):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
            if res.status_code == 429:
                print(f"⏳ Rate limit hit. Waiting {delay} seconds...")
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue

            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]

            embedding = json.loads(content)
            if isinstance(embedding, list) and all(isinstance(x, float) for x in embedding):
                return embedding
        except Exception as e:
            print(f"❌ Failed to embed: {e}")
            time.sleep(delay)
            delay = min(delay * 2, 60)

    return None

def phase3_embed_optimized():
    print("🔍 Fetching already embedded content hashes...")
    existing_hashes = set()
    for doc in embedding_collection.find({}, {"content_hash": 1}):
        existing_hashes.add(doc["content_hash"])

    print("📦 Loading classified documents...")
    classified_docs = list(classified_collection.find({}))
    print(f"🔢 Total classified docs: {len(classified_docs)}")

    all_to_insert = []

    for doc in classified_docs:
        url = doc["url"]
        chunks = doc.get("classified", [])
        print(f"\n🌐 Processing: {url} ({len(chunks)} chunks)")

        for idx, chunk in enumerate(chunks):
            content = f"{chunk['topic']}: {' '.join(chunk.get('tags', []))}"
            content_hash = generate_hash(content)

            if content_hash in existing_hashes:
                print(f"✅ Skipping already embedded chunk {idx+1}")
                continue

            embedding = generate_embedding(content)
            if embedding:
                all_to_insert.append({
                    "url": url,
                    "chunk_index": idx,
                    "content": content,
                    "original_chunk": chunk,
                    "embedding": embedding,
                    "content_hash": content_hash,
                    "timestamp": time.time()
                })
                existing_hashes.add(content_hash)
                print(f"✅ Embedded chunk {idx+1}/{len(chunks)}")
            else:
                print(f"⚠️ Failed to embed chunk {idx+1}")

            # Soft wait between calls
            time.sleep(0.5)

    if all_to_insert:
        print(f"\n💾 Inserting {len(all_to_insert)} new embeddings...")
        embedding_collection.insert_many(all_to_insert)
        print("✅ Insertion complete.")
    else:
        print("⚠️ No new embeddings to insert.")

if __name__ == "__main__":
    phase3_embed_optimized()
