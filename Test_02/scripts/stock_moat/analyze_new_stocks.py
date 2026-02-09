"""
Analyze New Stocks Only
Analyzes stocks that don't have 해자강도 filled yet
"""

import sys
import os
import time

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from excel_io import ExcelIO
from moat_analyzer import MoatAnalyzer


def analyze_new_stocks(limit: int = None):
    """Analyze only stocks without 해자강도

    Args:
        limit: Maximum number of stocks to analyze (None = all)
    """

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)
    analyzer = MoatAnalyzer()

    print(f"\n{'='*60}")
    print(f"🔍 신규 종목 해자 분석")
    if limit:
        print(f"   (테스트 모드: {limit}개만 분석)")
    print(f"{'='*60}\n")

    # Load stocks
    df = excel_io.load_stock_data()

    # Find stocks without 해자강도 OR with fallback classification
    # Fallback: core_sector_top='기타' and 해자강도=2
    new_stocks = df[
        df['해자강도'].isna() |
        ((df['core_sector_top'] == '기타') & (df['해자강도'] == 2))
    ]

    # Apply limit if specified
    if limit and len(new_stocks) > limit:
        total_new = len(new_stocks)
        new_stocks = new_stocks.head(limit)
        print(f"⚠️  테스트 모드: 전체 {total_new}개 중 {limit}개만 분석\n")

    total = len(new_stocks)
    print(f"재분석 대상 종목: {total}개 (fallback 분류 포함)")

    if total == 0:
        print("분석할 신규 종목이 없습니다.")
        print("모든 종목이 이미 분석되었습니다.\n")
        return

    print(f"예상 시간: ~{total * 0.5 / 60:.1f}분\n")
    print(f"{'='*60}\n")

    batch_updates = []
    stats = {'success': 0, 'failed': 0}

    start_time = time.time()

    for idx, (row_idx, stock) in enumerate(new_stocks.iterrows(), start=1):
        ticker = stock['ticker']
        name = stock['name']

        print(f"[{idx}/{total}] {name} ({ticker})")

        try:
            # Analyze with GICS
            result = analyzer.analyze_stock(ticker, name, auto_save=False)

            print(f"  ✅ {result['core_sector_top']} / {result['core_sector_sub']}")
            print(f"  해자강도: {result['해자강도']}/5\n")

            # Prepare update
            update_data = {
                'core_sector_top': result['core_sector_top'],
                'core_sector_sub': result['core_sector_sub'],
                'core_desc': result['core_desc'],
                '해자강도': result['해자강도'],
                '해자DESC': result['해자DESC']
            }

            batch_updates.append({'ticker': ticker, 'data': update_data})
            stats['success'] += 1

        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            stats['failed'] += 1

        # Progress indicator
        if idx % 10 == 0:
            elapsed = time.time() - start_time
            remaining = (total - idx) * (elapsed / idx)
            print(f"  ⏱️  진행: {idx}/{total} ({idx/total*100:.1f}%) | 남은 시간: {remaining/60:.1f}분\n")

        # Rate limiting (increased to avoid DART API rate limit)
        time.sleep(2.0)  # 2 seconds between requests

    # Batch update Excel
    if len(batch_updates) > 0:
        print(f"\n{'='*60}")
        print(f"💾 Excel 업데이트 중...")
        print(f"{'='*60}\n")

        results = excel_io.batch_update_stocks(batch_updates, mode='efficient')
        print(f"✅ 업데이트 완료: {results['success']}개\n")

    # Summary
    end_time = time.time()
    total_time = end_time - start_time

    print(f"{'='*60}")
    print(f"🎉 분석 완료!")
    print(f"{'='*60}")
    print(f"성공: {stats['success']}")
    print(f"실패: {stats['failed']}")
    print(f"소요 시간: {total_time/60:.1f}분")
    print(f"{'='*60}\n")

    # Final verification
    df_after = excel_io.load_stock_data()
    completed = df_after[df_after['해자강도'].notna()]
    print(f"📊 최종 상태: {len(completed)}/{len(df_after)} 완료\n")


if __name__ == "__main__":
    import sys

    # Check for test mode argument
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"테스트 모드: {limit}개 종목만 분석합니다.\n")
        except ValueError:
            print("Usage: python analyze_new_stocks.py [limit]")
            sys.exit(1)

    analyze_new_stocks(limit=limit)
