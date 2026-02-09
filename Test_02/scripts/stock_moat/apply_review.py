"""
Apply Review Report to Excel
Processes low_confidence_review.json and updates approved classifications
"""

import sys
import os
import json
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from excel_io import ExcelIO
import pandas as pd


def apply_review_report():
    """Apply approved review suggestions to Excel"""

    # Load review report
    review_path = f"{project_root}/data/stock_moat/low_confidence_review.json"

    if not os.path.exists(review_path):
        print(f"\n❌ 리뷰 파일 없음: {review_path}")
        print("먼저 generate_review_report.py를 실행하세요.\n")
        return

    with open(review_path, 'r', encoding='utf-8') as f:
        review_data = json.load(f)

    print(f"\n{'='*60}")
    print(f"📝 리뷰 보고서 적용")
    print(f"{'='*60}\n")
    print(f"생성 시각: {review_data['generated_at']}")
    print(f"총 종목: {review_data['total_stocks']}개\n")

    # Prepare updates
    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)

    batch_updates = []
    stats = {
        'approved': 0,
        'rejected': 0,
        'custom': 0,
        'skipped': 0
    }

    for stock in review_data['stocks']:
        ticker = stock['ticker']
        name = stock['name']
        action = stock.get('action', 'approve')

        if action == 'approve':
            # Use AI suggestion
            update_data = {
                'core_sector_top': stock['suggested_sector'],
                'core_sector_sub': stock['suggested_sub'],
                'core_desc': f"{name} - {stock['reasoning']}"
            }
            batch_updates.append({'ticker': ticker, 'data': update_data})
            stats['approved'] += 1
            print(f"✅ {name} ({ticker}): {stock['suggested_sector']}/{stock['suggested_sub']}")

        elif action == 'custom':
            # Use custom fields
            if 'custom_sector' in stock and 'custom_sub' in stock:
                custom_reasoning = stock.get('custom_reasoning', f"수동 분류 (DART {stock['dart_code']})")
                update_data = {
                    'core_sector_top': stock['custom_sector'],
                    'core_sector_sub': stock['custom_sub'],
                    'core_desc': f"{name} - {custom_reasoning}"
                }
                batch_updates.append({'ticker': ticker, 'data': update_data})
                stats['custom'] += 1
                print(f"🔧 {name} ({ticker}): {stock['custom_sector']}/{stock['custom_sub']} (수동)")
            else:
                stats['skipped'] += 1
                print(f"⏭️  {name} ({ticker}): custom 필드 없음 (건너뜀)")

        elif action == 'reject':
            # Keep current classification
            stats['rejected'] += 1
            print(f"⏸️  {name} ({ticker}): 현재 유지")

        else:
            stats['skipped'] += 1
            print(f"⏭️  {name} ({ticker}): 알 수 없는 action '{action}' (건너뜀)")

    # Apply batch update
    print(f"\n{'='*60}")
    print(f"💾 Excel 업데이트 중...")
    print(f"{'='*60}\n")

    if len(batch_updates) > 0:
        results = excel_io.batch_update_stocks(batch_updates, mode='efficient')
        print(f"✅ 업데이트 완료: {results['success']}개")
        if results['failed'] > 0:
            print(f"❌ 실패: {results['failed']}개")
    else:
        print("업데이트할 항목이 없습니다.")

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 적용 결과")
    print(f"{'='*60}")
    print(f"승인 (approve): {stats['approved']}개")
    print(f"거부 (reject): {stats['rejected']}개")
    print(f"수동 (custom): {stats['custom']}개")
    print(f"건너뜀 (skipped): {stats['skipped']}개")
    print(f"{'='*60}\n")

    # Final verification
    df_after = excel_io.load_stock_data()
    completed = df_after[df_after['해자강도'].notna()]
    low_conf_after = df_after[
        (df_after['해자강도'].notna()) &
        (df_after['core_sector_top'] == '기타')
    ]

    print(f"📊 최종 상태:")
    print(f"  완료: {len(completed)}/{len(df_after)}")
    print(f"  '기타' 분류: {len(low_conf_after)} ({len(low_conf_after)/len(completed)*100:.1f}%)")
    print(f"{'='*60}\n")

    # Archive review file
    archive_path = review_path.replace('.json', f'.applied_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    os.rename(review_path, archive_path)
    print(f"📁 리뷰 파일 보관: {os.path.basename(archive_path)}\n")


if __name__ == "__main__":
    apply_review_report()
