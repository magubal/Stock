from typing import List, Dict, Any
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from .base import BaseCollector

class ResearchReportCollector(BaseCollector):
    """증권사 리포트 수집기"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_urls = {
            'kiwoom': 'https://www.kiwoom.com',
            'miraeasset': 'https://www.miraeasset.com',
            'kbsec': 'https://securities.kbfg.com',
            'nhqv': 'https://www.nhqv.com'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def collect(self) -> List[Dict[str, Any]]:
        """여러 증권사 리포트 수집"""
        reports = []
        
        # 여러 증권사에서 병렬로 수집
        tasks = [
            self.collect_kiwoom_reports(),
            self.collect_miraeasset_reports(),
            self.collect_kbsec_reports(),
            self.collect_nhqv_reports()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                reports.extend(result)
            else:
                print(f"⚠️ 리포트 수집 오류: {result}")
        
        return reports
    
    async def collect_kiwoom_reports(self) -> List[Dict[str, Any]]:
        """키움증권 리포트 수집"""
        url = "https://www.kiwoom.com/h/invest/research/report/recommend.jspx"
        reports = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 리포트 목록 파싱
                        report_items = soup.select('.report-list li')
                        
                        for item in report_items:
                            try:
                                title_elem = item.select_one('.tit')
                                date_elem = item.select_one('.date')
                                link_elem = item.select_one('a')
                                
                                if title_elem and date_elem:
                                    title = title_elem.get_text(strip=True)
                                    date_str = date_elem.get_text(strip=True)
                                    link = urljoin(self.base_urls['kiwoom'], link_elem['href']) if link_elem else None
                                    
                                    reports.append({
                                        'title': title,
                                        'date': date_str,
                                        'link': link,
                                        'brokerage': '키움증권',
                                        'source': 'kiwoom'
                                    })
                            except Exception as e:
                                print(f"키움증권 리포트 파싱 오류: {e}")
                                continue
                        
            except Exception as e:
                print(f"키움증권 접속 오류: {e}")
        
        return reports
    
    async def collect_miraeasset_reports(self) -> List[Dict[str, Any]]:
        """미래에셋증권 리포트 수집"""
        url = "https://www.miraeasset.com/contents/research/researchList.jsp"
        reports = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 리포트 목록 파싱
                        report_items = soup.select('.research-list tr')
                        
                        for item in report_items:
                            try:
                                title_elem = item.select_one('.title')
                                date_elem = item.select_one('.date')
                                link_elem = item.select_one('a')
                                
                                if title_elem and date_elem:
                                    title = title_elem.get_text(strip=True)
                                    date_str = date_elem.get_text(strip=True)
                                    link = urljoin(self.base_urls['miraeasset'], link_elem['href']) if link_elem else None
                                    
                                    reports.append({
                                        'title': title,
                                        'date': date_str,
                                        'link': link,
                                        'brokerage': '미래에셋증권',
                                        'source': 'miraeasset'
                                    })
                            except Exception as e:
                                print(f"미래에셋증권 리포트 파싱 오류: {e}")
                                continue
                        
            except Exception as e:
                print(f"미래에셋증권 접속 오류: {e}")
        
        return reports
    
    async def collect_kbsec_reports(self) -> List[Dict[str, Any]]:
        """KB증권 리포트 수집"""
        url = "https://securities.kbfg.com/research/report/reportList.do"
        reports = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 리포트 목록 파싱
                        report_items = soup.select('.report-row')
                        
                        for item in report_items:
                            try:
                                title_elem = item.select_one('.report-title')
                                date_elem = item.select_one('.report-date')
                                link_elem = item.select_one('a')
                                
                                if title_elem and date_elem:
                                    title = title_elem.get_text(strip=True)
                                    date_str = date_elem.get_text(strip=True)
                                    link = urljoin(self.base_urls['kbsec'], link_elem['href']) if link_elem else None
                                    
                                    reports.append({
                                        'title': title,
                                        'date': date_str,
                                        'link': link,
                                        'brokerage': 'KB증권',
                                        'source': 'kbsec'
                                    })
                            except Exception as e:
                                print(f"KB증권 리포트 파싱 오류: {e}")
                                continue
                        
            except Exception as e:
                print(f"KB증권 접속 오류: {e}")
        
        return reports
    
    async def collect_nhqv_reports(self) -> List[Dict[str, Any]]:
        """NH투자증권 리포트 수집"""
        url = "https://www.nhqv.com/research/researchList.do"
        reports = []
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 리포트 목록 파싱
                        report_items = soup.select('.research-item')
                        
                        for item in report_items:
                            try:
                                title_elem = item.select_one('.item-title')
                                date_elem = item.select_one('.item-date')
                                link_elem = item.select_one('a')
                                
                                if title_elem and date_elem:
                                    title = title_elem.get_text(strip=True)
                                    date_str = date_elem.get_text(strip=True)
                                    link = urljoin(self.base_urls['nhqv'], link_elem['href']) if link_elem else None
                                    
                                    reports.append({
                                        'title': title,
                                        'date': date_str,
                                        'link': link,
                                        'brokerage': 'NH투자증권',
                                        'source': 'nhqv'
                                    })
                            except Exception as e:
                                print(f"NH투자증권 리포트 파싱 오류: {e}")
                                continue
                        
            except Exception as e:
                print(f"NH투자증권 접속 오류: {e}")
        
        return reports
    
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """리포트 데이터 파싱 및 표준화"""
        
        # 종목 코드 추출 (정규식)
        title = raw_data.get('title', '')
        stock_code = self.extract_stock_code(title)
        stock_name = self.extract_stock_name(title)
        
        # 추천 의견 추출
        recommendation = self.extract_recommendation(title)
        
        # 목표가 추출
        target_price = self.extract_target_price(title)
        
        # 날짜 파싱
        parsed_date = self.parse_date(raw_data.get('date', ''))
        
        return {
            'title': title,
            'content': '',  # 상세 내용은 별도 수집 필요
            'pdf_url': raw_data.get('link'),
            'brokerage': raw_data.get('brokerage'),
            'author': '',  # 작성자 정보는 상세 페이지에서 수집 필요
            'target_price': target_price,
            'recommendation': recommendation,
            'published_at': parsed_date,
            'stock_code': stock_code,
            'stock_name': stock_name,
            'source': raw_data.get('source'),
            'raw_data': raw_data
        }
    
    def extract_stock_code(self, text: str) -> str:
        """텍스트에서 종목 코드 추출"""
        # 종목 코드 패턴: A005930, 005930 등
        pattern = r'[A]?\d{6}'
        match = re.search(pattern, text)
        return match.group() if match else ''
    
    def extract_stock_name(self, text: str) -> str:
        """텍스트에서 종목명 추출 (단순 버전)"""
        # 종목명 추출 로직 (개선 필요)
        stock_names = ['삼성전자', 'LG에너지솔루션', 'SK하이닉스', '현대차', '기아']
        for name in stock_names:
            if name in text:
                return name
        return ''
    
    def extract_recommendation(self, text: str) -> str:
        """텍스트에서 추천 의견 추출"""
        text_lower = text.lower()
        
        if '매수' in text or 'buy' in text_lower:
            return 'buy'
        elif '매도' in text or 'sell' in text_lower:
            return 'sell'
        elif '보유' in text or 'hold' in text_lower or 'neutral' in text_lower:
            return 'hold'
        
        return 'hold'  # 기본값
    
    def extract_target_price(self, text: str) -> float:
        """텍스트에서 목표가 추출"""
        # 목표가 패턴: 80,000원, 80000원 등
        pattern = r'[\d,]+원'
        matches = re.findall(pattern, text)
        
        if matches:
            # 첫번째 가격을 목표가로 간주
            price_str = matches[0].replace(',', '').replace('원', '')
            try:
                return float(price_str)
            except ValueError:
                pass
        
        return None
    
    def parse_date(self, date_str: str) -> datetime:
        """날짜 문자열 파싱"""
        # 다양한 날짜 형식 지원
        date_formats = [
            '%Y-%m-%d',
            '%Y.%m.%d',
            '%Y/%m/%d',
            '%m-%d',
            '%m.%d',
            '%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                if len(date_str.split('.')[0]) == 4:  # 연도 포함
                    return datetime.strptime(date_str, fmt)
                else:  # 연도 없으면 현재 연도 추가
                    current_year = datetime.now().year
                    date_with_year = f"{current_year}.{date_str}"
                    return datetime.strptime(date_with_year, f"%Y.{fmt}")
            except ValueError:
                continue
        
        # 파싱 실패시 현재 시간 반환
        return datetime.now()
    
    async def save_to_db(self, data: Dict[str, Any]):
        """데이터베이스 저장 (구현 예정)"""
        # TODO: SQLAlchemy를 사용한 DB 저장 로직 구현
        print(f"💾 DB 저장 예정: {data['title'][:50]}...")
        pass