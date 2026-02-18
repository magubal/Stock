import pandas as pd
import sys

# Set encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

excel_path = 'data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx'
try:
    df = pd.read_excel(excel_path, sheet_name='stock_core_master', nrows=10, engine='openpyxl')
    print(f"Columns: {df.columns.tolist()}")
    
    for i in range(len(df)):
        name = df.iloc[i, 1]
        ticker = df.iloc[i, 0]
        # Find 해자DESC column index
        col_idx = -1
        for j, col in enumerate(df.columns):
            if 'DESC' in str(col):
                col_idx = j
                break
        
        if col_idx != -1:
            val = df.iloc[i, col_idx]
            print(f"Row {i+1} ({name} - {ticker}):")
            print(f"  Column Header: {df.columns[col_idx]}")
            print(f"  Content (repr): {repr(val)}")
            print("-" * 40)
except Exception as e:
    print(f"Error: {e}")
