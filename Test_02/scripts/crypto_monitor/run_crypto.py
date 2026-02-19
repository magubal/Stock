"""
Crypto Monitor - Batch Runner
CoinGecko → DefiLlama → Fear&Greed 순차 실행
Usage: python scripts/crypto_monitor/run_crypto.py
"""
import sys
import time
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')


def run(target_date=None):
    """크립토 배치 실행: CoinGecko → DefiLlama → Fear&Greed"""
    start = time.time()
    today = target_date or datetime.now().strftime("%Y-%m-%d")
    print(f"{'='*60}")
    print(f"  Crypto Monitor - Data Collection")
    print(f"  Date: {today}")
    print(f"{'='*60}")

    steps = {}

    # 1. CoinGecko (prices + global)
    print(f"\n[1/3] CoinGecko 코인 가격 + 글로벌 데이터")
    try:
        from coingecko_fetch import run as cg_run
        result = cg_run(today)
        steps["coingecko"] = f"success ({result.get('coins_saved', 0)} coins)"
    except Exception as e:
        steps["coingecko"] = f"failed: {e}"
        print(f"  [SKIP] CoinGecko 수집 실패: {e}")

    # 2. DefiLlama (TVL + stablecoins)
    print(f"\n[2/3] DefiLlama DeFi TVL + 스테이블코인")
    try:
        from defi_fetch import run as defi_run
        result = defi_run(today)
        steps["defillama"] = "success"
    except Exception as e:
        steps["defillama"] = f"failed: {e}"
        print(f"  [SKIP] DefiLlama 수집 실패: {e}")

    # 3. Fear & Greed
    print(f"\n[3/3] Fear & Greed Index")
    try:
        from fear_greed_fetch import run as fg_run
        result = fg_run(today)
        steps["fear_greed"] = f"success ({result.get('index', '?')})"
    except Exception as e:
        steps["fear_greed"] = f"failed: {e}"
        print(f"  [SKIP] Fear & Greed 수집 실패: {e}")

    elapsed = time.time() - start
    ok_count = sum(1 for v in steps.values() if v.startswith("success"))
    status = "success" if ok_count == 3 else ("partial" if ok_count > 0 else "failed")

    print(f"\n{'='*60}")
    print(f"  크립토 배치 완료: {status} ({elapsed:.1f}초, {ok_count}/3 성공)")
    print(f"{'='*60}")

    return {
        "collector": "crypto",
        "status": status,
        "duration": round(elapsed, 1),
        "date": today,
        "steps": steps,
    }


if __name__ == "__main__":
    run()
