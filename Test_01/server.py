"""
Stock Data Server with News
----------------------------
Flask 기반 API 서버
- Yahoo Finance에서 주가 데이터 가져오기
- SQLite DB에 저장
- 네이버 뉴스 검색
- 시장 이슈 검색
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import requests
from datetime import datetime, timedelta
from urllib.parse import quote
import os
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Database 파일 경로
DB_PATH = os.path.join(os.path.dirname(__file__), 'stock_data.db')

# 종목명 매핑 (코드 -> 이름)
STOCK_CODE_TO_NAME = {
    '005930': '삼성전자',
    '000660': 'SK하이닉스',
    '373220': 'LG에너지솔루션',
    '207940': '삼성바이오로직스',
    '005380': '현대차',
    '000270': '기아',
    '068270': '셀트리온',
    '006400': '삼성SDI',
    '105560': 'KB금융',
    '055550': '신한지주',
    '035420': '네이버',
    '035720': '카카오',
    '005490': '포스코홀딩스',
    '012330': '현대모비스',
    '051910': 'LG화학',
}


def init_db():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_info (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            currency TEXT,
            market TEXT,
            last_updated TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[OK] Database initialized: {DB_PATH}")


def get_yahoo_symbol(input_symbol):
    """종목코드를 Yahoo Finance 심볼로 변환"""
    input_symbol = input_symbol.strip().upper()
    if input_symbol.isdigit() and len(input_symbol) == 6:
        return input_symbol + '.KS'
    return input_symbol


def fetch_from_yahoo(symbol, interval='1d', range_period='3mo'):
    """Yahoo Finance API에서 데이터 가져오기"""
    yahoo_symbol = get_yahoo_symbol(symbol)
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
    params = {'interval': interval, 'range': range_period}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if 'chart' in data and data['chart']['result']:
            return data['chart']['result'][0], yahoo_symbol
        
        if yahoo_symbol.endswith('.KS'):
            yahoo_symbol = symbol + '.KQ'
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if 'chart' in data and data['chart']['result']:
                return data['chart']['result'][0], yahoo_symbol
        
        return None, yahoo_symbol
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None, yahoo_symbol


def save_to_db(symbol, data):
    """데이터를 SQLite에 저장"""
    if not data:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    meta = data.get('meta', {})
    timestamps = data.get('timestamp', [])
    quotes = data.get('indicators', {}).get('quote', [{}])[0]
    
    cursor.execute('''
        INSERT OR REPLACE INTO stock_info (symbol, name, currency, market, last_updated)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        symbol,
        meta.get('shortName', meta.get('symbol', symbol)),
        meta.get('currency', 'KRW'),
        meta.get('exchangeName', 'Unknown'),
        datetime.now().isoformat()
    ))
    
    saved_count = 0
    for i, ts in enumerate(timestamps):
        if ts is None:
            continue
        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO stock_prices (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, date_str,
                quotes.get('open', [None])[i] if i < len(quotes.get('open', [])) else None,
                quotes.get('high', [None])[i] if i < len(quotes.get('high', [])) else None,
                quotes.get('low', [None])[i] if i < len(quotes.get('low', [])) else None,
                quotes.get('close', [None])[i] if i < len(quotes.get('close', [])) else None,
                quotes.get('volume', [None])[i] if i < len(quotes.get('volume', [])) else None
            ))
            saved_count += 1
        except Exception as e:
            print(f"Error saving row: {e}")
    
    conn.commit()
    conn.close()
    return saved_count


def get_from_db(symbol, start_date=None, end_date=None):
    """SQLite에서 데이터 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = 'SELECT date, open, high, low, close, volume FROM stock_prices WHERE symbol = ?'
    params = [symbol]
    
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    
    query += ' ORDER BY date ASC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    cursor.execute('SELECT name, currency, market FROM stock_info WHERE symbol = ?', [symbol])
    info = cursor.fetchone()
    
    conn.close()
    return rows, info


def fetch_google_news_rss(query, max_count=8, max_days=3):
    """Google News RSS에서 뉴스 가져오기 - 3일 이내만 필터링"""
    import xml.etree.ElementTree as ET
    from html import unescape
    from email.utils import parsedate_to_datetime
    
    encoded_query = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(response.content)
        
        news_items = []
        items = root.findall('.//item')
        now = datetime.now()
        
        print(f"[GNEWS] Found {len(items)} items for '{query}'")
        
        for item in items[:max_count * 3]:
            try:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                source = item.find('source').text if item.find('source') is not None else ''
                
                # 날짜 파싱 및 3일 이내 필터링
                try:
                    dt = parsedate_to_datetime(pub_date)
                    days_ago = (now - dt.replace(tzinfo=None)).days
                    if days_ago > max_days:
                        continue  # 3일 넘은 기사 제외
                except:
                    continue  # 날짜 파싱 실패시 제외
                
                desc_elem = item.find('description')
                description = ''
                if desc_elem is not None and desc_elem.text:
                    desc_soup = BeautifulSoup(unescape(desc_elem.text), 'html.parser')
                    description = desc_soup.get_text(strip=True)
                
                if not title or not link:
                    continue
                
                time_str = format_time(pub_date)
                
                news_items.append({
                    'title': title,
                    'description': description[:200] + '...' if len(description) > 200 else description,
                    'link': link,
                    'source': source or '뉴스',
                    'time': time_str,
                    'days_ago': days_ago,
                    'timestamp': dt
                })
                
            except Exception as e:
                print(f"Error parsing RSS item: {e}")
                continue
        
        # 최신순 정렬
        news_items.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)
        
        # timestamp 제거하고 반환
        result = []
        for item in news_items[:max_count]:
            item.pop('timestamp', None)
            item.pop('days_ago', None)
            result.append(item)
        
        print(f"[GNEWS] Filtered to {len(result)} items within {max_days} days")
        return result
        
    except Exception as e:
        print(f"Error fetching Google News: {e}")
        return []


def fetch_dart_disclosures(stock_code, max_count=5, max_days=3):
    """DART OpenAPI를 사용하여 공시 정보 가져오기"""
    DART_API_KEY = "78e6c22ce8b530b1cb7c8bf085b6150a3a15c7ea"
    
    # 종목코드로 기업 고유번호(corp_code) 조회 필요
    # DART API는 corp_code를 요구하지만, 종목코드로 조회 가능한 API 사용
    
    # 공시검색 API: https://opendart.fss.or.kr/api/list.json
    today = datetime.now()
    bgn_de = (today - timedelta(days=max_days)).strftime('%Y%m%d')
    end_de = today.strftime('%Y%m%d')
    
    url = "https://opendart.fss.or.kr/api/list.json"
    params = {
        'crtfc_key': DART_API_KEY,
        'corp_code': '',  # 비워두면 전체 검색
        'bgn_de': bgn_de,
        'end_de': end_de,
        'page_count': 100,
        'page_no': 1
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 먼저 종목코드로 corp_code 찾기 (corpCode.xml에서)
        corp_code = get_corp_code(stock_code, DART_API_KEY)
        
        if corp_code:
            params['corp_code'] = corp_code
            print(f"[DART] Found corp_code: {corp_code} for stock: {stock_code}")
        else:
            print(f"[DART] Could not find corp_code for stock: {stock_code}")
            return []
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        data = response.json()
        
        if data.get('status') != '000':
            print(f"[DART] API Error: {data.get('message', 'Unknown error')}")
            return []
        
        disclosures = []
        items = data.get('list', [])
        
        print(f"[DART] Found {len(items)} disclosures for {stock_code}")
        
        for item in items[:max_count]:
            try:
                title = item.get('report_nm', '')
                rcept_no = item.get('rcept_no', '')
                rcept_dt = item.get('rcept_dt', '')
                corp_name = item.get('corp_name', '')
                
                # DART 공시 링크 생성
                link = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
                
                # 날짜 포맷팅
                if rcept_dt and len(rcept_dt) == 8:
                    formatted_date = f"{rcept_dt[:4]}.{rcept_dt[4:6]}.{rcept_dt[6:]}"
                else:
                    formatted_date = rcept_dt
                
                disclosures.append({
                    'title': f'[공시] {title}',
                    'description': f'{corp_name}: {title}',
                    'link': link,
                    'source': 'DART',
                    'time': formatted_date,
                    'is_disclosure': True
                })
                
            except Exception as e:
                print(f"[DART] Error parsing disclosure: {e}")
                continue
        
        return disclosures
        
    except Exception as e:
        print(f"[DART] Error fetching disclosures: {e}")
        return []


# Corp Code 캐시 (메모리)
_corp_code_cache = {}

def get_corp_code(stock_code, api_key):
    """종목코드로 DART corp_code 조회"""
    global _corp_code_cache
    
    # 캐시에 있으면 바로 반환
    if stock_code in _corp_code_cache:
        return _corp_code_cache[stock_code]
    
    # DART corpCode.xml 다운로드 및 파싱
    # 이 파일은 크기가 크므로 한번만 다운로드하고 캐싱
    try:
        import zipfile
        import io
        import xml.etree.ElementTree as ET
        
        url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
        
        print(f"[DART] Downloading corp code list...")
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            print(f"[DART] Failed to download corp codes: {response.status_code}")
            return None
        
        # ZIP 파일 압축 해제
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            xml_content = z.read('CORPCODE.xml')
        
        root = ET.fromstring(xml_content)
        
        # 모든 기업 코드 캐싱
        for corp in root.findall('.//list'):
            code = corp.findtext('stock_code', '').strip()
            corp_code = corp.findtext('corp_code', '').strip()
            if code and corp_code:
                _corp_code_cache[code] = corp_code
        
        print(f"[DART] Cached {len(_corp_code_cache)} corp codes")
        
        return _corp_code_cache.get(stock_code)
        
    except Exception as e:
        print(f"[DART] Error getting corp code: {e}")
        return None


def fetch_naver_finance_news(stock_code, max_count=5):
    """네이버 금융 뉴스 - 실제 기사 링크 제공"""
    url = f"https://finance.naver.com/item/news_news.naver?code={stock_code}&page=1"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.naver.com/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'euc-kr'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = []
        rows = soup.select('table.type5 tbody tr')
        
        print(f"[NFIN] Found {len(rows)} rows for code '{stock_code}'")
        
        for row in rows[:max_count * 2]:
            try:
                title_elem = row.select_one('td.title a')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')
                
                if href.startswith('/'):
                    link = 'https://finance.naver.com' + href
                else:
                    link = href
                
                source_elem = row.select_one('td.info')
                source = source_elem.get_text(strip=True) if source_elem else ''
                
                date_elem = row.select_one('td.date')
                time_str = date_elem.get_text(strip=True) if date_elem else ''
                
                if title and link:
                    news_items.append({
                        'title': title,
                        'description': f'{source}: {title}',
                        'link': link,
                        'source': source or '언론사',
                        'time': time_str or '최근'
                    })
                    
            except Exception as e:
                continue
        
        return news_items[:max_count]
        
    except Exception as e:
        print(f"Error fetching Naver Finance news: {e}")
        return []


def calculate_importance(title, description, source, query):
    """뉴스 중요도 점수 계산"""
    score = 0
    query_words = query.replace(' 주식', '').split()
    
    for word in query_words:
        if word in title:
            score += 10
    
    major_sources = ['연합뉴스', '조선일보', '중앙일보', '동아일보', '한국경제', 
                     '매일경제', 'SBS', 'KBS', 'MBC', 'JTBC', '서울경제', '파이낸셜뉴스']
    for ms in major_sources:
        if ms in source:
            score += 5
            break
    
    important_keywords = ['실적', '공시', '발표', 'AI', '반도체', '상승', '하락', 
                         '신고가', '투자', '매수', '매도', '전망', '분석', '급등', '급락']
    for kw in important_keywords:
        if kw in title:
            score += 3
    
    if '속보' in title or '긴급' in title or '단독' in title:
        score += 8
    
    return score


def format_time(pub_date):
    """RSS pubDate를 한국어 시간으로 변환"""
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


def fetch_news_combined(query, stock_code=None, max_count=8, max_days=3):
    """여러 소스에서 뉴스를 가져와 통합 - 3일 이내만, 최신순 정렬"""
    all_news = []
    disclosures = []
    
    # 1. Google News RSS (3일 이내)
    google_news = fetch_google_news_rss(query, max_count=6, max_days=max_days)
    all_news.extend(google_news)
    
    # 2. DART 공시 (3일 이내)
    if stock_code and stock_code.isdigit() and len(stock_code) == 6:
        disclosures = fetch_dart_disclosures(stock_code, max_count=3, max_days=max_days)
    
    # 중복 제거
    seen_titles = set()
    unique_news = []
    for item in all_news:
        title_key = item['title'][:20]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_news.append(item)
    
    # 공시는 뉴스 앞에 배치
    result = disclosures + unique_news
    
    # 뉴스가 없으면 빈 리스트 반환
    if not result:
        print(f"[NEWS] No news within {max_days} days for '{query}'")
    
    return result[:max_count]


# ==================== API Endpoints ====================

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock_data(symbol):
    """주가 데이터 API"""
    symbol = symbol.upper()
    interval = request.args.get('interval', '1d')
    range_period = request.args.get('range', '3mo')
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if range_period == '3mo':
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    elif range_period == '6mo':
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    else:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # 주봉은 항상 Yahoo에서 직접 가져옴
    if interval == '1wk':
        print(f"[FETCH] Weekly data - fetching from Yahoo Finance: {symbol}")
        yahoo_data, yahoo_symbol = fetch_from_yahoo(symbol, interval, range_period)
        
        if yahoo_data:
            meta = yahoo_data.get('meta', {})
            timestamps = yahoo_data.get('timestamp', [])
            quotes = yahoo_data.get('indicators', {}).get('quote', [{}])[0]
            
            labels = [datetime.fromtimestamp(ts).strftime('%Y-%m-%d') for ts in timestamps if ts]
            prices = [quotes.get('close', [None])[i] for i in range(len(timestamps)) if timestamps[i]]
            
            current_price = prices[-1] if prices else 0
            prev_price = prices[-2] if len(prices) > 1 else current_price
            price_change = current_price - prev_price if prev_price else 0
            percent_change = (price_change / prev_price * 100) if prev_price else 0
            
            return jsonify({
                'success': True,
                'symbol': symbol,
                'name': meta.get('shortName', symbol),
                'currency': meta.get('currency', 'KRW'),
                'market': meta.get('exchangeName', 'Unknown'),
                'currentPrice': current_price,
                'priceChange': price_change,
                'percentChange': round(percent_change, 2),
                'labels': labels,
                'prices': prices,
                'dataSource': 'yahoo_weekly',
                'recordCount': len(prices)
            })
        else:
            return jsonify({'success': False, 'error': '종목을 찾을 수 없습니다.'}), 404
    
    # 일봉은 DB 캐시 사용
    db_rows, db_info = get_from_db(symbol, start_date, end_date)
    
    if range_period == '6mo':
        expected_min_records = 100
    else:
        expected_min_records = 50
    
    data_insufficient = len(db_rows) < expected_min_records
    
    if not db_rows or data_insufficient or force_refresh:
        reason = "no data" if not db_rows else f"insufficient ({len(db_rows)}/{expected_min_records})" if data_insufficient else "force refresh"
        print(f"[FETCH] Fetching from Yahoo Finance: {symbol} ({reason})")
        yahoo_data, yahoo_symbol = fetch_from_yahoo(symbol, interval, range_period)
        
        if yahoo_data:
            saved = save_to_db(symbol, yahoo_data)
            print(f"[SAVE] Saved {saved} records to DB")
            db_rows, db_info = get_from_db(symbol, start_date, end_date)
        else:
            return jsonify({'success': False, 'error': '종목을 찾을 수 없습니다.'}), 404
    else:
        print(f"[DB] Loaded from DB: {symbol} ({len(db_rows)} records)")
    
    labels = [row[0] for row in db_rows]
    prices = [row[4] for row in db_rows]
    
    if prices:
        current_price = prices[-1]
        prev_price = prices[-2] if len(prices) > 1 and prices[-2] else current_price
        price_change = current_price - prev_price
        percent_change = (price_change / prev_price) * 100 if prev_price else 0
    else:
        current_price = price_change = percent_change = 0
    
    return jsonify({
        'success': True,
        'symbol': symbol,
        'name': db_info[0] if db_info else symbol,
        'currency': db_info[1] if db_info else 'KRW',
        'market': db_info[2] if db_info else 'Unknown',
        'currentPrice': current_price,
        'priceChange': price_change,
        'percentChange': round(percent_change, 2),
        'labels': labels,
        'prices': prices,
        'dataSource': 'database',
        'recordCount': len(db_rows)
    })


@app.route('/api/news/<symbol>', methods=['GET'])
def get_stock_news(symbol):
    """종목 관련 뉴스 API"""
    symbol = symbol.upper()
    
    # 종목코드를 종목명으로 변환
    stock_name = STOCK_CODE_TO_NAME.get(symbol, symbol)
    
    # DB에서 종목명 가져오기 시도
    if stock_name == symbol:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM stock_info WHERE symbol = ?', [symbol])
        result = cursor.fetchone()
        conn.close()
        if result:
            stock_name = result[0]
    
    print(f"[NEWS] Fetching news for: {stock_name} (code: {symbol})")
    news_items = fetch_news_combined(stock_name + " 주식", stock_code=symbol, max_count=8)
    
    return jsonify({
        'success': True,
        'symbol': symbol,
        'stockName': stock_name,
        'news': news_items,
        'count': len(news_items)
    })


def fetch_kita_trade_news(max_count=10):
    """KITA 무역뉴스 스크래핑 - 원문 링크 포함"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        list_url = 'https://www.kita.net/board/totalTradeNews/totalTradeNewsList.do'
        response = requests.get(list_url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = []
        
        # goDetailPage 패턴이 있는 링크 찾기
        links = soup.find_all('a', onclick=re.compile(r'goDetailPage'))
        
        for link in links[:max_count]:
            try:
                onclick = link.get('onclick', '')
                title = link.get_text(strip=True)
                
                # goDetailPage('98789', '2') 패턴에서 번호 추출
                match = re.search(r"goDetailPage\('(\d+)',\s*'(\d+)'\)", onclick)
                if match:
                    no = match.group(1)
                    site_id = match.group(2)
                    
                    # KITA 상세 페이지 URL
                    detail_url = f'https://www.kita.net/board/totalTradeNews/totalTradeNewsDetail.do?no={no}&siteId={site_id}'
                    
                    # 날짜 찾기
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
            except Exception as e:
                print(f"[KITA] Error parsing item: {e}")
                continue
        
        print(f"[KITA] Fetched {len(news_items)} trade news")
        return news_items
        
    except Exception as e:
        print(f"[KITA] Error fetching news: {e}")
        return []


@app.route('/api/market-issues', methods=['GET'])
def get_market_issues():
    """시장 핵심 이슈 API - KITA 무역뉴스 포함"""
    # KITA 무역뉴스 (메인) - 최근 1일치 모두 포함 위해 30개 조회
    kita_news = fetch_kita_trade_news(max_count=30)
    
    # Google News에서 증시 이슈 (보조)
    stock_issues = fetch_google_news_rss("코스피 증시", max_count=4, max_days=3)
    
    return jsonify({
        'success': True,
        'issues': kita_news,  # KITA 무역뉴스를 메인으로
        'risks': stock_issues,  # 증시 뉴스를 보조로
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/stocks', methods=['GET'])
def list_stocks():
    """저장된 종목 목록"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT symbol, name, currency, market, last_updated FROM stock_info ORDER BY last_updated DESC')
    rows = cursor.fetchall()
    conn.close()
    
    stocks = [{'symbol': r[0], 'name': r[1], 'currency': r[2], 'market': r[3], 'lastUpdated': r[4]} for r in rows]
    
    return jsonify({'success': True, 'stocks': stocks, 'count': len(stocks)})


@app.route('/api/kita-news', methods=['GET'])
def get_kita_news():
    """KITA 무역뉴스 전용 API"""
    count = request.args.get('count', 10, type=int)
    news = fetch_kita_trade_news(max_count=min(count, 20))
    
    return jsonify({
        'success': True,
        'news': news,
        'count': len(news),
        'source': 'KITA 한국무역협회',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'status': 'ok',
        'database': DB_PATH,
        'timestamp': datetime.now().isoformat()
    })


# ==================== Main ====================

if __name__ == '__main__':
    print("=" * 50)
    print("Stock Data Server Starting...")
    print("=" * 50)
    
    init_db()
    
    print("\n[API] Endpoints:")
    print("   GET /api/stock/<symbol>  - Stock data")
    print("   GET /api/news/<symbol>   - Stock news")
    print("   GET /api/market-issues   - Market issues (KITA)")
    print("   GET /api/kita-news       - KITA Trade News")
    print("   GET /api/stocks          - Saved stocks list")
    print("   GET /api/health          - Health check")
    print("\n[SERVER] Running at: http://localhost:5000")
    print("=" * 50 + "\n")
    
    app.run(debug=True, port=5000)
