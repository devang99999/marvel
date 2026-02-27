import os
import time
import json
import hashlib
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("mongo")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set")

client = MongoClient(MONGO_URI)
db = client["marvel_crawler"]
classified_collection = db["classified_chunks"]
embedding_collection = db["embedded_chunks"]

# Ensure index on content_hash for fast lookups and uniqueness
embedding_collection.create_index("content_hash", unique=True)

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

def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

def generate_embedding(content, retries=5, base_delay=2):
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

    delay = base_delay
    for attempt in range(1, retries + 1):
        try:
            res = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)

            if res.status_code == 429:
                print(f"⏳ Rate limited. Backing off for {delay} seconds... (Attempt {attempt})")
                time.sleep(delay)
                delay = min(delay * 2, 60)
                continue

            res.raise_for_status()
            content = res.json()["choices"][0]["message"]["content"]

            # Parse embedding JSON safely
            embedding = json.loads(content)
            if isinstance(embedding, list) and all(isinstance(x, (float, int)) for x in embedding):
                # Normalize to floats
                return [float(x) for x in embedding]

            print(f"❌ Unexpected embedding format on attempt {attempt}")
        except Exception as e:
            print(f"❌ Embedding failed on attempt {attempt}: {e}")

        time.sleep(delay)
        delay = min(delay * 2, 60)

    return None

def phase3_embed_optimized(batch_size=100):
    print("🔍 Loading existing content hashes to skip duplicates...")
    existing_hashes = set(doc["content_hash"] for doc in embedding_collection.find({}, {"content_hash": 1}))
    print(f"⚡ Found {len(existing_hashes)} existing embeddings.")

    print("📦 Loading classified documents...")
    classified_docs = list(classified_collection.find({}))
    print(f"📄 Total classified docs: {len(classified_docs)}")

    all_to_insert = []
    processed_chunks = 0
    skipped_chunks = 0

    for doc in classified_docs:
        url = doc.get("url")
        chunks = doc.get("classified", [])
        print(f"\n🌐 Processing URL: {url} with {len(chunks)} chunks.")

        for idx, chunk in enumerate(chunks):
            # Compose content string to embed
            content = f"{chunk.get('topic', '')}: {' '.join(chunk.get('tags', []))}"

            content_hash = generate_hash(content)
            if content_hash in existing_hashes:
                skipped_chunks += 1
                print(f"✅ Skipping chunk {idx + 1} (already embedded)")
                continue

            embedding = generate_embedding(content)
            if embedding is None:
                print(f"⚠️ Failed to embed chunk {idx + 1} at {url}. Skipping.")
                continue

            record = {
                "url": url,
                "chunk_index": idx,
                "content": content,
                "original_chunk": chunk,
                "embedding": embedding,
                "content_hash": content_hash,
                "timestamp": time.time()
            }
            all_to_insert.append(record)
            existing_hashes.add(content_hash)
            processed_chunks += 1
            print(f"✅ Embedded chunk {idx + 1}/{len(chunks)}")

            # Batch insert in chunks of batch_size
            if len(all_to_insert) >= batch_size:
                print(f"💾 Inserting batch of {len(all_to_insert)} embeddings...")
                try:
                    embedding_collection.insert_many(all_to_insert, ordered=False)
                except Exception as e:
                    print(f"❌ Batch insert error: {e}")
                all_to_insert = []

            # Small delay to avoid rate limits
            time.sleep(0.5)

    # Insert remaining embeddings
    if all_to_insert:
        print(f"💾 Inserting final batch of {len(all_to_insert)} embeddings...")
        try:
            embedding_collection.insert_many(all_to_insert, ordered=False)
        except Exception as e:
            print(f"❌ Batch insert error: {e}")

    print(f"\n✅ Finished embedding. Processed {processed_chunks} new chunks, skipped {skipped_chunks} duplicates.")

if __name__ == "__main__":
    phase3_embed_optimized()
