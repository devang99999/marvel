#!/usr/bin/env python3
"""
Inspect Marvel Chatbot MongoDB database: collections, counts, and sample data.

Usage (from marvel/ with .env containing mongo URI):
  source venv/bin/activate
  python inspect_db.py           # human-readable report
  python inspect_db.py --json   # machine-readable summary
"""
import os
import sys
import json
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Optional: use certifi for SSL (same as server_prime)
try:
    import certifi
    from pymongo import MongoClient
    MONGO_URI = os.getenv("mongo")
    if not MONGO_URI:
        print("ERROR: Set 'mongo' in .env (MongoDB connection string)")
        sys.exit(1)
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
except Exception as e:
    print(f"Connection setup failed: {e}")
    sys.exit(1)

DB_NAME = "marvel_crawler"
db = client[DB_NAME]


def json_serial(obj):
    """Convert ObjectId, datetime to JSON-serializable."""
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def sample_doc(doc, max_str=200, max_list=3, max_embedding=5, depth=0):
    """Produce a readable sample of a document (truncate long values)."""
    if doc is None:
        return None
    if depth > 2:
        return "<nested>"
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out[k] = str(v)
            continue
        if isinstance(v, str):
            out[k] = v[:max_str] + ("..." if len(v) > max_str else v)
        elif isinstance(v, list):
            if k == "embedding":
                out[k] = f"<list of floats, len={len(v)}>"
            elif k == "classified":
                out[k] = f"<list len={len(v)}>"
                if v and isinstance(v[0], dict):
                    out[f"{k}[0]"] = sample_doc(v[0], max_str=100, max_list=2, depth=depth + 1)
            else:
                out[k] = v[:max_list] if len(v) <= max_list else v[:max_list] + [f"...+{len(v)-max_list} more"]
        elif isinstance(v, dict):
            out[k] = sample_doc(v, max_str=max_str // 2, max_list=2, depth=depth + 1)
        elif isinstance(v, (datetime, ObjectId)):
            out[k] = json_serial(v)
        else:
            out[k] = v
    return out


def get_keys_from_cursor(coll, limit=100):
    """Get set of top-level keys seen in first `limit` docs."""
    keys = set()
    for doc in coll.find().limit(limit):
        keys.update(doc.keys())
    return sorted(keys)


def inspect_collection(name, as_json=False):
    """Inspect one collection: count, keys, 1–2 sample docs."""
    coll = db[name]
    count = coll.count_documents({})
    keys = get_keys_from_cursor(coll)
    samples = list(coll.find().limit(2))
    sample_out = [sample_doc(s) for s in samples]
    return {
        "collection": name,
        "count": count,
        "keys": keys,
        "samples": sample_out,
    }


def main():
    as_json = "--json" in sys.argv
    print(f"\n{'='*60}")
    print(f"  Marvel DB Inspector — database: {DB_NAME}")
    print(f"{'='*60}\n")

    try:
        # List all collections
        coll_names = db.list_collection_names()
    except Exception as e:
        print(f"ERROR listing collections: {e}")
        sys.exit(1)

    if not coll_names:
        print("No collections found.")
        if as_json:
            print(json.dumps({"database": DB_NAME, "collections": []}, indent=2))
        return

    results = []
    for name in sorted(coll_names):
        try:
            info = inspect_collection(name, as_json)
            results.append(info)
            if not as_json:
                print(f"📦 {name}")
                print(f"   Count: {info['count']}")
                print(f"   Keys:  {', '.join(info['keys'])}")
                if info["samples"]:
                    print("   Sample doc(s):")
                    for i, s in enumerate(info["samples"], 1):
                        print(f"     [{i}] {json.dumps(s, default=json_serial, indent=6)}")
                print()
        except Exception as e:
            results.append({"collection": name, "error": str(e)})
            if not as_json:
                print(f"📦 {name} — ERROR: {e}\n")

    if as_json:
        out = {"database": DB_NAME, "collections": results}
        print(json.dumps(out, default=json_serial, indent=2))
    else:
        print(f"{'='*60}")
        print("  HOW IT FITS TOGETHER (pipeline)")
        print(f"{'='*60}")
        print("  Phase 1 (data collection)    → urls, scraped_data")
        print("  Phase 2 (classification)     → classified_chunks (from scraped_data)")
        print("  Phase 3 (embeddings)        → embedded_chunks (from classified_chunks); not used by live app")
        print("  Live chatbot (server_prime) → reads classified_chunks (keyword search), writes chat_sessions + chat_history")
        print("  Auth                        → users (register/login)")
        print("  Optional / legacy            → qa_cache, chat_data, chat, web_answers")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
