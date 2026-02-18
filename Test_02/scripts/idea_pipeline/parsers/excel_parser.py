"""Excel 일일작업 데이터 파서 (7개 카테고리)"""
import re
from datetime import date, datetime
from typing import List
from .base_parser import BaseParser, DailyWorkRow


# 카테고리 한글 → 코드 매핑
CATEGORY_MAP = {
    "시장섹터선호변화": "SECTOR",
    "섹터선호": "SECTOR",
    "미국시장이슈및동향": "US_MARKET",
    "미국시장이슈": "US_MARKET",
    "미국시장": "US_MARKET",
    "시장테마흐름": "THEME",
    "테마흐름": "THEME",
    "시장테마": "THEME",
    "주식시장리스크": "RISK",
    "리스크": "RISK",
    "현금비중": "RISK",
    "익일시장추정": "NEXT_DAY",
    "익일시장추정및대응": "NEXT_DAY",
    "익일시장": "NEXT_DAY",
    "투자시장": "PORTFOLIO",
    "보유종목": "PORTFOLIO",
    "투자시장 및 보유종목": "PORTFOLIO",
    "AI 리서치": "AI_RESEARCH",
    "AI리서치": "AI_RESEARCH",
    "투자시장 AI": "AI_RESEARCH",
    "시장이슈": "US_MARKET",
    "시장강세스타일": "SECTOR",
    "강세스타일": "SECTOR",
    "주식시장심리": "RISK",
    "심리및방향성": "RISK",
    "방향성분석": "RISK",
    "중장기투자관점": "PORTFOLIO",
    "시장중장기": "PORTFOLIO",
    "투자관점": "PORTFOLIO",
    "익일시장추정결과": "NEXT_DAY",
    "시장섹터평가": "SECTOR",
    "방향성추정": "RISK",
    "투자진입매력도": "RISK",
    "인테리어": "PORTFOLIO",
}


def _match_category(raw: str) -> str:
    """원본 카테고리 텍스트를 코드로 변환"""
    cleaned = raw.strip().replace(" ", "")
    # 정확 매치
    for k, v in CATEGORY_MAP.items():
        if k.replace(" ", "") == cleaned:
            return v
    # 부분 매치
    for k, v in CATEGORY_MAP.items():
        if k.replace(" ", "") in cleaned or cleaned in k.replace(" ", ""):
            return v
    return "UNKNOWN"


class ExcelParser(BaseParser):
    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith((".xlsx", ".xls"))

    def parse(self, file_path: str) -> List[DailyWorkRow]:
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl이 필요합니다: pip install openpyxl")

        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        wb.close()

        if not rows:
            return []

        # 헤더 분석: 날짜, 업무카테고리, 설명/목적, 링크, 상세내용
        header = [str(c or "").strip() for c in rows[0]]
        col_map = _detect_columns(header)

        results = []
        for row in rows[1:]:
            if not row or all(c is None for c in row):
                continue

            raw_date = _get_cell(row, col_map.get("date"))
            raw_cat = str(_get_cell(row, col_map.get("category")) or "")
            raw_desc = str(_get_cell(row, col_map.get("description")) or "")
            raw_content = str(_get_cell(row, col_map.get("content")) or "")
            raw_link = str(_get_cell(row, col_map.get("link")) or "")

            if not raw_content.strip():
                continue

            # 날짜 파싱
            parsed_date = _parse_date(raw_date)
            if not parsed_date:
                continue

            category = _match_category(raw_cat)

            results.append(DailyWorkRow(
                date=parsed_date,
                category=category,
                description=raw_desc[:500],
                content=raw_content,
                source_link=raw_link[:500],
                source_type="excel",
            ))

        return results


def _detect_columns(header: List[str]) -> dict:
    """헤더에서 컬럼 인덱스 자동 감지"""
    col_map = {}
    for i, h in enumerate(header):
        hl = h.lower().replace(" ", "")
        if "날짜" in hl or "일자" in hl or "date" in hl:
            col_map["date"] = i
        elif "카테고리" in hl or "업무" in hl or "구분" in hl or "category" in hl:
            col_map["category"] = i
        elif "설명" in hl or "목적" in hl or "description" in hl:
            col_map["description"] = i
        elif "상세" in hl or "내용" in hl or "리서치" in hl or "content" in hl or "detail" in hl:
            col_map["content"] = i
        elif "링크" in hl or "link" in hl or "url" in hl or "session" in hl:
            col_map["link"] = i
    return col_map


def _get_cell(row, idx):
    if idx is None or idx >= len(row):
        return None
    return row[idx]


def _parse_date(val) -> date:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None
