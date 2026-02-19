"""
News Intelligence Monitor - AI Narrative Analyzer v2
Claude API로 당일 뉴스 + 실제 섹터 퍼포먼스 + US 지수 장중 데이터 분석
→ 핵심이슈/내러티브/섹터 영향도 + 시점별 투심 이슈 연결
"""
import sys
import os
import json
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from scripts.news_monitor.config import (
    DB_PATH, ANTHROPIC_API_KEY, ANTHROPIC_MODEL, MAX_ARTICLES_FOR_ANALYSIS,
    AVAILABLE_MODELS,
)

sys.stdout.reconfigure(encoding='utf-8')

ANALYSIS_PROMPT = """You are a senior financial market analyst. Analyze today's news headlines together with ACTUAL US index movements and sector performance data. Provide investment intelligence in Korean.

## Today's News ({article_count} articles, {date})

{articles_text}

## US Market Index Intraday Data

{index_data_text}

## Actual Sector Performance (1-Day Change from Finviz)

{sector_performance_text}

## Required Output (respond ONLY with valid JSON, no markdown fences):
{{
  "market_summary": "DOW/NASDAQ/S&P500 당일 시세 변화를 시간대별로 서술 (한국어, 2~3문단). 장 초반→장중→장 마감 흐름을 설명하고, 각 시점의 주요 가격 변동을 구체적 수치와 함께 기술.",
  "sentiment_timeline": [
    {{
      "time_period": "장 초반 (9:30-11:00 ET)",
      "market_move": "DOW +0.3%, NASDAQ +0.5% 등 구체적 수치",
      "sentiment_driver": "해당 시점의 투심 이슈/촉매제 (한국어)",
      "sentiment": "risk-on|risk-off|mixed"
    }}
  ],
  "key_issues": [
    {{
      "title": "핵심이슈 제목 (한국어)",
      "summary": "2~3문장 요약 (한국어)",
      "impact": "high|medium|low",
      "category": "macro|sector|geopolitical|earnings|crypto",
      "affected_indices": ["DOW", "NASDAQ", "S&P500"],
      "estimated_impact_pct": "해당 이슈로 인한 추정 지수 영향 (예: NASDAQ +0.3%)"
    }}
  ],
  "narrative": "오늘의 시장 내러티브 2~3문단 (한국어, 투자 심리 관점). 지수 움직임과 뉴스 이벤트를 시간순으로 연결하여 서술.",
  "sector_impact": [
    {{
      "sector": "Technology|Healthcare|Financials|Energy|Consumer Cyclical|Consumer Defensive|Industrial|Real Estate|Crypto|Utilities|Basic Materials|Communication Services",
      "direction": "bullish|bearish|neutral",
      "confidence": 0.0 to 1.0,
      "change_pct": actual 1-day change percentage from sector data above,
      "reason": "1문장 근거 (한국어, 뉴스+실제 퍼포먼스 종합)"
    }}
  ],
  "sentiment_score": -1.0 to 1.0,
  "sentiment_label": "fear|cautious|neutral|optimistic|greed"
}}

Rules:
- market_summary: MUST reference actual index prices and intraday movements from the data above
- sentiment_timeline: 3~4 time periods covering the trading session, each with specific price moves and the news/event that drove sentiment
- key_issues: exactly 3~5 items, sorted by impact (high first). Include which indices were most affected.
- sector_impact: include ALL sectors from the actual performance data above
- CRITICAL: sector direction MUST align with actual performance data (positive change = bullish, negative = bearish)
- confidence: how strongly news supports the price movement
- sentiment_score: -1.0(extreme fear) to 1.0(extreme greed)
- All text in Korean except sector names and index names
"""


def _build_articles_text(articles: list) -> str:
    """기사 리스트를 프롬프트용 텍스트로 변환."""
    by_category = {}
    for art in articles:
        cat = art.category
        by_category.setdefault(cat, []).append(art)

    parts = []
    for cat, items in by_category.items():
        parts.append(f"### {cat.upper()} ({len(items)} articles)")
        for item in items[:20]:
            pub = f" [{item.publisher}]" if item.publisher else ""
            parts.append(f"- {item.title}{pub}")
        parts.append("")
    return "\n".join(parts)


def _build_sector_text(sectors: list[dict]) -> str:
    """섹터 퍼포먼스를 프롬프트용 텍스트로 변환."""
    if not sectors:
        return "(Sector data unavailable)"
    lines = []
    for s in sorted(sectors, key=lambda x: x["change_pct"], reverse=True):
        arrow = "+" if s["change_pct"] > 0 else ""
        lines.append(f"- {s['name']}: {arrow}{s['change_pct']:.2f}%")
    return "\n".join(lines)


def _resolve_model(model: str | None) -> str:
    """모델 이름을 유효한 Claude 모델 ID로 해석."""
    if not model:
        return ANTHROPIC_MODEL
    # 약칭 → 정식 ID 매핑
    for mid, info in AVAILABLE_MODELS.items():
        if model == mid or model == info["label"] or model.lower() in mid.lower():
            return mid
    return model


def analyze_today_news(target_date: str = None, model: str = None) -> dict | None:
    """당일 뉴스 + 실제 섹터 퍼포먼스 + US 지수 데이터를 Claude API로 분석."""
    from backend.app.models.news_article import NewsArticle, MarketNarrative
    from scripts.news_monitor.finviz_fetch import fetch_sector_performance
    from scripts.news_monitor.index_fetch import (
        fetch_all_indices, summarize_index_data, build_index_prompt_text,
    )

    if not ANTHROPIC_API_KEY:
        print("  [WARN] ANTHROPIC_API_KEY not set, skipping analysis")
        return None

    use_model = _resolve_model(model)
    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    db = Session()

    # 당일 기사 조회 (KST/UTC 타임존 차이 대응)
    from sqlalchemy import or_
    prev_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
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
        .order_by(desc(NewsArticle.published_at))
        .limit(MAX_ARTICLES_FOR_ANALYSIS)
        .all()
    )

    if not articles:
        print(f"  [WARN] No articles found for {target_date}")
        db.close()
        return None

    print(f"  Analyzing {len(articles)} articles for {target_date} (model: {use_model})...")

    # US 지수 데이터 수집
    print("  Fetching US index data (DOW, NASDAQ, S&P500, VIX)...")
    raw_indices = fetch_all_indices()
    index_summaries = summarize_index_data(raw_indices)
    index_text = build_index_prompt_text(index_summaries)

    # 실제 섹터 퍼포먼스 수집
    sector_data = fetch_sector_performance()
    sector_text = _build_sector_text(sector_data)

    articles_text = _build_articles_text(articles)
    prompt = ANALYSIS_PROMPT.format(
        article_count=len(articles),
        date=target_date,
        articles_text=articles_text,
        index_data_text=index_text,
        sector_performance_text=sector_text,
    )

    # Claude API 호출
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=use_model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text.strip()
    except Exception as e:
        print(f"  [ERROR] Claude API call failed: {e}")
        db.close()
        return None

    # JSON 파싱
    try:
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0]
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        print(f"  [WARN] JSON parse failed, saving raw text as narrative")
        result = {
            "key_issues": [],
            "narrative": raw_text,
            "market_summary": "",
            "sentiment_timeline": [],
            "sector_impact": [],
            "sentiment_score": 0.0,
            "sentiment_label": "neutral",
        }

    # DB 저장 (UPSERT)
    existing = db.query(MarketNarrative).filter_by(date=target_date).first()
    if existing:
        existing.key_issues = result.get("key_issues", [])
        existing.narrative = result.get("narrative", "")
        existing.sector_impact = result.get("sector_impact", [])
        existing.sentiment_score = result.get("sentiment_score", 0.0)
        existing.sentiment_label = result.get("sentiment_label", "neutral")
        existing.article_count = len(articles)
        existing.index_data = {
            "indices": index_summaries,
            "market_summary": result.get("market_summary", ""),
            "sentiment_timeline": result.get("sentiment_timeline", []),
        }
        existing.generated_by = use_model
        existing.model_used = use_model
    else:
        row = MarketNarrative(
            date=target_date,
            key_issues=result.get("key_issues", []),
            narrative=result.get("narrative", ""),
            sector_impact=result.get("sector_impact", []),
            sentiment_score=result.get("sentiment_score", 0.0),
            sentiment_label=result.get("sentiment_label", "neutral"),
            article_count=len(articles),
            index_data={
                "indices": index_summaries,
                "market_summary": result.get("market_summary", ""),
                "sentiment_timeline": result.get("sentiment_timeline", []),
            },
            generated_by=use_model,
            model_used=use_model,
        )
        db.add(row)

    db.commit()
    db.close()

    print(f"  Analysis saved: {len(result.get('key_issues', []))} issues, "
          f"sentiment={result.get('sentiment_label', 'unknown')}, model={use_model}")
    return result


def generate_from_sector_data(target_date: str = None) -> dict | None:
    """
    AI 없이 실제 섹터 퍼포먼스 데이터만으로 sector_impact 생성.
    Claude API 사용 불가 시 fallback.
    """
    from backend.app.models.news_article import NewsArticle, MarketNarrative
    from scripts.news_monitor.finviz_fetch import fetch_sector_performance
    from scripts.news_monitor.index_fetch import fetch_all_indices, summarize_index_data

    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    sector_data = fetch_sector_performance()
    if not sector_data:
        print("  [WARN] No sector data available")
        return None

    # US 지수 데이터 수집 (fallback에서도)
    raw_indices = fetch_all_indices()
    index_summaries = summarize_index_data(raw_indices)

    # 실제 퍼포먼스 기반 sector_impact 생성
    sector_impact = []
    for s in sorted(sector_data, key=lambda x: abs(x["change_pct"]), reverse=True):
        if s["change_pct"] > 0.3:
            direction = "bullish"
        elif s["change_pct"] < -0.3:
            direction = "bearish"
        else:
            direction = "neutral"
        sector_impact.append({
            "sector": s["name"],
            "direction": direction,
            "confidence": min(abs(s["change_pct"]) / 2.0, 1.0),
            "change_pct": s["change_pct"],
            "reason": f"1일 변동 {s['change_pct']:+.2f}% (Finviz 실시간)",
        })

    # 전체 시장 센티먼트 계산
    avg_change = sum(s["change_pct"] for s in sector_data) / len(sector_data)
    if avg_change > 0.8:
        sentiment_label = "optimistic"
    elif avg_change > 0.2:
        sentiment_label = "neutral"
    elif avg_change > -0.2:
        sentiment_label = "neutral"
    elif avg_change > -0.8:
        sentiment_label = "cautious"
    else:
        sentiment_label = "fear"
    sentiment_score = max(-1.0, min(1.0, avg_change / 2.0))

    # 기사 수 조회
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    db = Session()

    from sqlalchemy import or_
    prev_date = (datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    article_count = (
        db.query(NewsArticle)
        .filter(
            NewsArticle.source != "DEMO",
            or_(
                NewsArticle.published_at.between(f"{target_date} 00:00:00", f"{target_date} 23:59:59"),
                NewsArticle.fetched_at.between(f"{target_date} 00:00:00", f"{target_date} 23:59:59"),
                NewsArticle.fetched_at.between(f"{prev_date} 15:00:00", f"{target_date} 23:59:59"),
            ),
        )
        .count()
    )

    result = {
        "key_issues": [],
        "narrative": "",
        "sector_impact": sector_impact,
        "sentiment_score": round(sentiment_score, 2),
        "sentiment_label": sentiment_label,
    }

    # DB 저장 (UPSERT)
    existing = db.query(MarketNarrative).filter_by(date=target_date).first()
    if existing:
        existing.sector_impact = sector_impact
        existing.sentiment_score = result["sentiment_score"]
        existing.sentiment_label = result["sentiment_label"]
        existing.article_count = article_count
        existing.index_data = {"indices": index_summaries}
        existing.generated_by = "finviz-sector-live"
    else:
        row = MarketNarrative(
            date=target_date,
            key_issues=result["key_issues"],
            narrative=result["narrative"],
            sector_impact=sector_impact,
            sentiment_score=result["sentiment_score"],
            sentiment_label=result["sentiment_label"],
            article_count=article_count,
            index_data={"indices": index_summaries},
            generated_by="finviz-sector-live",
        )
        db.add(row)

    db.commit()
    db.close()

    print(f"  Sector data saved: {len(sector_impact)} sectors, sentiment={sentiment_label}")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Narrative Analyzer")
    parser.add_argument('--date', type=str, default=None, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--model', type=str, default=None,
                        help=f'AI model (available: {", ".join(AVAILABLE_MODELS.keys())})')
    args = parser.parse_args()

    target = args.date
    print(f"[NEWS] Narrative analysis starting (model: {args.model or 'default'})...")
    result = analyze_today_news(target, model=args.model)
    if result is None:
        print("[NEWS] AI analysis unavailable, using sector data fallback...")
        generate_from_sector_data(target)
    print("[NEWS] Done.")
