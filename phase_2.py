import os
import time
import random
import re
import json
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# MongoDB Setup
MONGO_URI = os.getenv("mongo")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set.")

client = MongoClient(MONGO_URI)
db = client["marvel_crawler"]

raw_collection = db["scraped_data"]  # raw scraped data from Phase 1
classified_collection = db["classified_chunks"]  # store classified results

# Groq API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

# Prompt template for classification
PROMPT_TEMPLATE = """You are a data extractor for a Marvel chatbot. 
From the following raw chunk of data, extract the relevant:
- characters (as a list)
- topic (as a short label: e.g. biography, powers, origin, movies, etc.)
- tags (as a list of themes/keywords)

Only respond with the JSON object. Example:
{{
  "characters": [...],
  "topic": "biography",
  "tags": [...]
}}

Chunk:
\"\"\"{chunk}\"\"\"
"""

def chunk_text(text, max_chunk_size=700):
    """
    Efficiently split large text into manageable chunks:
    - Split by paragraphs
    - Further split long paragraphs by sentences if needed
    """
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 1 <= max_chunk_size:
            current_chunk += " " + para if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            # If paragraph too large, split by sentence
            if len(para) > max_chunk_size:
                sentences = re.split(r'(?<=[.!?]) +', para)
                temp_chunk = ""
                for sent in sentences:
                    if len(temp_chunk) + len(sent) + 1 <= max_chunk_size:
                        temp_chunk += " " + sent if temp_chunk else sent
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = sent
                if temp_chunk:
                    chunks.append(temp_chunk.strip())
                current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def classify_chunk(chunk, max_retries=7):
    prompt = PROMPT_TEMPLATE.format(chunk=chunk.strip())
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are a JSON-only extractor for Marvel chatbot training."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    backoff = 2  # initial backoff seconds

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after else backoff + random.uniform(0.5, 1.5)
                print(f"⏳ Rate limited (429). Retry attempt {attempt} in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                backoff = min(backoff * 2, 60)
                continue

            if response.status_code == 413:
                print(f"🚫 Payload too large (413). Consider smaller chunks.")
                return None

            response.raise_for_status()

            raw_content = response.json()["choices"][0]["message"]["content"]
            # Extract JSON object robustly
            match = re.search(r"\{[\s\S]*?\}", raw_content)
            if not match:
                raise ValueError("No valid JSON found in LLM response.")

            parsed_json = json.loads(match.group())
            return parsed_json

        except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error on attempt {attempt}: {e}")
            time.sleep(backoff + random.uniform(0.5, 1.5))
            backoff = min(backoff * 2, 60)

    print("🚫 Max retries reached, skipping this chunk.")
    return None

def phase2_classify():
    # Fetch docs that are not yet classified
    unclassified_docs = raw_collection.find({
        "_id": {"$nin": [doc["_id"] for doc in classified_collection.find({}, {"_id": 1})]}
    })

    total_docs = raw_collection.count_documents({})
    processed = 0

    for doc in unclassified_docs:
        url = doc.get("url")
        content = doc.get("content", "")

        if not content:
            print(f"⚠️ No content for {url}, skipping.")
            continue

        print(f"\n📄 Classifying document {processed + 1}/{total_docs}: {url}")

        # Chunk the content
        chunks = chunk_text(content)
        print(f"🔍 Split into {len(chunks)} chunks.")

        classified_chunks = []
        for idx, chunk in enumerate(chunks):
            print(f"  🧩 Classifying chunk {idx + 1}/{len(chunks)} (size: {len(chunk)})...")
            result = classify_chunk(chunk)
            if result:
                classified_chunks.append(result)
            else:
                print(f"  ⚠️ Failed chunk {idx + 1}")

            time.sleep(1)  # rate limit buffer

        if classified_chunks:
            # Save once per document, minimizing DB writes
            classified_collection.insert_one({
                "url": url,
                "classified": classified_chunks,
                "timestamp": time.time()
            })
            print(f"✅ Document classified and saved for {url}")
        else:
            print(f"⚠️ No valid classified chunks for {url}")

        processed += 1

if __name__ == "__main__":
    phase2_classify()
