"""
End-of-Day Batch Runner
모든 수집기를 순서대로 실행하고 스트레스 인덱스를 계산합니다.
Usage: python scripts/liquidity_monitor/run_eod.py
"""
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')


def run():
    """EOD 배치 실행: FRED → Price → News → Fed → Calculate"""
    start = time.time()
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"{'='*60}")
    print(f"  Liquidity Stress Monitor - EOD Batch")
    print(f"  Date: {today}")
    print(f"{'='*60}")

    # 1. FRED Macro
    print(f"\n[1/5] FRED 매크로 지표 수집")
    try:
        from fred_fetch import run as fred_run
        fred_run()
    except Exception as e:
        print(f"  [SKIP] FRED 수집 실패: {e}")

    # 2. Yahoo Price
    print(f"\n[2/5] ETF/지수 가격 수집")
    try:
        from price_fetch import run as price_run
        price_run()
    except Exception as e:
        print(f"  [SKIP] Price 수집 실패: {e}")

    # 3. News
    print(f"\n[3/5] 위기 키워드 뉴스 수집")
    try:
        from news_fetch import run as news_run
        news_run()
    except Exception as e:
        print(f"  [SKIP] News 수집 실패: {e}")

    # 4. Fed Tone
    print(f"\n[4/5] Fed 스피치 톤 분석")
    try:
        from fed_speech_fetch import run as fed_run
        fed_run()
    except Exception as e:
        print(f"  [SKIP] Fed 톤 분석 실패: {e}")

    # 5. Calculate
    print(f"\n[5/5] 스트레스 인덱스 계산")
    try:
        from stress_calculator import calculate
        total, level = calculate(today)
    except Exception as e:
        print(f"  [SKIP] 인덱스 계산 실패: {e}")

    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  EOD 배치 완료 ({elapsed:.1f}초)")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
