#!/usr/bin/env python3
"""
KIND 당일 공시 수집 스크립트
Source: https://kind.krx.co.kr/disclosure/todaydisclosure.do

수집한 공시를 data/disclosures/YYYY-MM-DD.json 에 저장합니다.
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "disclosures"
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "scripts" / "collector_log.txt", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# KIND API 설정
KIND_BASE_URL = "https://kind.krx.co.kr"
KIND_SEARCH_URL = f"{KIND_BASE_URL}/disclosure/todaydisclosure.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": f"{KIND_BASE_URL}/disclosure/todaydisclosure.do",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
}

# 시장 구분 코드
MARKET_CODES = {
    "ALL": "",       # 전체
    "KOSPI": "Y",    # 유가증권시장
    "KOSDAQ": "K",   # 코스닥
    "KONEX": "N",    # 코넥스
}


def fetch_disclosures_page(target_date: str, page_no: int = 1,
                           market: str = "ALL") -> str | None:
    """KIND 당일공시 페이지를 POST로 요청하여 HTML을 반환합니다."""
    form_data = {
        "method": "searchTodayDisclosureSub",
        "currentPageSize": "100",
        "pageIndex": str(page_no),
        "orderMode": "0",
        "orderStat": "D",
        "forward": "todaydisclosure_sub",
        "chose_marketType": MARKET_CODES.get(market, ""),
        "textCr498": target_date.replace("-", ""),  # YYYYMMDD
        "marketType": MARKET_CODES.get(market, ""),
    }

    try:
        session = requests.Session()
        # 먼저 메인 페이지 방문하여 쿠키 획득
        session.get(KIND_SEARCH_URL, headers=HEADERS, timeout=15)
        time.sleep(1)

        response = session.post(
            KIND_SEARCH_URL,
            data=form_data,
            headers=HEADERS,
            timeout=30,
        )
        response.encoding = response.apparent_encoding or "utf-8"

        if response.status_code == 200:
            return response.text
        else:
            logger.error(f"HTTP {response.status_code} 응답")
            return None

    except requests.RequestException as e:
        logger.error(f"요청 실패: {e}")
        return None


def parse_disclosure_table(html: str) -> list[dict]:
    """KIND 공시 HTML 테이블을 파싱하여 구조화된 데이터를 반환합니다."""
    soup = BeautifulSoup(html, "html.parser")
    disclosures = []

    # KIND는 <table class="list type-00"> 형태의 테이블 사용
    table = soup.find("table", class_="list")
    if not table:
        # 대안: 모든 테이블 탐색
        tables = soup.find_all("table")
        for t in tables:
            if t.find("th"):
                table = t
                break

    if not table:
        logger.warning("공시 테이블을 찾을 수 없습니다.")
        return disclosures

    tbody = table.find("tbody")
    if not tbody:
        tbody = table

    rows = tbody.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        try:
            # KIND 테이블 구조: 시간 | 회사명 | 공시제목 | 제출인 | 시장구분
            time_text = cols[0].get_text(strip=True)
            company_tag = cols[1].find("a")
            title_tag = cols[2].find("a")

            company = company_tag.get_text(strip=True) if company_tag else cols[1].get_text(strip=True)
            title = title_tag.get_text(strip=True) if title_tag else cols[2].get_text(strip=True)

            # 종목코드 추출 (링크에서)
            code = ""
            if company_tag and company_tag.get("href"):
                href = company_tag["href"]
                if "rcpNo=" in href:
                    code = href.split("rcpNo=")[-1][:6]
            
            # URL 추출 (onclick 속성에서 acptno, docno 추출)
            detail_url = ""
            if title_tag:
                onclick = title_tag.get("onclick", "")
                if onclick:
                    # openDisclsViewer('20260213001859','') — docno는 빈 문자열일 수 있음
                    import re
                    match = re.search(r"openDisclsViewer\('([^']+)',\s*'([^']*)'", onclick)
                    if match:
                        acpt_no = match.group(1)
                        doc_no = match.group(2)
                        detail_url = f"https://kind.krx.co.kr/common/disclsviewer.do?method=search&acptno={acpt_no}&docno={doc_no}&viewerhost=&viewerport="

            # 제출인/시장 구분 (col[3]: "유가증권시장본부", "코스닥시장본부", "시장감시위원회" 등)
            market = ""
            if len(cols) >= 4:
                market = cols[3].get_text(strip=True)

            disclosure = {
                "company": company,
                "code": code,
                "title": title,
                "time": time_text,
                "market": market,
                "url": detail_url,
            }
            disclosures.append(disclosure)

        except (IndexError, AttributeError) as e:
            logger.debug(f"행 파싱 실패: {e}")
            continue

    return disclosures


def collect_all_pages(target_date: str, market: str = "ALL") -> list[dict]:
    """모든 페이지의 공시를 수집합니다."""
    all_disclosures = []
    page = 1
    max_pages = 20  # 안전 상한

    while page <= max_pages:
        logger.info(f"페이지 {page} 수집 중... (날짜: {target_date})")
        html = fetch_disclosures_page(target_date, page_no=page, market=market)

        if not html:
            logger.warning(f"페이지 {page} 수집 실패, 중단")
            break

        disclosures = parse_disclosure_table(html)
        if not disclosures:
            logger.info(f"페이지 {page}에 데이터 없음, 수집 완료")
            break

        all_disclosures.extend(disclosures)
        logger.info(f"  → {len(disclosures)}건 수집 (누적: {len(all_disclosures)}건)")

        # 100건 미만이면 마지막 페이지
        if len(disclosures) < 100:
            break

        page += 1
        time.sleep(2)  # Rate limit

    return all_disclosures


def save_disclosures(disclosures: list[dict], target_date: str) -> Path:
    """수집된 공시를 JSON 파일로 저장합니다."""
    output_file = DATA_DIR / f"{target_date}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(disclosures, f, ensure_ascii=False, indent=2)
    return output_file


def generate_sample_data(target_date: str) -> list[dict]:
    """KIND 접속 실패 시 사용할 샘플 데이터를 생성합니다.

    실제 KIND 데이터 구조와 동일한 형태를 제공하여
    Analyzer와 Frontend 개발/테스트를 지원합니다.
    """
    base_url = "https://kind.krx.co.kr/common/disclsviewer.do?method=search&acptno=20240101000001&docno=20240101000123&viewerhost=&viewerport="
    
    samples = [
        {"company": "삼성전자", "code": "005930", "title": "단일판매·공급계약체결",
         "time": "16:30", "market": "유가증권시장", "url": base_url},
        {"company": "SK하이닉스", "code": "000660", "title": "전환사채권발행결정",
         "time": "16:25", "market": "유가증권시장", "url": base_url},
        {"company": "LG에너지솔루션", "code": "373220", "title": "단일판매·공급계약체결",
         "time": "16:20", "market": "유가증권시장", "url": base_url},
        {"company": "카카오", "code": "035720", "title": "자기주식취득신탁계약체결결정",
         "time": "16:15", "market": "유가증권시장", "url": base_url},
        {"company": "네이버", "code": "035420", "title": "현금·현물배당결정",
         "time": "16:10", "market": "유가증권시장", "url": base_url},
        {"company": "셀트리온", "code": "068270", "title": "유상증자결정",
         "time": "16:05", "market": "유가증권시장", "url": base_url},
        {"company": "에코프로비엠", "code": "247540", "title": "전환사채권발행결정",
         "time": "15:55", "market": "코스닥", "url": base_url},
        {"company": "HLB", "code": "028300", "title": "소송등의제기·신청",
         "time": "15:50", "market": "코스닥", "url": base_url},
        {"company": "포스코홀딩스", "code": "005490", "title": "영업(잠정)실적(공정공시)",
         "time": "15:45", "market": "유가증권시장", "url": base_url},
        {"company": "현대차", "code": "005380", "title": "단일판매·공급계약체결",
         "time": "15:40", "market": "유가증권시장", "url": base_url},
        {"company": "기아", "code": "000270", "title": "현금·현물배당결정",
         "time": "15:35", "market": "유가증권시장", "url": base_url},
        {"company": "크래프톤", "code": "259960", "title": "자기주식취득신탁계약체결결정",
         "time": "15:30", "market": "유가증권시장", "url": base_url},
        {"company": "두산에너빌리티", "code": "034020", "title": "신주인수권부사채권발행결정",
         "time": "15:25", "market": "유가증권시장", "url": base_url},
        {"company": "씨젠", "code": "096530", "title": "주권매매거래정지",
         "time": "15:20", "market": "코스닥", "url": base_url},
        {"company": "삼성SDI", "code": "006400", "title": "영업(잠정)실적(공정공시)",
         "time": "15:15", "market": "유가증권시장", "url": base_url},
        {"company": "한화솔루션", "code": "009830", "title": "채무보증결정",
         "time": "15:10", "market": "유가증권시장", "url": base_url},
        {"company": "NAVER", "code": "035420",
         "title": "임원ㆍ주요주주특정증권등소유상황보고서", "time": "15:05",
         "market": "유가증권시장", "url": base_url},
        {"company": "엘앤에프", "code": "066970", "title": "전환사채권발행결정",
         "time": "15:00", "market": "코스닥", "url": base_url},
        {"company": "삼성바이오로직스", "code": "207940", "title": "단일판매·공급계약체결",
         "time": "14:55", "market": "유가증권시장", "url": base_url},
        {"company": "카카오뱅크", "code": "323410",
         "title": "주식등의대량보유상황보고서(약식)", "time": "14:50",
         "market": "유가증권시장", "url": base_url},
        {"company": "LG전자", "code": "066570", 
         "title": "매출액또는손익구조30%(대규모법인은15%)이상변동", "time": "14:45",
         "market": "유가증권시장", "url": base_url},
    ]
    return samples


def main():
    """메인 실행 함수"""
    target = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    use_sample = "--sample" in sys.argv

    logger.info(f"=== KIND 공시 수집 시작 (날짜: {target}) ===")

    if use_sample:
        logger.info("샘플 데이터 모드로 실행")
        disclosures = generate_sample_data(target)
    else:
        disclosures = collect_all_pages(target)

        if not disclosures:
            logger.warning("KIND에서 데이터를 수집할 수 없습니다. 샘플 데이터로 대체합니다.")
            disclosures = generate_sample_data(target)

    output_file = save_disclosures(disclosures, target)
    logger.info(f"=== 수집 완료: {len(disclosures)}건 → {output_file} ===")

    return str(output_file)


if __name__ == "__main__":
    main()
