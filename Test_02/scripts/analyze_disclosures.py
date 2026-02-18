#!/usr/bin/env python3
"""
공시 분석 스크립트 — Event Taxonomy 기반 감성 분류 + Impact Score 산출

Input:  data/disclosures/YYYY-MM-DD.json (collect_disclosures.py 출력)
Output: dashboard/data/latest_disclosures.json (프론트엔드용)
"""

import sys
import re
import json
import time
import logging
from datetime import date, datetime
from pathlib import Path
from collections import Counter

import requests
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "disclosures"
DASHBOARD_DATA_DIR = PROJECT_ROOT / "dashboard" / "data"
DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ── Event Taxonomy ──────────────────────────────────────────────

RISK_ON_KEYWORDS = {
    "단일판매": {"event_class": "supply_contract", "badge": "공급계약", "score": (2, 5)},
    "공급계약": {"event_class": "supply_contract", "badge": "공급계약", "score": (2, 5)},
    "자기주식취득": {"event_class": "buyback", "badge": "자사주매입", "score": (3, 6)},
    "자기주식소각": {"event_class": "buyback_cancel", "badge": "자사주소각", "score": (4, 6)},
    "현금배당": {"event_class": "dividend", "badge": "배당", "score": (2, 4)},
    "현금·현물배당": {"event_class": "dividend", "badge": "배당", "score": (2, 4)},
    "무상증자": {"event_class": "bonus_issue", "badge": "무상증자", "score": (1, 3)},
    "영업실적등에대한전망": {"event_class": "earnings_guidance", "badge": "실적전망", "score": (3, 7)},
    "영업(잠정)실적": {"event_class": "earnings_surprise", "badge": "실적공시", "score": (3, 7)},
    "매출액또는손익구조": {"event_class": "earnings_variance", "badge": "손익구조", "score": (3, 7)},
}

RISK_OFF_KEYWORDS = {
    "유상증자": {"event_class": "rights_offering", "badge": "유상증자", "score": (-8, -5)},
    "전환사채": {"event_class": "cb_issuance", "badge": "CB발행", "score": (-5, -2)},
    "전환사채권발행": {"event_class": "cb_issuance", "badge": "CB발행", "score": (-5, -2)},
    "신주인수권부사채": {"event_class": "bw_issuance", "badge": "BW발행", "score": (-5, -2)},
    "신주인수권부사채권발행": {"event_class": "bw_issuance", "badge": "BW발행", "score": (-5, -2)},
    "매매거래정지": {"event_class": "suspension", "badge": "거래정지", "score": (-10, -10)},
    "주권매매거래정지": {"event_class": "suspension", "badge": "거래정지", "score": (-10, -10)},
    "불성실공시": {"event_class": "unfaithful", "badge": "불성실공시", "score": (-7, -4)},
    "소송": {"event_class": "lawsuit", "badge": "소송", "score": (-5, -2)},
    "채무보증": {"event_class": "debt_guarantee", "badge": "채무보증", "score": (-4, -2)},
}

NEUTRAL_KEYWORDS = {
    "임원ㆍ주요주주특정증권등소유상황보고서": {"event_class": "insider_report", "badge": "내부자보고", "score": (0, 0)},
    "주식등의대량보유상황보고서": {"event_class": "major_holding", "badge": "대량보유", "score": (0, 0)},
    "단순투자": {"event_class": "simple_investment", "badge": "단순투자", "score": (0, 0)},
    "소유상황보고": {"event_class": "insider_report", "badge": "내부자보고", "score": (0, 0)},
}


EARNINGS_CLASSES = ("earnings_surprise", "earnings_guidance", "earnings_variance")
CONTRACT_CLASSES = ("supply_contract",)

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Referer": "https://kind.krx.co.kr/",
}


def _get_doc_no(viewer_url: str) -> str:
    """KIND viewer 페이지에서 mainDoc select의 docNo를 추출합니다."""
    try:
        resp = requests.get(viewer_url, headers=_HTTP_HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        select = soup.find("select", id="mainDoc")
        if select:
            for opt in select.find_all("option"):
                val = opt.get("value", "")
                if "|" in val:
                    return val.split("|")[0]
    except Exception as e:
        logger.debug(f"docNo 추출 실패: {e}")
    return ""


def _get_htm_url(doc_no: str) -> str:
    """searchContents에서 실제 문서 HTM URL을 추출합니다."""
    try:
        url = f"https://kind.krx.co.kr/common/disclsviewer.do?method=searchContents&docNo={doc_no}"
        resp = requests.get(url, headers=_HTTP_HEADERS, timeout=15)
        resp.encoding = "utf-8"
        match = re.search(r"setPath\([^,]*,\s*'(https://[^']+\.htm)'", resp.text)
        if match:
            return match.group(1)
    except Exception as e:
        logger.debug(f"HTM URL 추출 실패: {e}")
    return ""


def _parse_financial_yoy(html: str) -> dict:
    """HTM 문서에서 매출액/영업이익 전년대비 증감률(%)을 추출합니다.

    손익구조30% 타입: Row = ['- 매출액', 당해, 직전, 증감금액, 증감비율(%), 흑자적자]
    잠정실적 타입:    Row = ['매출액', 당해실적, 당기, 전기, 전기대비%, -, 전년동기, 전년동기대비%, -]
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {"revenue_yoy": None, "op_profit_yoy": None}

    for table in soup.find_all("table"):
        text = table.get_text()
        if "매출" not in text:
            continue

        # 헤더에서 증감비율/증감률 컬럼 위치 파악
        yoy_col_idx = None
        header_row = None
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            cell_text = " ".join(cells)
            if "증감비율" in cell_text or "증감률" in cell_text:
                header_row = cells
                # 마지막 증감비율/증감률 컬럼 찾기 (전년동기대비가 더 뒤에 있음)
                for i in range(len(cells) - 1, -1, -1):
                    if "증감" in cells[i] and ("비율" in cells[i] or "률" in cells[i]):
                        yoy_col_idx = i
                        break
                break

        if yoy_col_idx is None:
            continue

        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cells) <= yoy_col_idx:
                continue

            label = cells[0].replace("-", "").strip()
            pct_text = cells[yoy_col_idx].replace(",", "").strip()

            pct_match = re.search(r"([-]?\d+\.?\d*)", pct_text)
            if not pct_match:
                continue

            pct = float(pct_match.group(1))

            if re.match(r"^매출", label) and result["revenue_yoy"] is None:
                result["revenue_yoy"] = pct
            elif re.match(r"^영업이익|^영업손익", label) and result["op_profit_yoy"] is None:
                result["op_profit_yoy"] = pct

    return result


def fetch_earnings_yoy(viewer_url: str) -> dict:
    """실적 공시 상세 페이지에서 매출액/영업이익 전년대비 증감률을 추출합니다.

    Returns: {"revenue_yoy": float|None, "op_profit_yoy": float|None}
    """
    result = {"revenue_yoy": None, "op_profit_yoy": None}

    doc_no = _get_doc_no(viewer_url)
    if not doc_no:
        return result
    time.sleep(0.5)

    htm_url = _get_htm_url(doc_no)
    if not htm_url:
        return result
    time.sleep(0.5)

    try:
        resp = requests.get(htm_url, headers=_HTTP_HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding or "euc-kr"
        result = _parse_financial_yoy(resp.text)
    except Exception as e:
        logger.debug(f"실적 상세 파싱 실패: {e}")

    return result


def enrich_earnings_scores(disclosures: list[dict]) -> int:
    """실적 관련 공시의 상세 페이지를 파싱하여 점수를 재산정합니다.

    Rules:
    - 매출액 또는 영업이익 전년대비 >= +30% → score +30
    - 매출액 또는 영업이익 전년대비 < 0%  → score -10
    - 그 외 → 기존 점수 유지

    Returns: 보강된 공시 건수
    """
    targets = [d for d in disclosures if d.get("event_class") in EARNINGS_CLASSES and d.get("url")]
    if not targets:
        return 0

    logger.info(f"실적 공시 {len(targets)}건 상세 분석 시작 (KIND 상세 페이지 접근)...")
    enriched_count = 0

    for i, item in enumerate(targets):
        yoy = fetch_earnings_yoy(item["url"])

        rev = yoy["revenue_yoy"]
        op = yoy["op_profit_yoy"]

        if rev is None and op is None:
            continue

        enriched_count += 1
        detail_parts = []
        if rev is not None:
            detail_parts.append(f"매출액 YoY {rev:+.1f}%")
        if op is not None:
            detail_parts.append(f"영업이익 YoY {op:+.1f}%")
        item["detail"] = " | ".join(detail_parts)

        # 점수 재산정
        if (rev is not None and rev >= 30) or (op is not None and op >= 30):
            item["impact_score"] = 30
            item["sentiment"] = "positive"
        elif (rev is not None and rev < 0) or (op is not None and op < 0):
            item["impact_score"] = -10
            item["sentiment"] = "negative"

        if (i + 1) % 10 == 0:
            logger.info(f"  {i + 1}/{len(targets)}건 처리 완료")
        time.sleep(1)  # Rate limit

    logger.info(f"실적 상세 분석 완료: {enriched_count}/{len(targets)}건 보강")
    return enriched_count


def _get_all_doc_nos(viewer_url: str) -> list[tuple[str, str]]:
    """KIND viewer 페이지에서 모든 문서 옵션을 추출합니다.

    Returns: [(docNo, title), ...] — 첫 항목이 원본, 마지막이 최신
    """
    try:
        resp = requests.get(viewer_url, headers=_HTTP_HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        select = soup.find("select", id="mainDoc")
        if select:
            results = []
            for opt in select.find_all("option"):
                val = opt.get("value", "")
                text = opt.get_text(strip=True)
                if "|" in val:
                    results.append((val.split("|")[0], text))
            return results
    except Exception as e:
        logger.debug(f"문서 옵션 추출 실패: {e}")
    return []


def _get_htm_content(doc_no: str) -> str:
    """docNo로부터 실제 HTM 문서 내용을 가져옵니다."""
    htm_url = _get_htm_url(doc_no)
    if not htm_url:
        return ""
    time.sleep(0.5)
    try:
        resp = requests.get(htm_url, headers=_HTTP_HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding or "euc-kr"
        return resp.text
    except Exception as e:
        logger.debug(f"HTM 문서 로드 실패: {e}")
    return ""


def _parse_contract_fields(html: str) -> dict:
    """계약 공시 HTM에서 계약금액, 매출액대비%, 종료일을 추출합니다.

    Returns: {
        "contract_amount": int|None,  # 계약금액 총액 or 해지금액
        "revenue": int|None,          # 최근 매출액
        "revenue_pct": float|None,    # 매출액 대비 (%)
        "end_date": str|None,         # 계약 종료일 (YYYY-MM-DD)
        "is_cancel": bool,            # 해지 공시 여부
    }
    """
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "contract_amount": None, "revenue": None,
        "revenue_pct": None, "end_date": None, "is_cancel": False,
    }

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if not cells:
                continue
            joined = " ".join(cells)

            # 해지금액
            if "해지금액" in joined:
                result["is_cancel"] = True
                for c in cells[1:]:
                    val = c.replace(",", "").replace("-", "").strip()
                    if val.isdigit() and int(val) > 0:
                        result["contract_amount"] = int(val)
                        break

            # 계약금액 총액(원)
            elif "계약금액" in joined and "총액" in joined:
                for c in cells[1:]:
                    val = c.replace(",", "").replace("-", "").strip()
                    if val.isdigit() and int(val) > 0:
                        result["contract_amount"] = int(val)
                        break

            # 최근 매출액(원) / 최근매출액(원)
            elif re.search(r"최근\s*매출액", joined) and "상대" not in joined:
                for c in cells[1:]:
                    val = c.replace(",", "").replace("-", "").strip()
                    if val.isdigit() and int(val) > 0:
                        result["revenue"] = int(val)
                        break

            # 매출액 대비(%) / 매출액대비(%)
            elif re.search(r"매출액\s*대비", joined):
                for c in cells[1:]:
                    c_clean = c.replace(",", "").strip()
                    m = re.search(r"([\d.]+)", c_clean)
                    if m:
                        result["revenue_pct"] = float(m.group(1))
                        break

            # 종료일
            elif "종료일" in joined:
                for c in cells:
                    if re.match(r"\d{4}-\d{2}-\d{2}", c):
                        result["end_date"] = c.strip()

    return result


def enrich_contract_scores(disclosures: list[dict]) -> int:
    """계약 공시의 상세 페이지를 파싱하여 점수를 재산정합니다.

    Rules:
    - 해지 계약 → score -30
    - 공급계약 매출액대비 >= 30% → score +50
    - 공급계약 매출액대비 >= 20% → score +30
    - 공급계약 매출액대비 >= 10% → score +10
    - (정정) 계약금액이 원본 대비 20%↑ → score +30
    - (정정) 종료일이 원본 대비 1개월+ 앞당겨짐 → score +10

    Returns: 보강된 공시 건수
    """
    targets = [d for d in disclosures
               if d.get("event_class") in CONTRACT_CLASSES and d.get("url")]
    if not targets:
        return 0

    logger.info(f"계약 공시 {len(targets)}건 상세 분석 시작...")
    enriched_count = 0

    for i, item in enumerate(targets):
        title = item.get("title", "")
        is_cancel = "해지" in title
        is_correction = "정정" in title and not is_cancel

        if is_correction:
            # 정정 공시: 원본 vs 최신 비교
            score = _score_correction_contract(item)
        else:
            # 일반 공급계약 또는 해지
            score = _score_normal_contract(item, is_cancel)

        if score is not None:
            enriched_count += 1

        if (i + 1) % 5 == 0:
            logger.info(f"  계약 {i + 1}/{len(targets)}건 처리 완료")
        time.sleep(1)

    logger.info(f"계약 상세 분석 완료: {enriched_count}/{len(targets)}건 보강")
    return enriched_count


def _score_normal_contract(item: dict, is_cancel: bool) -> float | None:
    """일반 계약/해지 공시의 점수를 산정합니다."""
    docs = _get_all_doc_nos(item["url"])
    if not docs:
        return None
    time.sleep(0.5)

    doc_no = docs[-1][0]  # 최신 문서
    html = _get_htm_content(doc_no)
    if not html:
        return None

    fields = _parse_contract_fields(html)

    if is_cancel or fields["is_cancel"]:
        item["impact_score"] = -30
        item["sentiment"] = "negative"
        pct = fields.get("revenue_pct")
        detail = f"계약해지"
        if pct:
            detail += f" (매출대비 {pct:.1f}%)"
        if fields.get("contract_amount"):
            detail += f" | 해지금액 {fields['contract_amount']:,}원"
        item["detail"] = detail
        return -30

    # 일반 공급계약 — 매출액대비(%) 기준 점수
    pct = fields.get("revenue_pct")
    if pct is None:
        return None

    detail_parts = [f"매출대비 {pct:.1f}%"]
    if fields.get("contract_amount"):
        detail_parts.append(f"계약금액 {fields['contract_amount']:,}원")

    if pct >= 30:
        item["impact_score"] = 50
        item["sentiment"] = "positive"
    elif pct >= 20:
        item["impact_score"] = 30
        item["sentiment"] = "positive"
    elif pct >= 10:
        item["impact_score"] = 10
        item["sentiment"] = "positive"

    item["detail"] = " | ".join(detail_parts)
    return item["impact_score"]


def _score_correction_contract(item: dict) -> float | None:
    """정정 계약 공시의 점수를 산정합니다 (직전 버전 vs 최신 비교)."""
    docs = _get_all_doc_nos(item["url"])
    if len(docs) < 2:
        # 직전 버전이 없으면 일반 공급계약으로 처리
        return _score_normal_contract(item, is_cancel=False)
    time.sleep(0.5)

    # 직전 버전 (docs[-2]) 파싱 — 이번 정정 직전의 상태
    prev_html = _get_htm_content(docs[-2][0])
    if not prev_html:
        return _score_normal_contract(item, is_cancel=False)
    prev = _parse_contract_fields(prev_html)
    time.sleep(0.5)

    # 최신 (마지막) 파싱
    latest_html = _get_htm_content(docs[-1][0])
    if not latest_html:
        return None
    latest = _parse_contract_fields(latest_html)

    detail_parts = []
    score_bonus = 0

    # 1) 매출액대비 기준 기본 점수 (최신 기준)
    pct = latest.get("revenue_pct")
    if pct is not None:
        detail_parts.append(f"매출대비 {pct:.1f}%")
        if pct >= 30:
            item["impact_score"] = 50
        elif pct >= 20:
            item["impact_score"] = 30
        elif pct >= 10:
            item["impact_score"] = 10

    # 2) 계약금액 변동 비교 (직전 vs 최신)
    if prev["contract_amount"] and latest["contract_amount"] and prev["contract_amount"] > 0:
        change_pct = (latest["contract_amount"] - prev["contract_amount"]) / prev["contract_amount"] * 100
        detail_parts.append(f"계약금액 {change_pct:+.1f}%")
        if change_pct >= 20:
            score_bonus += 30
            detail_parts.append("(금액 20%↑)")

    # 3) 종료일 변동 비교 — 앞당겨진 경우만 (직전 vs 최신)
    if prev["end_date"] and latest["end_date"]:
        try:
            prev_dt = datetime.strptime(prev["end_date"], "%Y-%m-%d")
            latest_dt = datetime.strptime(latest["end_date"], "%Y-%m-%d")
            diff_days = (prev_dt - latest_dt).days  # 양수 = 앞당겨짐
            if diff_days >= 30:
                score_bonus += 10
                detail_parts.append(f"종료일 {diff_days}일 앞당김")
            elif diff_days <= -30:
                score_bonus -= 5
                detail_parts.append(f"종료일 {-diff_days}일 연장(-5)")
            elif diff_days < 0:
                detail_parts.append(f"종료일 {-diff_days}일 연장")
        except ValueError:
            pass

    if score_bonus != 0:
        item["impact_score"] = item.get("impact_score", 3.5) + score_bonus
        if score_bonus > 0:
            item["sentiment"] = "positive"

    if detail_parts:
        item["detail"] = " | ".join(detail_parts)
        return item["impact_score"]

    return None


def classify_event(title: str) -> dict:
    """공시 제목에서 이벤트를 분류하고 감성/점수를 반환합니다."""
    # Risk-On 키워드 매칭 (우선)
    for keyword, meta in RISK_ON_KEYWORDS.items():
        if keyword in title:
            avg_score = round((meta["score"][0] + meta["score"][1]) / 2, 1)
            return {
                "event_class": meta["event_class"],
                "sentiment": "positive",
                "impact_score": avg_score,
                "badge": meta["badge"],
            }

    # Risk-Off 키워드 매칭
    for keyword, meta in RISK_OFF_KEYWORDS.items():
        if keyword in title:
            avg_score = round((meta["score"][0] + meta["score"][1]) / 2, 1)
            return {
                "event_class": meta["event_class"],
                "sentiment": "negative",
                "impact_score": avg_score,
                "badge": meta["badge"],
            }

    # Neutral 키워드 매칭
    for keyword, meta in NEUTRAL_KEYWORDS.items():
        if keyword in title:
            return {
                "event_class": meta["event_class"],
                "sentiment": "neutral",
                "impact_score": 0,
                "badge": meta["badge"],
            }

    # 미분류
    return {
        "event_class": "unclassified",
        "sentiment": "neutral",
        "impact_score": 0,
        "badge": "기타",
    }


def detect_cluster_alerts(disclosures: list[dict]) -> list[str]:
    """업종/이벤트별 클러스터 패턴을 감지합니다.

    같은 이벤트 유형이 3건 이상 동시에 발생하면 알림을 생성합니다.
    """
    alerts = []

    # 이벤트 클래스별 회사 목록
    event_companies: dict[str, list[str]] = {}
    for d in disclosures:
        ec = d.get("event_class", "")
        if ec in ("unclassified", "insider_report", "major_holding", "simple_investment"):
            continue
        event_companies.setdefault(ec, []).append(d["company"])

    event_labels = {
        "cb_issuance": "CB 발행",
        "bw_issuance": "BW 발행",
        "rights_offering": "유상증자",
        "supply_contract": "공급계약",
        "buyback": "자사주매입",
        "dividend": "배당",
        "lawsuit": "소송",
        "suspension": "거래정지",
        "earnings_surprise": "실적공시",
    }

    for event_class, companies in event_companies.items():
        if len(companies) >= 3:
            label = event_labels.get(event_class, event_class)
            alerts.append(f"{len(companies)}개사 동시 {label}")
        elif len(companies) >= 2:
            label = event_labels.get(event_class, event_class)
            # 부정적 이벤트는 2건부터 알림
            if event_class in ("cb_issuance", "bw_issuance", "rights_offering", "suspension"):
                alerts.append(f"{len(companies)}개사 동시 {label}")

    return alerts


def get_sentiment_label(score: float) -> str:
    """일일 종합 점수에서 감성 라벨을 반환합니다."""
    if score >= 5:
        return "매우 긍정"
    elif score >= 2:
        return "긍정"
    elif score >= -2:
        return "중립"
    elif score >= -5:
        return "주의"
    else:
        return "경계"


def analyze(target_date: str) -> dict:
    """공시 데이터를 분석하여 프론트엔드용 JSON을 생성합니다."""
    input_file = DATA_DIR / f"{target_date}.json"

    if not input_file.exists():
        logger.error(f"입력 파일 없음: {input_file}")
        logger.info("먼저 collect_disclosures.py를 실행하세요.")
        return {}

    with open(input_file, "r", encoding="utf-8") as f:
        raw_disclosures = json.load(f)

    logger.info(f"총 {len(raw_disclosures)}건 분석 시작")

    # 분류 및 점수 산출
    processed = []
    total_score = 0
    sentiment_counts = Counter()
    dilution_events = 0
    buyback_events = 0

    for item in raw_disclosures:
        classification = classify_event(item["title"])

        enriched = {
            **item,
            **classification,
            "detail": "",  # 상세 정보 (금액 등은 향후 상세 페이지 파싱으로 확보)
        }
        processed.append(enriched)

        total_score += classification["impact_score"]
        sentiment_counts[classification["sentiment"]] += 1

        if classification["event_class"] in ("cb_issuance", "bw_issuance", "rights_offering"):
            dilution_events += 1
        elif classification["event_class"] in ("buyback", "buyback_cancel", "dividend"):
            buyback_events += 1

    # 실적 공시 상세 분석 (KIND 상세 페이지에서 YoY 증감률 파싱)
    enrich_earnings_scores(processed)

    # 계약 공시 상세 분석 (KIND 상세 페이지에서 계약금액/매출대비/정정 비교)
    enrich_contract_scores(processed)

    # 점수/감성 재집계 (상세 분석으로 변경된 점수 반영)
    total_score = sum(d["impact_score"] for d in processed)
    sentiment_counts = Counter(d["sentiment"] for d in processed)

    # 클러스터 알림
    cluster_alerts = detect_cluster_alerts(processed)

    # 일일 종합 점수 (평균)
    daily_score = round(total_score / max(len(processed), 1), 2)

    result = {
        "date": target_date,
        "summary": {
            "total": len(processed),
            "risk_on": sentiment_counts.get("positive", 0),
            "risk_off": sentiment_counts.get("negative", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "sentiment_label": get_sentiment_label(daily_score),
            "daily_score": daily_score,
            "dilution_count": dilution_events,
            "buyback_count": buyback_events,
            "cluster_alerts": cluster_alerts,
        },
        "disclosures": processed,
    }

    logger.info(f"분석 결과: Risk-On {sentiment_counts['positive']}건, "
                f"Risk-Off {sentiment_counts['negative']}건, "
                f"Neutral {sentiment_counts['neutral']}건")
    logger.info(f"일일 점수: {daily_score} ({result['summary']['sentiment_label']})")

    if cluster_alerts:
        for alert in cluster_alerts:
            logger.info(f"클러스터 알림: {alert}")

    return result


def save_result(result: dict, target_date: str) -> Path:
    """분석 결과를 저장합니다."""
    # 대시보드용 (최신 데이터)
    latest_file = DASHBOARD_DATA_DIR / "latest_disclosures.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 아카이브용 (날짜별)
    archive_file = DATA_DIR / f"processed_{target_date}.json"
    with open(archive_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return latest_file


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()

    logger.info(f"=== 공시 분석 시작 (날짜: {target}) ===")

    result = analyze(target)
    if not result:
        sys.exit(1)

    output_file = save_result(result, target)
    logger.info(f"=== 분석 완료 → {output_file} ===")


if __name__ == "__main__":
    main()
