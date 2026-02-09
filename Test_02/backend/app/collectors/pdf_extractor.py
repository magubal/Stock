from typing import List, Dict, Any
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from .base import BaseCollector

class PDFReportCollector(BaseCollector):
    """PDF 리포트 상세 내용 수집기"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf, application/octet-stream',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3'
        }
    
    async def collect(self) -> List[Dict[str, Any]]:
        """PDF 리포트 URL 목록에서 상세 내용 수집"""
        # TODO: 데이터베이스에서 수집할 리포트 목록 가져오기
        report_urls = [
            'https://www.miraeasset.com/resources/research/2023/ABC123.pdf',
            # 실제 URL 목록으로 대체 필요
        ]
        
        reports = []
        
        for url in report_urls:
            try:
                report_data = await self.extract_pdf_content(url)
                if report_data:
                    reports.append(report_data)
                
                # 요청 간 딜레이
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"PDF 리포트 수집 실패 {url}: {e}")
                continue
        
        return reports
    
    async def extract_pdf_content(self, pdf_url: str) -> Dict[str, Any]:
        """PDF에서 텍스트 추출"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        # PDF 다운로드 및 텍스트 추출
                        pdf_content = await response.read()
                        
                        # PyMuPDF나 pdfplumber로 텍스트 추출 (별도 설치 필요)
                        text = await self.extract_text_from_pdf(pdf_content)
                        
                        return {
                            'pdf_url': pdf_url,
                            'content': text,
                            'extracted_at': datetime.now()
                        }
                    else:
                        print(f"PDF 다운로드 실패: {response.status}")
                        return None
                        
            except Exception as e:
                print(f"PDF 파싱 실패: {e}")
                return None
    
    async def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """PDF 바이너리에서 텍스트 추출"""
        # TODO: PyMuPDF(fitz)나 pdfplumber 설치 후 구현
        # 예시 구조:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            print("⚠️ PyMuPDF가 설치되지 않음. pip install PyMuPDF 필요")
            return ""
        except Exception as e:
            print(f"PDF 텍스트 추출 실패: {e}")
            return ""
    
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """PDF 내용에서 구조화된 데이터 추출"""
        content = raw_data.get('content', '')
        
        # 투자의견 추출
        recommendation = self.extract_recommendation_from_text(content)
        
        # 목표가 추출
        target_price = self.extract_target_price_from_text(content)
        
        # 핵심 내용 요약
        summary = self.extract_summary(content)
        
        return {
            'content': content,
            'recommendation': recommendation,
            'target_price': target_price,
            'summary': summary,
            'pdf_url': raw_data.get('pdf_url'),
            'extracted_at': raw_data.get('extracted_at')
        }
    
    def extract_recommendation_from_text(self, text: str) -> str:
        """리포트 내용에서 투자의견 추출"""
        recommendation_patterns = [
            r'투자의견[:\s]*([가-힣]+)',
            r'의견[:\s]*([가-힣]+)',
            r'추천[:\s]*([가-힣]+)',
            r'매수강도[:\s]*([0-9]+)',
        ]
        
        for pattern in recommendation_patterns:
            match = re.search(pattern, text)
            if match:
                opinion = match.group(1)
                if '매수' in opinion or '강매수' in opinion or 'Buy' in opinion:
                    return 'buy'
                elif '매도' in opinion or '강매도' in opinion or 'Sell' in opinion:
                    return 'sell'
                elif '보유' in opinion or '중립' in opinion or 'Hold' in opinion:
                    return 'hold'
        
        return 'hold'  # 기본값
    
    def extract_target_price_from_text(self, text: str) -> float:
        """리포트 내용에서 목표가 추출"""
        # 목표가 관련 패턴
        target_price_patterns = [
            r'목표가[:\s]*([0-9,]+)원',
            r'Target Price[:\s]*\$?([0-9,]+)',
            r'12개월 목표가[:\s]*([0-9,]+)원',
            r'B/S[:\s]*([0-9,]+)원',  # Buy/Sell price
        ]
        
        for pattern in target_price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                price_str = matches[0].replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def extract_summary(self, text: str) -> str:
        """리포트 내용 요약"""
        # 첫 문단이나 주요 섹션 추출
        lines = text.split('\n')
        summary_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not line.startswith('▲'):  # 의미 있는 문장
                summary_lines.append(line)
                if len(summary_lines) >= 3:  # 처음 3문장
                    break
        
        return ' '.join(summary_lines) if summary_lines else text[:200]
    
    async def save_to_db(self, data: Dict[str, Any]):
        """데이터베이스 저장 (구현 예정)"""
        # TODO: 기존 리포트 레코드 업데이트
        print(f"💾 리포트 내용 저장 예정: {data.get('summary', '')[:50]}...")
        pass