"""
Check Final Status of Stock Moat Analysis
"""

import sys
import os

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from excel_io import ExcelIO
import pandas as pd


def check_final_status():
    """Check final analysis status"""

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)

    # Load data
    df = excel_io.load_stock_data()

    # Statistics
    completed = df[df['해자강도'].notna()]
    incomplete = df[df['해자강도'].isna()]
    low_conf = df[(df['해자강도'].notna()) & (df['core_sector_top'] == '기타')]
    high_moat = df[df['해자강도'] >= 4]

    print(f"\n{'━'*60}")
    print(f"📊 전체 진행 상황")
    print(f"{'━'*60}")
    print(f"총 종목: {len(df)}")
    print(f"완료: {len(completed)} ({len(completed)/len(df)*100:.1f}%)")
    print(f"미완료: {len(incomplete)} ({len(incomplete)/len(df)*100:.1f}%)")
    print(f"{'━'*60}")
    print(f"High moat (≥4): {len(high_moat)}")
    print(f"Low-confidence (기타): {len(low_conf)}")
    print(f"{'━'*60}\n")

    if len(high_moat) > 0:
        print("🌟 High Moat Stocks:")
        for idx, stock in high_moat.iterrows():
            print(f"  {stock['ticker']}: {stock['name']}")
            print(f"    Sector: {stock['core_sector_top']} / {stock['core_sector_sub']}")
            print(f"    해자강도: {stock['해자강도']}/5")
            print()

    if len(incomplete) > 0:
        print(f"⏳ 미완료 종목 샘플 (첫 10개):")
        for idx, stock in incomplete.head(10).iterrows():
            print(f"  {stock['ticker']}: {stock['name']}")
        if len(incomplete) > 10:
            print(f"  ... and {len(incomplete) - 10} more")
        print()

    print(f"{'━'*60}")
    print(f"분류 분포:")
    print(f"{'━'*60}")
    sector_counts = completed['core_sector_top'].value_counts()
    for sector, count in sector_counts.head(10).items():
        percentage = count / len(completed) * 100
        print(f"  {sector}: {count} ({percentage:.1f}%)")
    print(f"{'━'*60}\n")


if __name__ == "__main__":
    check_final_status()
