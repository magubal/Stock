import requests
import datetime
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(name, url):
    print(f"Testing {name} ({url})...", end="", flush=True)
    try:
        start = datetime.datetime.now()
        response = requests.get(url, timeout=10)
        duration = (datetime.datetime.now() - start).total_seconds()
        print(f" Status: {response.status_code}, Time: {duration:.2f}s")
        if response.status_code != 200:
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f" Error: {e}")

today = datetime.datetime.now().strftime("%Y-%m-%d")

# 1. Daily Digest for today
test_endpoint("Daily Digest", f"{BASE_URL}/daily-digest/{today}")

# 2. Module endpoints
modules = [
    ("Disclosures", f"{BASE_URL}/disclosures?date={today}"),
    ("News", f"{BASE_URL}/news-intel/articles?date={today}"),
    ("Liquidity", f"{BASE_URL}/liquidity-stress/current?date={today}"),
    ("Moat", f"{BASE_URL}/moat/dashboard/stats?date={today}"),
    ("Intelligence", f"{BASE_URL}/cross-module/context?date={today}"),
    ("Blog", f"{BASE_URL}/blog-review/posts?date={today}"),
]

for name, url in modules:
    test_endpoint(name, url)
