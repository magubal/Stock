"""
Data Collection Service
-----------------------
Skill: data-collection
Workflows: /01-data-collection

뉴스, 보고서, 시세 등 데이터 수집
"""

import requests
from datetime import datetime, timedelta
from urllib.parse import quote
from bs4 import BeautifulSoup
import re


class DataCollectionService:
    """Data Collection Skill Implementation"""
    
    def __init__(self, config):
        self.config = config
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    # ==================== Stock Data ====================
    
    def get_yahoo_symbol(self, input_symbol):
        """종목코드를 Yahoo Finance 심볼로 변환"""
        input_symbol = input_symbol.strip().upper()
        if input_symbol.isdigit() and len(input_symbol) == 6:
            return input_symbol + '.KS'
        return input_symbol
    
    def fetch_stock_data(self, symbol, interval='1d', range_period='3mo'):
        """Yahoo Finance에서 주가 데이터 수집"""
        yahoo_symbol = self.get_yahoo_symbol(symbol)
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        params = {'interval': interval, 'range': range_period}
        
        try:
            response = requests.get(url, params=params, headers=self.headers, 
                                   timeout=self.config.get('YAHOO_TIMEOUT', 10))
            data = response.json()
            
            if 'chart' in data and data['chart']['result']:
                return data['chart']['result'][0], yahoo_symbol
            
            # KOSDAQ 시도
            if yahoo_symbol.endswith('.KS'):
                yahoo_symbol = symbol + '.KQ'
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
                response = requests.get(url, params=params, headers=self.headers, timeout=10)
                data = response.json()
                
                if 'chart' in data and data['chart']['result']:
                    return data['chart']['result'][0], yahoo_symbol
            
            return None, yahoo_symbol
            
        except Exception as e:
            print(f"[DataCollection] Error fetching stock data: {e}")
            return None, yahoo_symbol
    
    # ==================== News Data ====================
    
    def fetch_google_news(self, query, max_count=8, max_days=3):
        """Google News RSS에서 뉴스 수집"""
        import xml.etree.ElementTree as ET
        from html import unescape
        from email.utils import parsedate_to_datetime
        
        encoded_query = quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            root = ET.fromstring(response.content)
            
            news_items = []
            items = root.findall('.//item')
            now = datetime.now()
            
            for item in items[:max_count * 3]:
                try:
                    title = item.find('title').text if item.find('title') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    source = item.find('source').text if item.find('source') is not None else ''
                    
                    try:
                        dt = parsedate_to_datetime(pub_date)
                        days_ago = (now - dt.replace(tzinfo=None)).days
                        if days_ago > max_days:
                            continue
                    except:
                        continue
                    
                    desc_elem = item.find('description')
                    description = ''
                    if desc_elem is not None and desc_elem.text:
                        desc_soup = BeautifulSoup(unescape(desc_elem.text), 'html.parser')
                        description = desc_soup.get_text(strip=True)
                    
                    if not title or not link:
                        continue
                    
                    time_str = self._format_time(pub_date)
                    
                    news_items.append({
                        'title': title,
                        'description': description[:200] + '...' if len(description) > 200 else description,
                        'link': link,
                        'source': source or '뉴스',
                        'time': time_str,
                        'timestamp': dt
                    })
                    
                except Exception:
                    continue
            
            news_items.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
            
            result = []
            for item in news_items[:max_count]:
                item.pop('timestamp', None)
                result.append(item)
            
            return result
            
        except Exception as e:
            print(f"[DataCollection] Error fetching Google News: {e}")
            return []
    
    def fetch_kita_news(self, max_count=10):
        """KITA 무역뉴스 수집"""
        try:
            list_url = 'https://www.kita.net/board/totalTradeNews/totalTradeNewsList.do'
            response = requests.get(list_url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            links = soup.find_all('a', onclick=re.compile(r'goDetailPage'))
            
            for link in links[:max_count]:
                try:
                    onclick = link.get('onclick', '')
                    title = link.get_text(strip=True)
                    
                    match = re.search(r"goDetailPage\('(\d+)',\s*'(\d+)'\)", onclick)
                    if match:
                        no = match.group(1)
                        site_id = match.group(2)
                        detail_url = f'https://www.kita.net/board/totalTradeNews/totalTradeNewsDetail.do?no={no}&siteId={site_id}'
                        
                        parent = link.find_parent('li')
                        date = ''
                        if parent:
                            text = parent.get_text()
                            date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', text)
                            if date_match:
                                date = date_match.group(1)
                        
                        news_items.append({
                            'title': title,
                            'description': title,
                            'link': detail_url,
                            'source': 'KITA 무역뉴스',
                            'time': date or '최근'
                        })
                except Exception:
                    continue
            
            return news_items
            
        except Exception as e:
            print(f"[DataCollection] Error fetching KITA news: {e}")
            return []
    
    def _format_time(self, pub_date):
        """시간 포맷팅"""
        if not pub_date:
            return '최근'
        
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date)
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f'{diff.days}일 전'
            elif diff.seconds > 3600:
                return f'{diff.seconds // 3600}시간 전'
            elif diff.seconds > 60:
                return f'{diff.seconds // 60}분 전'
            else:
                return '방금 전'
        except:
            return pub_date[:10] if len(pub_date) > 10 else pub_date
