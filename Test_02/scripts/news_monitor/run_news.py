"""
News Intelligence Monitor - Unified Batch Runner
데이터 수집 파이프라인: 뉴스 → 종목(Stock) → 섹터 매트릭스 → AI 분석

수집 순서 (중요):
  1. Finviz 뉴스 수집 (5 카테고리)
  2. Industry Stock 배치 수집 (144 industries, ~20분 소요)
  3. Sector Impact Matrix (섹터 + 인더스트리 퍼포먼스)
  4. AI 내러티브 분석 (Claude Sonnet)

Stock 수집이 Sector Matrix 직전에 실행되어야 하는 이유:
  - 종목별 당일 변화율이 섹터 영향도 분석의 근거 데이터로 활용됨
  - Sector Matrix가 최신 종목 데이터를 기반으로 집계되어야 일관성 확보

Usage:
  python scripts/news_monitor/run_news.py
  python scripts/news_monitor/run_news.py --skip-analysis --skip-stocks
  python scripts/news_monitor/run_news.py --max-stocks 10
  python scripts/news_monitor/run_news.py --date 2026-02-19
"""
import sys
import os
import argparse
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.stdout.reconfigure(encoding='utf-8')

from scripts.news_monitor.config import DB_PATH
from scripts.news_monitor.finviz_fetch import (
    fetch_all_categories,
    save_sector_industry_performance,
)
from scripts.news_monitor.narrative_analyzer import analyze_today_news


def ensure_tables():
    """테이블 자동 생성 (없으면)."""
    from sqlalchemy import create_engine
    from backend.app.models.news_article import NewsArticle, MarketNarrative
    from backend.app.database import Base

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(bind=engine)


def main():
    parser = argparse.ArgumentParser(description="News Intelligence Monitor - Unified Batch")
    parser.add_argument('--skip-analysis', action='store_true', help='Skip Claude AI analysis (Step 4)')
    parser.add_argument('--skip-stocks', action='store_true', help='Skip stock batch collection (Step 2)')
    parser.add_argument('--skip-sector', action='store_true', help='Skip sector matrix collection (Step 3)')
    parser.add_argument('--max-stocks', type=int, default=0, help='Max industries for stock collection (0=all)')
    parser.add_argument('--date', type=str, default=None, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--stocks-only', action='store_true', help='Run only stock batch (Step 2)')
    parser.add_argument('--model', type=str, default=None, help='AI model for analysis (sonnet/haiku/opus)')
    args = parser.parse_args()

    # KST 기준 날짜 (한국 시장 기준)
    kst_now = datetime.now(timezone.utc) + timedelta(hours=9)
    target_date = args.date or kst_now.strftime("%Y-%m-%d")

    print("=" * 60)
    print(f"[NEWS] News Intelligence Monitor - Unified Batch")
    print(f"[NEWS] Date: {target_date}")
    print(f"[NEWS] Pipeline: News → Stocks → Sector Matrix → AI")
    print("=" * 60)

    # 0. 테이블 확인
    ensure_tables()

    batch_start = time.time()

    # --stocks-only 모드: Step 2만 실행
    if args.stocks_only:
        _run_step2_stocks(target_date, args.max_stocks)
        elapsed = time.time() - batch_start
        print(f"\n{'=' * 60}")
        print(f"[NEWS] Stocks-only batch complete. ({elapsed:.0f}s)")
        print(f"{'=' * 60}")
        return

    # ── Step 1: 뉴스 수집 ──
    print(f"\n{'─' * 50}")
    print("[Step 1/4] Fetching news from Finviz...")
    print(f"{'─' * 50}")
    results = fetch_all_categories()
    total_saved = sum(r["saved"] for r in results.values())
    total_fetched = sum(r["fetched"] for r in results.values())
    print(f"[Step 1] Complete: {total_fetched} fetched, {total_saved} saved")

    # ── Step 2: Stock 배치 수집 (Sector Matrix 직전) ──
    if args.skip_stocks:
        print(f"\n{'─' * 50}")
        print("[Step 2/4] Stock batch collection - SKIPPED (--skip-stocks)")
        print(f"{'─' * 50}")
    else:
        _run_step2_stocks(target_date, args.max_stocks)

    # ── Step 3: Sector Impact Matrix (섹터 + 인더스트리 퍼포먼스) ──
    if args.skip_sector:
        print(f"\n{'─' * 50}")
        print("[Step 3/4] Sector Impact Matrix - SKIPPED (--skip-sector)")
        print(f"{'─' * 50}")
    else:
        print(f"\n{'─' * 50}")
        print("[Step 3/4] Fetching Sector Impact Matrix...")
        print(f"{'─' * 50}")
        perf_result = save_sector_industry_performance(target_date)
        print(f"[Step 3] Complete: {perf_result.get('sectors', 0)} sectors, "
              f"{perf_result.get('industries', 0)} industries saved")

    # ── Step 4: AI 내러티브 분석 ──
    if args.skip_analysis:
        print(f"\n{'─' * 50}")
        print("[Step 4/4] AI narrative analysis - SKIPPED (--skip-analysis)")
        print(f"{'─' * 50}")
    else:
        print(f"\n{'─' * 50}")
        print("[Step 4/4] Running AI narrative analysis...")
        print(f"{'─' * 50}")
        result = analyze_today_news(target_date, model=args.model)
        if result:
            print(f"[Step 4] Complete: sentiment={result.get('sentiment_label', 'N/A')}")
        else:
            print("[Step 4] No analysis generated (no articles or API key missing)")

    elapsed = time.time() - batch_start
    print(f"\n{'=' * 60}")
    print(f"[NEWS] Unified batch complete. ({elapsed:.0f}s)")
    print(f"{'=' * 60}")


def _run_step2_stocks(target_date: str, max_industries: int):
    """Step 2: Industry Stock 배치 수집."""
    print(f"\n{'─' * 50}")
    print("[Step 2/4] Stock batch collection (before Sector Matrix)...")
    if max_industries > 0:
        print(f"  Limited to {max_industries} industries")
    else:
        print(f"  Full batch: 144 industries (~20min with anti-blocking delay)")
    print(f"{'─' * 50}")

    from scripts.news_monitor.stock_fetch import run_batch
    stock_result = run_batch(target_date=target_date, max_industries=max_industries)
    if stock_result:
        print(f"[Step 2] Complete: {stock_result.get('industries', 0)} industries, "
              f"{stock_result.get('stocks', 0)} stocks in {stock_result.get('elapsed', 0):.0f}s")
    else:
        print("[Step 2] No stocks collected")


if __name__ == "__main__":
    main()
