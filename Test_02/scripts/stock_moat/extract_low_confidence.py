"""
Extract Low-Confidence Stocks for Manual Review
Creates a separate list of stocks with confidence < 50%
"""

import sys
import os
import json

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from excel_io import ExcelIO
import pandas as pd


def extract_low_confidence():
    """Extract stocks with low confidence (기타/미분류) for manual review"""

    excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
    excel_io = ExcelIO(excel_path)

    print(f"\n{'='*60}")
    print(f"📋 Extracting Low-Confidence Stocks")
    print(f"{'='*60}\n")

    # Load data
    df = excel_io.load_stock_data()

    # Find low-confidence stocks (기타/미분류)
    low_confidence = df[
        (df['해자강도'].notna()) &  # Analyzed
        (
            (df['core_sector_top'] == '기타') |
            (df['core_sector_sub'] == '미분류')
        )
    ].copy()

    print(f"Found {len(low_confidence)} low-confidence stocks\n")

    # Group by pattern
    categories = {
        '제조업': [],
        '제지/펄프': [],
        '여행/관광': [],
        '화장품/뷰티': [],
        '엔터테인먼트': [],
        '기타': []
    }

    for idx, stock in low_confidence.iterrows():
        ticker = stock['ticker']
        name = stock['name']

        # Pattern matching for categorization
        if any(keyword in name for keyword in ['제지', '판지', '펄프', 'P&P', 'PNS', 'SP']):
            categories['제조업'].append({'ticker': ticker, 'name': name})
        elif any(keyword in name for keyword in ['투어', '여행', 'Cruise', 'Carnival', 'Royal', 'Norwegian']):
            categories['여행/관광'].append({'ticker': ticker, 'name': name})
        elif any(keyword in name for keyword in ['마녀공장', '뷰티', '코디', '아모레', '코리아나', '에이피알', '삐아', '달바', '아로마티카']):
            categories['화장품/뷰티'].append({'ticker': ticker, 'name': name})
        elif any(keyword in name for keyword in ['하이브', 'HYBE', '에스엠', 'SM', '미디어', 'TJ']):
            categories['엔터테인먼트'].append({'ticker': ticker, 'name': name})
        else:
            categories['기타'].append({'ticker': ticker, 'name': name})

    # Display results
    for category, stocks in categories.items():
        if len(stocks) > 0:
            print(f"\n### {category} ({len(stocks)}개)")
            print(f"{'─'*60}")
            for stock in stocks[:10]:  # Show first 10
                print(f"  {stock['ticker']}: {stock['name']}")
            if len(stocks) > 10:
                print(f"  ... and {len(stocks) - 10} more")

    # Save to JSON
    output_path = f"{project_root}/data/stock_moat/low_confidence_stocks.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    output = {
        'total_count': len(low_confidence),
        'categories': {
            category: [
                {
                    'ticker': stock['ticker'],
                    'name': stock['name'],
                    'current_classification': f"{df[df['ticker'] == stock['ticker']].iloc[0]['core_sector_top']}/{df[df['ticker'] == stock['ticker']].iloc[0]['core_sector_sub']}"
                }
                for stock in stocks
            ]
            for category, stocks in categories.items() if len(stocks) > 0
        },
        'generated_at': pd.Timestamp.now().isoformat()
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Saved to: {output_path}")
    print(f"{'='*60}\n")

    return output


if __name__ == "__main__":
    result = extract_low_confidence()
