import requests
from bs4 import BeautifulSoup
import re

def check_page(page_num):
    url = f"https://www.kita.net/board/totalTradeNews/totalTradeNewsList.do?pageIndex={page_num}"
    print(f"Checking {url}")
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Get first news item
        item = soup.select_one('a[onclick*="goDetailPage"]')
        if item:
            print(f"Page {page_num} first item: {item.get_text(strip=True)[:30]}...")
            parent = item.find_parent('li')
            if parent:
                print(f"  Date: {parent.get_text()[-15:]}")
        else:
            print(f"Page {page_num}: No items found")
            
    except Exception as e:
        print(e)

check_page(1)
check_page(2)
