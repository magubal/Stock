from typing import List, Dict, Any
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from .base import BaseCollector

class NewsCollector(BaseCollector):
    """뉴스 수집기 - 주요 경제 뉴스 사이트"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.news_sources = {
            'yna': {
                'name': '연합뉴스',
                'base_url': 'https://www.yna.co.kr',
                'list_url': 'https://www.yna.co.kr/economy',
                'selectors': {
                    'list': '.news-list li',
                    'title': '.tit a',
                    'time': '.time',
                    'content': '.story-news article'
                }
            },
            'hankyung': {
                'name': '한국경제',
                'base_url': 'https://www.hankyung.com',
                'list_url': 'https://www.hankyung.com/economy',
                'selectors': {
                    'list': '.article-list li',
                    'title': '.tit a',
                    'time': '.date',
                    'content': '.article-view'
                }
            },
            'maeil': {
                'name': '매일경제',
                'base_url': 'https://www.mk.co.kr',
                'list_url': 'https://www.mk.co.kr/news/economy/',
                'selectors': {
                    'list': '.article_list li',
                    'title': '.tit a',
                    'time': '.date',
                    'content': '.center_col'
                }
            },
            'edaily': {
                'name': '이데일리',
                'base_url': 'https://www.edaily.co.kr',
                'list_url': 'https://www.edaily.co.kr/News/NewsRead.ec?newsId=026',
                'selectors': {
                    'list': '.news_list li',
                    'title': '.news_title a',
                    'time': '.date_time',
                    'content': '.article_body'
                }
            }
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def collect(self) -> List[Dict[str, Any]]:
        """여러 뉴스 소스에서 병렬로 뉴스 수집"""
        all_news = []
        
        # 여러 뉴스 소스에서 병렬로 수집
        tasks = [
            self.collect_yna_news(),
            self.collect_hankyung_news(),
            self.collect_maeil_news(),
            self.collect_edaily_news()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            else:
                print(f"⚠️ 뉴스 수집 오류: {result}")
        
        # 중복 제거 (제목 기준)
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title = news.get('title', '')
            if title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(news)
        
        # 최신 뉴스 100개로 제한
        return sorted(unique_news, key=lambda x: x.get('published_at', ''), reverse=True)[:100]
    
    async def collect_yna_news(self) -> List[Dict[str, Any]]:
        """연합뉴스 수집"""
        source_config = self.news_sources['yna']
        news_list = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                # 뉴스 목록 페이지
                async with session.get(source_config['list_url']) as response:
                    if response.status != 200:
                        print(f"연합뉴스 접속 실패: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 뉴스 기사 목록 파싱
                    news_items = soup.select(source_config['selectors']['list'])
                    
                    for item in news_items[:20]:  # 최대 20개만 수집
                        try:
                            title_elem = item.select_one(source_config['selectors']['title'])
                            time_elem = item.select_one(source_config['selectors']['time'])
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            full_url = urljoin(source_config['base_url'], link)
                            published_time = self.parse_news_time(time_elem.get_text(strip=True)) if time_elem else datetime.now()
                            
                            # 상세 내용 수집
                            content = await self.get_news_content(session, full_url, source_config['selectors']['content'])
                            
                            news_data = {
                                'title': title,
                                'content': content,
                                'url': full_url,
                                'published_at': published_time,
                                'source': 'yna',
                                'source_name': source_config['name']
                            }
                            
                            news_list.append(news_data)
                            
                        except Exception as e:
                            print(f"연합뉴스 기사 파싱 오류: {e}")
                            continue
                    
            except Exception as e:
                print(f"연합뉴스 전체 수집 오류: {e}")
        
        return news_list
    
    async def collect_hankyung_news(self) -> List[Dict[str, Any]]:
        """한국경제 수집"""
        source_config = self.news_sources['hankyung']
        news_list = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(source_config['list_url']) as response:
                    if response.status != 200:
                        print(f"한국경제 접속 실패: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    news_items = soup.select(source_config['selectors']['list'])
                    
                    for item in news_items[:20]:
                        try:
                            title_elem = item.select_one(source_config['selectors']['title'])
                            time_elem = item.select_one(source_config['selectors']['time'])
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            full_url = urljoin(source_config['base_url'], link)
                            published_time = self.parse_news_time(time_elem.get_text(strip=True)) if time_elem else datetime.now()
                            
                            content = await self.get_news_content(session, full_url, source_config['selectors']['content'])
                            
                            news_list.append({
                                'title': title,
                                'content': content,
                                'url': full_url,
                                'published_at': published_time,
                                'source': 'hankyung',
                                'source_name': source_config['name']
                            })
                            
                        except Exception as e:
                            print(f"한국경제 기사 파싱 오류: {e}")
                            continue
                    
            except Exception as e:
                print(f"한국경제 전체 수집 오류: {e}")
        
        return news_list
    
    async def collect_maeil_news(self) -> List[Dict[str, Any]]:
        """매일경제 수집"""
        source_config = self.news_sources['maeil']
        news_list = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(source_config['list_url']) as response:
                    if response.status != 200:
                        print(f"매일경제 접속 실패: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    news_items = soup.select(source_config['selectors']['list'])
                    
                    for item in news_items[:20]:
                        try:
                            title_elem = item.select_one(source_config['selectors']['title'])
                            time_elem = item.select_one(source_config['selectors']['time'])
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            full_url = urljoin(source_config['base_url'], link)
                            published_time = self.parse_news_time(time_elem.get_text(strip=True)) if time_elem else datetime.now()
                            
                            content = await self.get_news_content(session, full_url, source_config['selectors']['content'])
                            
                            news_list.append({
                                'title': title,
                                'content': content,
                                'url': full_url,
                                'published_at': published_time,
                                'source': 'maeil',
                                'source_name': source_config['name']
                            })
                            
                        except Exception as e:
                            print(f"매일경제 기사 파싱 오류: {e}")
                            continue
                    
            except Exception as e:
                print(f"매일경제 전체 수집 오류: {e}")
        
        return news_list
    
    async def collect_edaily_news(self) -> List[Dict[str, Any]]:
        """이데일리 수집"""
        source_config = self.news_sources['edaily']
        news_list = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(source_config['list_url']) as response:
                    if response.status != 200:
                        print(f"이데일리 접속 실패: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    news_items = soup.select(source_config['selectors']['list'])
                    
                    for item in news_items[:20]:
                        try:
                            title_elem = item.select_one(source_config['selectors']['title'])
                            time_elem = item.select_one(source_config['selectors']['time'])
                            
                            if not title_elem:
                                continue
                            
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            full_url = urljoin(source_config['base_url'], link)
                            published_time = self.parse_news_time(time_elem.get_text(strip=True)) if time_elem else datetime.now()
                            
                            content = await self.get_news_content(session, full_url, source_config['selectors']['content'])
                            
                            news_list.append({
                                'title': title,
                                'content': content,
                                'url': full_url,
                                'published_at': published_time,
                                'source': 'edaily',
                                'source_name': source_config['name']
                            })
                            
                        except Exception as e:
                            print(f"이데일리 기사 파싱 오류: {e}")
                            continue
                    
            except Exception as e:
                print(f"이데일리 전체 수집 오류: {e}")
        
        return news_list
    
    async def get_news_content(self, session: aiohttp.ClientSession, url: str, content_selector: str) -> str:
        """개별 뉴스 기사 상세 내용 수집"""
        try:
            # 딜레이 적용 (서버 부하 방지)
            await asyncio.sleep(self.config.get('request_delay', 1.0))
            
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 기사 내용 파싱
                    content_elem = soup.select_one(content_selector)
                    if content_elem:
                        # 불필요한 태그 제거
                        for tag in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                            tag.decompose()
                        
                        content = content_elem.get_text(strip=True)
                        # 여러 공백을 단일 공백으로 정리
                        content = re.sub(r'\s+', ' ', content)
                        return content
                    else:
                        # 대체 선택자 시도
                        alt_selectors = [
                            '.article-body',
                            '#articleBody',
                            '.news-body',
                            '.content',
                            'article p'
                        ]
                        
                        for selector in alt_selectors:
                            content_elem = soup.select_one(selector)
                            if content_elem:
                                return content_elem.get_text(strip=True)
                        
                        return "내용 수집 실패"
                else:
                    return f"HTTP 오류: {response.status}"
                    
        except Exception as e:
            return f"내용 수집 오류: {str(e)}"
    
    def parse_news_time(self, time_str: str) -> datetime:
        """뉴스 시간 파싱"""
        if not time_str:
            return datetime.now()
        
        # 다양한 시간 형식 파싱
        time_patterns = [
            r'(\d{4})[-./](\d{1,2})[-./](\d{1,2})\s*(\d{1,2}):(\d{2})',  # 2023-12-01 14:30
            r'(\d{1,2})[-./](\d{1,2})\s*(\d{1,2}):(\d{2})',  # 12-01 14:30
            r'(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2}):(\d{2})',  # 12월 1일 14:30
            r'(\d{1,2}):(\d{2})',  # 14:30 (오늘 뉴스)
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, time_str)
            if match:
                groups = match.groups()
                
                if len(groups) == 5:  # 년월일시분
                    year, month, day, hour, minute = map(int, groups)
                elif len(groups) == 4:  # 월일시분
                    now = datetime.now()
                    year = now.year
                    month, day, hour, minute = map(int, groups)
                elif len(groups) == 2:  # 시분
                    now = datetime.now()
                    year, month, day = now.year, now.month, now.day
                    hour, minute = map(int, groups)
                else:
                    continue
                
                return datetime(year, month, day, hour, minute)
        
        # 파싱 실패시 현재 시간 반환
        return datetime.now()
    
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 데이터 파싱 및 표준화"""
        
        # 종목 코드 추출
        title = raw_data.get('title', '')
        content = raw_data.get('content', '')
        full_text = f"{title} {content}"
        
        stock_codes = self.extract_stock_codes(full_text)
        stock_names = self.extract_stock_names(full_text)
        
        # 중요도 평가
        importance_score = self.calculate_importance(title, content)
        
        # 감성 분석 (간단 버전)
        sentiment_score = self.analyze_sentiment(title, content)
        
        # 카테고리 분류
        category = self.classify_news_category(title, content)
        
        return {
            'title': raw_data.get('title'),
            'content': raw_data.get('content'),
            'url': raw_data.get('url'),
            'published_at': raw_data.get('published_at'),
            'author': raw_data.get('author', ''),
            'source_id': None,  # TODO: 데이터베이스 ID 설정
            'sentiment_score': sentiment_score,
            'importance_score': importance_score,
            'stock_mentions': ','.join(stock_codes) if stock_codes else None,
            'category': category,
            'source_name': raw_data.get('source_name'),
            'raw_source': raw_data.get('source')
        }
    
    def extract_stock_codes(self, text: str) -> List[str]:
        """텍스트에서 종목 코드 추출"""
        # 종목 코드 패턴: A005930, 005930 등
        pattern = r'[A]?\d{6}'
        codes = re.findall(pattern, text)
        return list(set(codes))  # 중복 제거
    
    def extract_stock_names(self, text: str) -> List[str]:
        """텍스트에서 주요 종목명 추출"""
        # 주요 종목명 리스트 (확장 가능)
        stock_names = [
            '삼성전자', 'LG에너지솔루션', 'SK하이닉스', '현대차', '기아',
            '삼성바이오로직스', '셀트리온', '삼성SDI', 'LG화학', 'POSCO홀딩스',
            'NAVER', '카카오', '삼성전기', 'SK텔레콤', 'LG유플러스',
            'KB금융', '신한지주', '하나금융지주', '우리금융지주', 'KB금융'
        ]
        
        found_names = []
        text_lower = text.lower()
        
        for name in stock_names:
            if name in text:
                found_names.append(name)
        
        return list(set(found_names))
    
    def calculate_importance(self, title: str, content: str) -> float:
        """뉴스 중요도 점수 계산 (0-1)"""
        importance = 0.5  # 기본 점수
        
        # 제목에 핵심 키워드 포함 시 가중치
        title_lower = title.lower()
        
        high_importance_keywords = [
            '실적', '실적발표', '분기', '매출', '영업이익', '순이익',
            '결산', '배당', '분배', '액면분할', '증자', '유상증자',
            'M&A', '인수', '합병', '매각', '스핀오프',
            '정책', '규제', '금리', '환율', '유가', '금값'
        ]
        
        for keyword in high_importance_keywords:
            if keyword in title_lower:
                importance += 0.1
        
        # 종목 코드 언급 시 가중치
        if self.extract_stock_codes(f"{title} {content}"):
            importance += 0.1
        
        # 주요 종목명 언급 시 가중치
        if self.extract_stock_names(f"{title} {content}"):
            importance += 0.1
        
        # 길이가 긴 기사는 중요할 가능성
        if len(content) > 1000:
            importance += 0.05
        
        return min(importance, 1.0)  # 최대 1.0으로 제한
    
    def analyze_sentiment(self, title: str, content: str) -> float:
        """간단한 감성 분석 (-1 부정 ~ 1 긍정)"""
        text = f"{title} {content}".lower()
        
        # 긍정 키워드
        positive_keywords = [
            '상승', '급등', '상향', '호조', '호실적', '개선', '증가',
            '최고', '신고', '돌파', '성장', '기대', '긍정', '낙관'
        ]
        
        # 부정 키워드
        negative_keywords = [
            '하락', '급락', '하향', '부진', '악화', '감소', '하락세',
            '최저', '신저', '하락', '위기', '리스크', '우려', '부정'
        ]
        
        positive_count = sum(1 for keyword in positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in negative_keywords if keyword in text)
        
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0  # 중립
        
        return (positive_count - negative_count) / total_keywords
    
    def classify_news_category(self, title: str, content: str) -> str:
        """뉴스 카테고리 분류"""
        text = f"{title} {content}".lower()
        
        categories = {
            '시장동향': ['코스피', '코스닥', '시장', '지수', '주가', '투자'],
            '실적공시': ['실적', '매출', '영업이익', '순이익', '분기', '결산'],
            '기업공시': ['공시', 'M&A', '인수', '합병', '매각', '지분'],
            '금융정책': ['금리', '환율', '정책', '규제', '한은', 'Fed'],
            '산업동향': ['산업', '섹터', '시장', '트렌드', '전망'],
            '해외증시': ['다우', '나스닥', 'S&P', '월가', '미국', '중국', '일본']
        }
        
        max_score = 0
        best_category = '일반뉴스'
        
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > max_score:
                max_score = score
                best_category = category
        
        return best_category
    
    async def save_to_db(self, data: Dict[str, Any]):
        """데이터베이스 저장 (구현 예정)"""
        # TODO: SQLAlchemy를 사용한 DB 저장 로직 구현
        print(f"💾 뉴스 저장 예정: {data['title'][:50]}...")
        pass