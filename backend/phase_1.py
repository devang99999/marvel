import os
import time
import random
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from pymongo import MongoClient
from serpapi import GoogleSearch
from playwright.sync_api import sync_playwright


load_dotenv()

# === CONFIG ===
SERP_API_KEY = os.getenv("SERP_API_KEY")
MONGO_URI = os.getenv("mongo")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DB_NAME = "marvel_crawler"
COLLECTION_URLS = "urls"
COLLECTION_SCRAPED = "scraped_data"

# === Mongo Setup ===
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
urls_collection = db[COLLECTION_URLS]
scraped_collection = db[COLLECTION_SCRAPED]

# === LLM-based Dynamic Search Query Generation ===
def generate_search_queries(topic="marvel characters", n=1):
    print("🤖 Generating search queries using LLaMA via Groq HTTP API...")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Give me a list of {n} specific, diverse search queries related to '{topic}' for information gathering. "
                    "Include character names, biographies, powers, history, etc. One query per line, no numbering."
                )
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        queries = [line.strip() for line in content.split("\n") if line.strip()]
        print(f"✅ Got {len(queries)} queries from LLM.")
        return queries
    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return [topic]  # Fallback to original topic if API fails


# === Search URLs ===
def run_search(query):
    print(f"🔍 Searching for: {query}")
    search = GoogleSearch({"q": query, "api_key": SERP_API_KEY, "num": 20})
    results = search.get_dict()
    urls = [r.get('link') for r in results.get("organic_results", []) if r.get("link")]
    print(f"✅ Found {len(urls)} URLs for query '{query}'")
    return urls

# === BeautifulSoup Scraper ===
def scrape_with_bs(url):
    try:
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            print(f"❌ Request failed with status {res.status_code} for {url}")
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        content = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))
        if len(content) < 200:
            print(f"⚠️ Content too short with BeautifulSoup for {url}")
            return None
        return {"url": url, "title": title, "content": content, "method": "beautifulsoup"}
    except Exception as e:
        print(f"❌ BS scrape error for {url}: {e}")
        return None

# === Playwright Scraper ===
def scrape_with_playwright(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_load_state("networkidle")
            soup = BeautifulSoup(page.content(), "html.parser")
            browser.close()
            title = soup.title.string.strip() if soup.title else ""
            content = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))
            if len(content) < 200:
                print(f"⚠️ Content too short with Playwright for {url}")
                return None
            return {"url": url, "title": title, "content": content, "method": "playwright"}
    except Exception as e:
        print(f"❌ Playwright scrape error for {url}: {e}")
        return None

# === Combined Scraper ===
def scrape_url(url):
    print(f"🕷️ Scraping: {url}")
    result = scrape_with_bs(url)
    if result:
        return result
    print(f"➡️ Falling back to Playwright for {url}")
    return scrape_with_playwright(url)

# === Phase 1 Orchestration ===
def phase1_run():
    SEARCH_CATEGORIES = generate_search_queries("marvel characters")

    scraped_count = 0
    for query in SEARCH_CATEGORIES:
        urls = run_search(query)
        time.sleep(random.uniform(2, 5))

        for url in urls:
            if scraped_collection.find_one({"url": url}):
                print(f"⚡ Already scraped: {url}")
                continue

            scraped = scrape_url(url)
            if scraped:
                scraped.update({
                    "query": query,
                    "scrape_timestamp": time.time()
                })
                scraped_collection.insert_one(scraped)
                urls_collection.update_one(
                {"url": url},
                {"$set": {"query": query, "url": url, "timestamp": time.time()}},
                upsert=True
                )
                scraped_count += 1

            time.sleep(random.uniform(2, 4))

    print(f"✅ Scraped {scraped_count} new pages.")

if __name__ == "__main__":
    phase1_run()
