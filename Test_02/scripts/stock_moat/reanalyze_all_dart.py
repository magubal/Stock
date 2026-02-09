"""
Re-analyze ALL 208 Stocks with DART Official Data
Replaces keyword-based classifications with business report evidence
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
import pandas as pd


def reanalyze_all_stocks():
    """Re-analyze all stocks with DART data"""

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)
    analyzer = MoatAnalyzer()

    print(f"\n{'='*60}")
    print(f"🔄 DART 기반 전체 재분석")
    print(f"{'='*60}\n")

    # Load all stocks
    df = excel_io.load_stock_data()
    total = len(df)

    print(f"총 종목: {total}개")
    print(f"예상 시간: {total}초 (~{total/60:.1f}분)\n")

    print(f"{'='*60}\n")

    # Process all stocks
    batch_updates = []
    stats = {
        'success': 0,
        'failed': 0,
        'high_confidence': 0,
        'medium_confidence': 0,
        'low_confidence': 0
    }

    start_time = time.time()

    for idx, (row_idx, stock) in enumerate(df.iterrows(), start=1):
        ticker = stock['ticker']
        name = stock['name']

        print(f"[{idx}/{total}] {name} ({ticker})")

        try:
            # Analyze with DART
            result = analyzer.analyze_stock(ticker, name, auto_save=False)

            # Prepare update
            update_data = {
                'core_sector_top': result['core_sector_top'],
                'core_sector_sub': result['core_sector_sub'],
                'core_desc': result['core_desc'],
                '해자강도': result['해자강도'],
                '해자DESC': result['해자DESC']
            }

            batch_updates.append({
                'ticker': ticker,
                'data': update_data
            })

            # Track confidence
            confidence = result['confidence']
            if confidence >= 0.8:
                stats['high_confidence'] += 1
            elif confidence >= 0.5:
                stats['medium_confidence'] += 1
            else:
                stats['low_confidence'] += 1

            stats['success'] += 1

            # Progress indicator
            if idx % 10 == 0:
                elapsed = time.time() - start_time
                remaining = (total - idx) * (elapsed / idx)
                print(f"  ⏱️  진행: {idx}/{total} ({idx/total*100:.1f}%) | 남은 시간: {remaining/60:.1f}분\n")

        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            stats['failed'] += 1

        # Rate limiting (DART API)
        time.sleep(0.5)

    # Batch update Excel
    print(f"\n{'='*60}")
    print(f"💾 Excel 업데이트 중...")
    print(f"{'='*60}\n")

    if len(batch_updates) > 0:
        # Update in chunks to avoid memory issues
        chunk_size = 50
        for i in range(0, len(batch_updates), chunk_size):
            chunk = batch_updates[i:i + chunk_size]
            print(f"  Chunk {i//chunk_size + 1}/{(len(batch_updates) + chunk_size - 1)//chunk_size}")

            batch_results = excel_io.batch_update_stocks(
                chunk,
                mode='efficient'
            )

            print(f"  ✅ Updated: {batch_results['success']} stocks\n")

    # Final statistics
    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n{'='*60}")
    print(f"🎉 재분석 완료!")
    print(f"{'='*60}")
    print(f"성공: {stats['success']}")
    print(f"실패: {stats['failed']}")
    print(f"{'='*60}")
    print(f"고신뢰도 (≥80%): {stats['high_confidence']} ({stats['high_confidence']/total*100:.1f}%)")
    print(f"중신뢰도 (50-80%): {stats['medium_confidence']} ({stats['medium_confidence']/total*100:.1f}%)")
    print(f"저신뢰도 (<50%): {stats['low_confidence']} ({stats['low_confidence']/total*100:.1f}%)")
    print(f"{'='*60}")
    print(f"총 소요 시간: {total_time/60:.1f}분")
    print(f"{'='*60}\n")

    # Final verification
    df_after = excel_io.load_stock_data()
    completed_after = df_after[df_after['해자강도'].notna()]
    low_conf_after = df_after[(df_after['해자강도'].notna()) & (df_after['core_sector_top'] == '기타')]

    print(f"📊 최종 상태:")
    print(f"  완료: {len(completed_after)}/{len(df_after)}")
    print(f"  '기타' 분류: {len(low_conf_after)} ({len(low_conf_after)/len(completed_after)*100:.1f}%)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    reanalyze_all_stocks()
