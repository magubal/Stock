import requests
import datetime
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(name, url):
    print(f"Testing {name} ({url})...", end="", flush=True)
    try:
        start = datetime.datetime.now()
        response = requests.get(url, timeout=10)
        duration = (datetime.datetime.now() - start).total_seconds()
        print(f" Status: {response.status_code}, Time: {duration:.2f}s")
        if response.status_code != 200:
            print(f"  Response: {response.text[:200]}")
            return False
        else:
            # Check for key fields
            data = response.json()
            if "disclosures" in url:
                print(f"  Data keys: {list(data.keys())}")
            elif "liquidity" in url:
                print(f"  Data keys: {list(data.keys())}")
            elif "moat" in url:
                print(f"  Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            return True
    except Exception as e:
        print(f" Error: {e}")
        return False

def main():
    print("=== Verifying Fix for Market Daily Digest ===")
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    results = []
    results.append(test_endpoint("Daily Digest", f"{BASE_URL}/api/v1/daily-digest/{today}"))
    results.append(test_endpoint("Disclosures", f"{BASE_URL}/api/v1/disclosures"))
    results.append(test_endpoint("Liquidity Stress", f"{BASE_URL}/api/v1/liquidity-stress"))
    results.append(test_endpoint("Moat Dashboard", f"{BASE_URL}/api/v1/moat-dashboard"))
    results.append(test_endpoint("News Articles", f"{BASE_URL}/api/v1/news-intel/articles?limit=5"))
    results.append(test_endpoint("Blog Posts", f"{BASE_URL}/api/v1/blog-review/posts"))
    results.append(test_endpoint("Cross Module Context", f"{BASE_URL}/api/v1/cross-module/context"))

    if all(results):
        print("\nALL TESTS PASSED. The dashboard should load correctly.")
    else:
        print("\nSOME TESTS FAILED.")

if __name__ == "__main__":
    main()
