"""
SerpAPI helper: cache responses + monthly budget so the free tier (100 req/month) doesn't exhaust.

Usage:
  from serp_helper import serp_search, get_serp_cached, save_serp_cached, can_use_serp_api

  # Get search results (from cache if fresh, else call API if under budget)
  results = serp_search(query, api_key=SERPAPI_KEY, num=20)
  # results = list of organic_results dicts, or None if budget exceeded / API error

  # For phase_4: can also cache scraped content so we don't re-scrape
  doc = get_serp_cached(query)
  if doc and doc.get("content"):
      return doc["content"]
  results = serp_search(query, api_key=..., num=1)
  ... scrape first URL ...
  save_serp_cached(query, results, content=scraped_text)
"""
import os
import re
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

try:
    import certifi
    from pymongo import MongoClient
except ImportError:
    certifi = None
    MongoClient = None

# Config
MONTHLY_LIMIT = int(os.environ.get("SERPAPI_MONTHLY_LIMIT", "100"))
CACHE_DAYS = int(os.environ.get("SERPAPI_CACHE_DAYS", "30"))

_db = None
_collection = None
_budget_collection = None


def _get_db():
    global _db, _collection, _budget_collection
    if _db is not None:
        return _db, _collection, _budget_collection
    uri = os.getenv("mongo")
    if not uri or not MongoClient:
        return None, None, None
    client = MongoClient(uri, tlsCAFile=certifi.where() if certifi else None)
    _db = client["marvel_crawler"]
    _collection = _db["serp_cache"]
    _budget_collection = _db["api_budget"]
    return _db, _collection, _budget_collection


def _normalize_query(q):
    if not q or not isinstance(q, str):
        return ""
    return " ".join(re.sub(r"\s+", " ", q.lower().strip()).split())


def get_serp_cached(query, max_age_days=None):
    """Return cached doc { organic_results, content?, updated_at } or None."""
    db, coll, _ = _get_db()
    if not coll:
        return None
    norm = _normalize_query(query)
    if not norm:
        return None
    max_age = timedelta(days=max_age_days or CACHE_DAYS)
    doc = coll.find_one({"query_norm": norm})
    if not doc:
        return None
    updated = doc.get("updated_at")
    if updated:
        if getattr(updated, "tzinfo", None) is None:
            updated = updated.replace(tzinfo=timezone.utc) if isinstance(updated, datetime) else datetime.fromtimestamp(updated, tz=timezone.utc)
        if datetime.now(timezone.utc) - updated > max_age:
            return None
    return doc


def save_serp_cached(query, organic_results, content=None):
    """Store or update cache for this query. Optionally store scraped content."""
    db, coll, _ = _get_db()
    if not coll:
        return
    norm = _normalize_query(query)
    if not norm:
        return
    now = datetime.now(timezone.utc)
    update = {
        "query": query,
        "query_norm": norm,
        "organic_results": organic_results,
        "updated_at": now,
    }
    if content is not None:
        update["content"] = content
    coll.update_one(
        {"query_norm": norm},
        {"$set": update, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )


def can_use_serp_api():
    """True if we're under the monthly limit."""
    _, _, budget_coll = _get_db()
    if not budget_coll:
        return True
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    doc = budget_coll.find_one({"_id": "serpapi"})
    if not doc or doc.get("month") != month:
        return True
    return (doc.get("count") or 0) < MONTHLY_LIMIT


def record_serp_use():
    """Increment monthly usage (call after a successful API request). New month = counter effectively resets."""
    _, _, budget_coll = _get_db()
    if not budget_coll:
        return
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    doc = budget_coll.find_one({"_id": "serpapi"})
    if doc and doc.get("month") != month:
        budget_coll.update_one({"_id": "serpapi"}, {"$set": {"month": month, "count": 1}}, upsert=True)
    else:
        budget_coll.update_one(
            {"_id": "serpapi"},
            {"$set": {"month": month}, "$inc": {"count": 1}},
            upsert=True,
        )


def serp_search(query, api_key, num=20):
    """
    Get organic_results: from cache if fresh, else call SerpAPI if under budget.
    Returns list of result dicts, or None if budget exceeded or API error.
    """
    norm = _normalize_query(query)
    if not norm:
        return None

    doc = get_serp_cached(query)
    if doc and doc.get("organic_results") is not None:
        return doc["organic_results"]

    if not can_use_serp_api():
        return None

    url = f"https://serpapi.com/search.json?q={requests.utils.quote(query)}&num={num}&api_key={api_key}"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        data = res.json()
        results = data.get("organic_results") or []
        record_serp_use()
        save_serp_cached(query, results)
        return results
    except Exception as e:
        return None
