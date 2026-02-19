"""
News Intelligence - AI Analysis Endpoints
GET  /api/v1/news-intel-ai/models        - 사용 가능한 AI 모델 목록
POST /api/v1/news-intel-ai/analyze       - AI 분석 실행 (모델 선택)
POST /api/v1/news-intel-ai/manual        - 자동 요약 (규칙 기반, AI 없이)
GET  /api/v1/news-intel-ai/prefill       - 편집용 프리필 데이터 조회
POST /api/v1/news-intel-ai/manual-save   - 수동 리서치 브리핑 저장
"""
import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Query, Body

_scripts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _scripts_root not in sys.path:
    sys.path.insert(0, _scripts_root)

router = APIRouter(prefix="/api/v1/news-intel-ai", tags=["News Intelligence AI"])


@router.get("/models")
async def get_available_models():
    """사용 가능한 AI 모델 목록 조회"""
    from scripts.news_monitor.config import AVAILABLE_MODELS
    return {
        "models": [
            {"id": mid, **info}
            for mid, info in AVAILABLE_MODELS.items()
        ],
        "default": "claude-sonnet-4-5-20250929",
    }


@router.post("/analyze")
async def run_analysis(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    model: str = Query(None, description="AI 모델 ID"),
):
    """AI 내러티브 분석 실행 (모델 선택 가능). US 지수 + 섹터 + 뉴스 통합 분석."""
    try:
        from scripts.news_monitor.narrative_analyzer import analyze_today_news
        from datetime import timedelta

        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        target_date = date or kst_now.strftime("%Y-%m-%d")

        result = await asyncio.to_thread(analyze_today_news, target_date, model)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail={"detail": "분석 불가 (기사 없음 또는 API 키 미설정)", "error_code": "ANALYSIS_UNAVAILABLE"},
            )

        return {
            "status": "ok",
            "date": target_date,
            "model": model or "default",
            "key_issues": len(result.get("key_issues", [])),
            "sentiment": result.get("sentiment_label", "unknown"),
            "has_market_summary": bool(result.get("market_summary")),
            "has_timeline": bool(result.get("sentiment_timeline")),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"분석 실패: {str(e)}", "error_code": "ANALYSIS_ERROR"},
        )


@router.post("/manual")
async def save_manual_briefing(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
):
    """
    수동 브리핑 생성: 수집된 기사 헤드라인 + 섹터 퍼포먼스 + US 지수 데이터를
    기반으로 규칙 기반 브리핑을 자동 생성하여 DB에 저장.
    AI API 없이 작동.
    """
    try:
        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        target_date = date or kst_now.strftime("%Y-%m-%d")

        result = await asyncio.to_thread(_build_manual_briefing, target_date)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"수동 브리핑 생성 실패: {str(e)}", "error_code": "MANUAL_BRIEFING_ERROR"},
        )


@router.get("/autofill")
async def get_autofill_data(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
):
    """자동 채우기: 규칙 기반으로 브리핑 데이터 생성 (DB 저장 안함). 모달 편집용."""
    try:
        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        target_date = date or kst_now.strftime("%Y-%m-%d")

        data = await asyncio.to_thread(_generate_auto_briefing, target_date)
        timeline = data.get("sentiment_timeline", [])
        idx_names = [i.get("name", "?") for i in data.get("index_data", {}).get("indices", [])]
        print(f"  [AUTOFILL] indices={idx_names}, timeline={len(timeline)}구간")
        # 모달 폼에 맞는 형식으로 변환
        return {
            "source": "autofill",
            "generated_by": "manual-auto",
            "date": target_date,
            "key_issues": data["key_issues"],
            "narrative": data["narrative"],
            "market_summary": data["index_data"].get("market_summary", ""),
            "sentiment_timeline": timeline,
            "sentiment_score": data["sentiment_score"],
            "sentiment_label": data["sentiment_label"],
            "sector_impact": data["sector_impact"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"자동 채우기 실패: {str(e)}", "error_code": "AUTOFILL_ERROR"},
        )


@router.get("/prefill")
async def get_prefill_data(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
):
    """편집 모달용 프리필 데이터: 기존 DB 데이터 또는 자동 생성 초안 반환."""
    try:
        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        target_date = date or kst_now.strftime("%Y-%m-%d")

        result = await asyncio.to_thread(_get_prefill, target_date)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"프리필 실패: {str(e)}", "error_code": "PREFILL_ERROR"},
        )


@router.post("/manual-save")
async def save_manual_research(
    date: str = Query(None, description="날짜 (YYYY-MM-DD)"),
    payload: dict = Body(..., description="수동 리서치 브리핑 전체 내용"),
):
    """수동 리서치 브리핑 저장 (manual-research 방식)."""
    try:
        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        target_date = date or kst_now.strftime("%Y-%m-%d")

        result = await asyncio.to_thread(_save_manual_research, target_date, payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": f"저장 실패: {str(e)}", "error_code": "MANUAL_SAVE_ERROR"},
        )


def _get_prefill(target_date: str) -> dict:
    """기존 DB 데이터가 있으면 반환, 없으면 자동 생성 초안."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.models.news_article import MarketNarrative

    DB_PATH = os.path.join(_scripts_root, 'backend', 'stock_research.db')
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Session = sessionmaker(bind=engine)
    db = Session()

    existing = db.query(MarketNarrative).filter_by(date=target_date).first()
    db.close()

    if existing:
        idx_data = existing.index_data or {}
        return {
            "source": "db",
            "generated_by": existing.generated_by or "",
            "date": target_date,
            "key_issues": existing.key_issues or [],
            "narrative": existing.narrative or "",
            "market_summary": idx_data.get("market_summary", ""),
            "sentiment_timeline": idx_data.get("sentiment_timeline", []),
            "sentiment_score": existing.sentiment_score or 0,
            "sentiment_label": existing.sentiment_label or "중립",
        }

    # DB에 없으면 빈 템플릿 반환
    return {
        "source": "empty",
        "generated_by": "",
        "date": target_date,
        "key_issues": [],
        "narrative": "",
        "market_summary": "",
        "sentiment_timeline": [],
        "sentiment_score": 0,
        "sentiment_label": "중립",
    }


def _save_manual_research(target_date: str, payload: dict) -> dict:
    """수동 리서치 내용을 DB에 저장 (manual-research 방식)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.models.news_article import MarketNarrative

    DB_PATH = os.path.join(_scripts_root, 'backend', 'stock_research.db')
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Session = sessionmaker(bind=engine)
    db = Session()

    key_issues = payload.get("key_issues", [])
    narrative_text = payload.get("narrative", "")
    market_summary = payload.get("market_summary", "")
    sentiment_timeline = payload.get("sentiment_timeline", [])
    sentiment_score = float(payload.get("sentiment_score", 0))
    sentiment_label = payload.get("sentiment_label", "중립")
    sector_impact = payload.get("sector_impact", None)

    existing = db.query(MarketNarrative).filter_by(date=target_date).first()
    idx_data = {}
    if existing and existing.index_data:
        idx_data = dict(existing.index_data)
    idx_data["market_summary"] = market_summary
    if sentiment_timeline:
        idx_data["sentiment_timeline"] = sentiment_timeline

    if existing:
        existing.key_issues = key_issues
        existing.narrative = narrative_text
        existing.sentiment_score = round(sentiment_score, 2)
        existing.sentiment_label = sentiment_label
        existing.index_data = idx_data
        existing.generated_by = "manual-research"
        existing.model_used = "manual-research"
        if sector_impact is not None:
            existing.sector_impact = sector_impact
    else:
        row = MarketNarrative(
            date=target_date,
            key_issues=key_issues,
            narrative=narrative_text,
            sector_impact=sector_impact or [],
            sentiment_score=round(sentiment_score, 2),
            sentiment_label=sentiment_label,
            article_count=0,
            index_data=idx_data,
            generated_by="manual-research",
        )
        db.add(row)

    db.commit()
    db.close()

    return {
        "status": "ok",
        "date": target_date,
        "key_issues": len(key_issues),
        "narrative_len": len(narrative_text),
        "market_summary_len": len(market_summary),
        "timeline_entries": len(sentiment_timeline),
        "sentiment": sentiment_label,
        "model": "manual-research",
    }


def _generate_auto_briefing(target_date: str) -> dict:
    """수집된 데이터 기반으로 구조화된 브리핑 데이터 생성 (DB 저장 안함)."""
    from sqlalchemy import create_engine, or_, desc
    from sqlalchemy.orm import sessionmaker
    from backend.app.models.news_article import (
        NewsArticle, MarketNarrative, SectorPerformance, IndustryPerformance
    )
    from scripts.news_monitor.index_fetch import fetch_all_indices, summarize_index_data
    from scripts.news_monitor.finviz_fetch import fetch_sector_performance

    DB_PATH = os.path.join(_scripts_root, 'backend', 'stock_research.db')
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Session = sessionmaker(bind=engine)
    db = Session()

    prev_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

    # 1) 기사 수집
    articles = (
        db.query(NewsArticle)
        .filter(
            NewsArticle.source != "DEMO",
            or_(
                NewsArticle.published_at.between(f"{target_date} 00:00:00", f"{target_date} 23:59:59"),
                NewsArticle.fetched_at.between(f"{target_date} 00:00:00", f"{target_date} 23:59:59"),
                NewsArticle.fetched_at.between(f"{prev_date} 15:00:00", f"{target_date} 23:59:59"),
            ),
        )
        .order_by(desc(NewsArticle.fetched_at))
        .limit(500)
        .all()
    )
    article_count = len(articles)

    # 2) 섹터 퍼포먼스
    sector_data = fetch_sector_performance() or []

    # 3) US 지수 데이터 (라이브 → DB 캐시 fallback)
    raw_indices = fetch_all_indices()
    index_summaries = summarize_index_data(raw_indices)

    cached_timeline = []
    if not index_summaries:
        # Yahoo Finance 429 등 실패 시 DB 캐시된 지수 데이터 사용
        existing = db.query(MarketNarrative).filter_by(date=target_date).first()
        if existing and existing.index_data:
            cached = existing.index_data.get("indices", [])
            if cached:
                index_summaries = cached
                print(f"  [AUTOFILL] Live index fetch failed, using DB cache ({len(cached)} indices)")
            cached_timeline = existing.index_data.get("sentiment_timeline", [])

    db.close()

    # 4) 섹터 기반 sector_impact 생성 (헤드라인에서 변동이유 추출)
    headline_reasons = _match_sector_reasons(articles)
    sector_impact = []
    for s in sorted(sector_data, key=lambda x: abs(x["change_pct"]), reverse=True):
        if s["change_pct"] > 0.3:
            direction = "bullish"
        elif s["change_pct"] < -0.3:
            direction = "bearish"
        else:
            direction = "neutral"
        reason = headline_reasons.get(s["name"], "")
        if not reason:
            reason = f"관련 헤드라인 미확인 (Finviz {s['change_pct']:+.2f}%)"
        sector_impact.append({
            "sector": s["name"],
            "direction": direction,
            "confidence": min(abs(s["change_pct"]) / 2.0, 1.0),
            "change_pct": s["change_pct"],
            "reason": reason,
        })

    # 5) 핵심 이슈, 내러티브, 시장 요약, 센티먼트 타임라인
    key_issues = _extract_key_issues(articles, sector_data, index_summaries)
    narrative = _generate_narrative(target_date, index_summaries, sector_impact)
    market_summary = _generate_market_summary(index_summaries, sector_impact)
    sentiment_timeline = _generate_sentiment_timeline(index_summaries, sector_impact, articles)
    if not sentiment_timeline and cached_timeline:
        sentiment_timeline = cached_timeline
        print(f"  [AUTOFILL] Using cached sentiment_timeline ({len(cached_timeline)} entries)")

    avg_change = sum(s["change_pct"] for s in sector_data) / max(len(sector_data), 1)
    if avg_change > 0.5:
        sentiment_label = "낙관"
    elif avg_change > 0.1:
        sentiment_label = "cautious-optimistic"
    elif avg_change > -0.1:
        sentiment_label = "중립"
    elif avg_change > -0.5:
        sentiment_label = "경계"
    else:
        sentiment_label = "공포"
    sentiment_score = max(-1.0, min(1.0, avg_change / 2.0))

    return {
        "date": target_date,
        "key_issues": key_issues,
        "narrative": narrative,
        "sector_impact": sector_impact,
        "sentiment_score": round(sentiment_score, 2),
        "sentiment_label": sentiment_label,
        "article_count": article_count,
        "sentiment_timeline": sentiment_timeline,
        "index_data": {"indices": index_summaries, "market_summary": market_summary},
    }


def _build_manual_briefing(target_date: str) -> dict:
    """자동 브리핑 생성 + DB 저장."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.models.news_article import MarketNarrative

    data = _generate_auto_briefing(target_date)

    DB_PATH = os.path.join(_scripts_root, 'backend', 'stock_research.db')
    engine = create_engine(f'sqlite:///{DB_PATH}')
    Session = sessionmaker(bind=engine)
    db = Session()

    existing = db.query(MarketNarrative).filter_by(date=target_date).first()
    idx_data = data["index_data"]

    if existing:
        existing.key_issues = data["key_issues"]
        existing.narrative = data["narrative"]
        existing.sector_impact = data["sector_impact"]
        existing.sentiment_score = data["sentiment_score"]
        existing.sentiment_label = data["sentiment_label"]
        existing.article_count = data["article_count"]
        existing.index_data = idx_data
        existing.generated_by = "manual-auto"
        existing.model_used = "manual-auto"
    else:
        row = MarketNarrative(
            date=target_date,
            key_issues=data["key_issues"],
            narrative=data["narrative"],
            sector_impact=data["sector_impact"],
            sentiment_score=data["sentiment_score"],
            sentiment_label=data["sentiment_label"],
            article_count=data["article_count"],
            index_data=idx_data,
            generated_by="manual-auto",
        )
        db.add(row)

    db.commit()
    db.close()

    return {
        "status": "ok",
        "date": target_date,
        "key_issues": len(data["key_issues"]),
        "sectors": len(data["sector_impact"]),
        "indices": len(idx_data.get("indices", [])),
        "article_count": data["article_count"],
        "sentiment": data["sentiment_label"],
        "model": "manual-auto",
    }


def _match_sector_reasons(articles) -> dict:
    """수집된 기사 헤드라인에서 섹터별 변동 이유를 추출하여 한 줄 reason으로 반환."""
    SECTOR_KEYWORDS = {
        "Energy": ["energy", "oil", "crude", "opec", "natural gas", "lng", "petroleum",
                    "exxon", "chevron", "drilling", "pipeline", "wti", "brent"],
        "Basic Materials": ["material", "mining", "steel", "copper", "gold", "silver",
                            "lithium", "chemical", "rare earth", "aluminum", "iron ore"],
        "Technology": ["tech", "ai ", " ai,", "semiconductor", "chip", "nvidia", "apple",
                       "microsoft", "google", "meta", "software", "cloud", "tsmc", "intel",
                       "broadcom", "amd", "asml"],
        "Consumer Cyclical": ["consumer", "retail", "amazon", "tesla", "auto", "ev ",
                              "housing", "spending", "luxury", "nike", "home depot"],
        "Financial": ["bank", "financial", "jpmorgan", "goldman", "rate", "lending",
                      "credit", "insurance", "wells fargo", "morgan stanley", "yield"],
        "Communication Services": ["communication", "media", "streaming", "disney",
                                    "netflix", "social media", "alphabet", "spotify"],
        "Healthcare": ["health", "pharma", "biotech", "drug", "fda", "medical",
                       "hospital", "vaccine", "eli lilly", "pfizer", "novo nordisk"],
        "Industrials": ["industrial", "manufacturing", "boeing", "caterpillar",
                        "infrastructure", "production", "defense", "lockheed", "ge "],
        "Consumer Defensive": ["walmart", "costco", "food", "staple", "grocery",
                               "procter", "coca-cola", "pepsi", "tobacco", "defensive"],
        "Real Estate": ["real estate", "reit", "housing", "mortgage", "property",
                        "commercial real", "office space"],
        "Utilities": ["utility", "utilities", "electric", "power grid", "renewable",
                      "solar", "wind energy", "nuclear", "nextera"],
    }

    # 헤드라인 수집 (최대 300건, 내부 수집 기사 우선)
    headlines = []
    for a in articles[:300]:
        title = a.title or ""
        if title.strip():
            headlines.append(title)

    sector_reasons = {}
    for sector_name, keywords in SECTOR_KEYWORDS.items():
        matched_headlines = []
        for h in headlines:
            h_lower = h.lower()
            for kw in keywords:
                if kw in h_lower:
                    matched_headlines.append(h)
                    break
            if len(matched_headlines) >= 5:
                break

        if matched_headlines:
            # 가장 관련성 높은 헤드라인 1개 선택 (가장 먼저 매칭된 = 최신)
            best = matched_headlines[0]
            # 카드 한 줄 표시를 위해 길이 제한
            if len(best) > 65:
                best = best[:62] + "..."
            if len(matched_headlines) >= 3:
                sector_reasons[sector_name] = f"{best} +{len(matched_headlines)-1}"
            else:
                sector_reasons[sector_name] = best

    return sector_reasons


def _extract_key_issues(articles, sector_data, index_summaries) -> list:
    """헤드라인 기반 핵심 이슈 추출. 각 이슈에 변동 이유(WHY) 포함."""
    issues = []
    headline_reasons = _match_sector_reasons(articles)

    # 상위 상승/하락 섹터 (WHY 포함)
    if sector_data:
        top_bull = max(sector_data, key=lambda x: x["change_pct"])
        top_bear = min(sector_data, key=lambda x: x["change_pct"])
        if top_bull["change_pct"] > 0.5:
            reason = headline_reasons.get(top_bull['name'], "")
            summary = reason if reason else f"{top_bull['name']} 섹터 매수세 유입"
            issues.append({
                "title": f"{top_bull['name']} 섹터 강세 (+{top_bull['change_pct']:.2f}%)",
                "summary": summary,
                "impact": "high" if top_bull["change_pct"] > 1.0 else "medium",
                "category": "섹터 동향",
            })
        if top_bear["change_pct"] < -0.5:
            reason = headline_reasons.get(top_bear['name'], "")
            summary = reason if reason else f"{top_bear['name']} 섹터 매도 압력"
            issues.append({
                "title": f"{top_bear['name']} 섹터 약세 ({top_bear['change_pct']:.2f}%)",
                "summary": summary,
                "impact": "high" if top_bear["change_pct"] < -1.0 else "medium",
                "category": "섹터 동향",
            })

    # 지수 변동 이슈
    for idx in index_summaries:
        if abs(idx.get("change_pct", 0)) > 0.5:
            direction = "상승" if idx["change_pct"] > 0 else "하락"
            issues.append({
                "title": f"{idx['name']} {direction} ({idx['change_pct']:+.2f}%)",
                "summary": f"{idx.get('full_name', idx['name'])} {idx['current']:,.2f} ({idx['change_pct']:+.2f}%). 장중 {idx.get('day_high', 0):,.2f}~{idx.get('day_low', 0):,.2f}.",
                "impact": "high" if abs(idx["change_pct"]) > 1.0 else "medium",
                "category": "지수",
            })

    # 헤드라인 키워드 기반 테마 이슈 (대표 헤드라인 포함)
    keywords_map = {
        "Fed": "통화정책", "FOMC": "통화정책", "rate cut": "통화정책",
        "rate hike": "통화정책", "minutes": "통화정책",
        "inflation": "인플레이션", "CPI": "인플레이션", "PPI": "인플레이션",
        "earnings": "실적", "revenue": "실적", "guidance": "실적",
        "beat": "실적", "miss": "실적",
        "AI": "기술/AI", "Nvidia": "기술/AI", "semiconductor": "기술/AI",
        "tariff": "무역정책", "trade war": "무역정책", "China": "지정학",
        "oil": "원자재", "gold": "원자재", "crypto": "크립토", "bitcoin": "크립토",
    }
    keyword_hits = {}  # cat -> [(count, representative_headline)]
    for a in articles[:200]:
        title = (a.title or "")
        title_lower = title.lower()
        for kw, cat in keywords_map.items():
            if kw.lower() in title_lower:
                if cat not in keyword_hits:
                    keyword_hits[cat] = {"count": 0, "headline": title}
                keyword_hits[cat]["count"] += 1

    for cat, info in sorted(keyword_hits.items(), key=lambda x: -x[1]["count"])[:3]:
        if info["count"] >= 3:
            headline = info["headline"]
            if len(headline) > 80:
                headline = headline[:77] + "..."
            issues.append({
                "title": f"{cat} 관련 뉴스 다수 ({info['count']}건)",
                "summary": headline,
                "impact": "medium",
                "category": cat,
            })

    return issues[:7]


def _generate_narrative(target_date: str, index_summaries: list, sector_impact: list) -> str:
    """지수 + 섹터 데이터 기반 내러티브 자동 생성 (한글)."""
    parts = [f"{target_date} 미국 증시 요약: "]

    for idx in index_summaries:
        if idx["name"] == "VIX":
            continue
        direction = "상승" if idx.get("change_pct", 0) >= 0 else "하락"
        parts.append(f"{idx['name']} {idx['current']:,.2f}({idx['change_pct']:+.2f}% {direction})")

    vix = next((x for x in index_summaries if x["name"] == "VIX"), None)
    if vix:
        parts.append(f". VIX {vix['current']:.2f}({vix['change_pct']:+.2f}%)")

    parts.append(". ")

    # 섹터 요약
    bulls = [s for s in sector_impact if s["direction"] == "bullish"]
    bears = [s for s in sector_impact if s["direction"] == "bearish"]
    if bulls:
        top = sorted(bulls, key=lambda x: -x["change_pct"])[:3]
        names = ", ".join(f"{s['sector']}({s['change_pct']:+.2f}%)" for s in top)
        parts.append(f"강세 섹터: {names}. ")
    if bears:
        bot = sorted(bears, key=lambda x: x["change_pct"])[:3]
        names = ", ".join(f"{s['sector']}({s['change_pct']:+.2f}%)" for s in bot)
        parts.append(f"약세 섹터: {names}. ")

    return "".join(parts)


def _generate_sentiment_timeline(index_summaries: list, sector_impact: list, articles) -> list:
    """지수 장중 데이터 + 섹터 + 기사 기반 센티먼트 타임라인 자동 생성 (4구간)."""
    # S&P500 기준 장중 흐름 파악
    sp = next((x for x in index_summaries if x["name"] == "S&P500"), None)
    dow = next((x for x in index_summaries if x["name"] == "DOW"), None)
    nasdaq = next((x for x in index_summaries if x["name"] == "NASDAQ"), None)
    ref = sp or dow or nasdaq
    if not ref:
        return []

    points = ref.get("intraday_points", [])
    prev_close = ref.get("previous_close", ref["current"])

    # 헤드라인에서 드라이버 키워드 추출
    headline_texts = [a.title for a in articles[:200] if a.title]
    keyword_drivers = {
        "Fed": [], "FOMC": [], "inflation": [], "CPI": [],
        "earnings": [], "guidance": [], "AI": [], "Nvidia": [],
        "oil": [], "tariff": [], "jobs": [], "GDP": [],
    }
    for h in headline_texts:
        h_lower = h.lower()
        for kw in keyword_drivers:
            if kw.lower() in h_lower:
                keyword_drivers[kw].append(h)

    # 섹터 강세/약세 top3
    bulls = sorted([s for s in sector_impact if s["change_pct"] > 0.3],
                   key=lambda x: -x["change_pct"])[:3]
    bears = sorted([s for s in sector_impact if s["change_pct"] < -0.3],
                   key=lambda x: x["change_pct"])[:3]
    bull_text = ", ".join(f"{s['sector']}({s['change_pct']:+.2f}%)" for s in bulls) if bulls else ""
    bear_text = ", ".join(f"{s['sector']}({s['change_pct']:+.2f}%)" for s in bears) if bears else ""

    # 주요 뉴스 테마 요약 (상위 2개)
    theme_counts = {}
    for kw, hits in keyword_drivers.items():
        if hits:
            theme_counts[kw] = len(hits)
    top_themes = sorted(theme_counts.items(), key=lambda x: -x[1])[:2]
    theme_text = ", ".join(f"{k} 관련 뉴스 {v}건" for k, v in top_themes)

    # 4구간 정의 (고정 템플릿)
    # 가격 기반 market_move 계산
    def _price_at(fraction: float) -> float:
        """intraday_points에서 시간 비율에 해당하는 가격 추정."""
        if not points:
            return ref["current"]
        idx = min(int(fraction * (len(points) - 1)), len(points) - 1)
        return points[idx].get("price", ref["current"])

    mid_morning = _price_at(0.25)
    midday = _price_at(0.5)
    mid_afternoon = _price_at(0.75)
    close_price = ref["current"]

    def _move_text(start, end, name):
        pct = ((end - start) / start * 100) if start else 0
        direction = "+" if pct >= 0 else ""
        return f"{name} {end:,.2f}({direction}{pct:.2f}%)"

    def _sentiment(start, end):
        pct = ((end - start) / start * 100) if start else 0
        if pct > 0.15:
            return "risk-on"
        elif pct < -0.15:
            return "risk-off"
        return "mixed"

    ref_name = ref["name"]
    timeline = []

    # 구간 1: 개장~오전 (09:30-11:00)
    p1_driver_parts = []
    if bull_text:
        p1_driver_parts.append(f"강세 섹터: {bull_text}")
    if theme_text:
        p1_driver_parts.append(theme_text)
    if not p1_driver_parts:
        p1_driver_parts.append("시장 개장, 섹터별 차별화 흐름")

    timeline.append({
        "time_period": "09:30-11:00 ET (개장~오전)",
        "market_move": _move_text(prev_close, mid_morning, ref_name),
        "sentiment_driver": ". ".join(p1_driver_parts[:2]),
        "sentiment": _sentiment(prev_close, mid_morning),
    })

    # 구간 2: 오전~점심 (11:00-13:00)
    p2_parts = []
    if bear_text:
        p2_parts.append(f"약세 섹터 압박: {bear_text}")
    fed_hits = keyword_drivers.get("Fed", []) + keyword_drivers.get("FOMC", [])
    if fed_hits:
        p2_parts.append(f"Fed/FOMC 관련 뉴스 {len(fed_hits)}건")
    if not p2_parts:
        p2_parts.append("장중 보합권 횡보, 방향성 탐색")

    timeline.append({
        "time_period": "11:00-13:00 ET (오전~점심)",
        "market_move": _move_text(mid_morning, midday, ref_name),
        "sentiment_driver": ". ".join(p2_parts[:2]),
        "sentiment": _sentiment(mid_morning, midday),
    })

    # 구간 3: 오후 (13:00-15:00)
    p3_parts = []
    earnings_hits = keyword_drivers.get("earnings", []) + keyword_drivers.get("guidance", [])
    if earnings_hits:
        best = earnings_hits[0][:60]
        p3_parts.append(f"실적 뉴스: {best}")
    ai_hits = keyword_drivers.get("AI", []) + keyword_drivers.get("Nvidia", [])
    if ai_hits:
        p3_parts.append(f"AI/반도체 뉴스 {len(ai_hits)}건")
    if not p3_parts:
        p3_parts.append("오후 트레이딩, 포지션 조정 구간")

    timeline.append({
        "time_period": "13:00-15:00 ET (오후)",
        "market_move": _move_text(midday, mid_afternoon, ref_name),
        "sentiment_driver": ". ".join(p3_parts[:2]),
        "sentiment": _sentiment(midday, mid_afternoon),
    })

    # 구간 4: 마감 (15:00-16:00)
    p4_parts = []
    overall_pct = ((close_price - prev_close) / prev_close * 100) if prev_close else 0
    if overall_pct > 0.3:
        p4_parts.append(f"장 마감 양봉. 전일 대비 {overall_pct:+.2f}%")
    elif overall_pct < -0.3:
        p4_parts.append(f"장 마감 음봉. 전일 대비 {overall_pct:+.2f}%")
    else:
        p4_parts.append(f"보합 마감. 전일 대비 {overall_pct:+.2f}%")
    if bull_text and bear_text:
        p4_parts.append(f"상승 주도: {bulls[0]['sector']}, 하락 주도: {bears[0]['sector']}")

    timeline.append({
        "time_period": "15:00-16:00 ET (마감)",
        "market_move": _move_text(mid_afternoon, close_price, ref_name),
        "sentiment_driver": ". ".join(p4_parts[:2]),
        "sentiment": _sentiment(mid_afternoon, close_price),
    })

    return timeline


def _generate_market_summary(index_summaries: list, sector_impact: list) -> str:
    """지수 장중 데이터 기반 시장 요약 (한글)."""
    parts = []
    for idx in index_summaries:
        if idx["name"] == "VIX":
            continue
        high = idx.get("day_high", 0)
        low = idx.get("day_low", 0)
        parts.append(
            f"{idx['name']}: 종가 {idx['current']:,.2f}({idx['change_pct']:+.2f}%), "
            f"장중 고점 {high:,.2f}, 저점 {low:,.2f}"
        )

    bulls = sorted([s for s in sector_impact if s["change_pct"] > 0], key=lambda x: -x["change_pct"])[:3]
    bears = sorted([s for s in sector_impact if s["change_pct"] < 0], key=lambda x: x["change_pct"])[:3]

    if bulls:
        parts.append("상승 주도: " + ", ".join(f"{s['sector']}({s['change_pct']:+.2f}%)" for s in bulls))
    if bears:
        parts.append("하락 주도: " + ", ".join(f"{s['sector']}({s['change_pct']:+.2f}%)" for s in bears))

    return ". ".join(parts) + "."
