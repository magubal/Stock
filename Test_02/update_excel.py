import pandas as pd
import json
import os
import sys

# Paths
excel_path = r'F:\PSJ\AntigravityWorkPlace\Stock\Test_02\data\MGB_daily\stock_core_master_v2_korean_taxonomy_2026-01-30.xlsx'
json_path = sys.argv[1] if len(sys.argv) > 1 else r'F:\PSJ\AntigravityWorkPlace\Stock\Test_02\researched_stocks_final.json'

# Load researched data
with open(json_path, 'r', encoding='utf-8') as f:
    researched_data = json.load(f)

print(f"Loading Excel file: {excel_path}")
df_dict = pd.read_excel(excel_path, sheet_name=None)
master_df = df_dict['stock_core_master']

# Ensure ticker column is string for reliable matching
master_df['ticker'] = master_df['ticker'].astype(str).str.zfill(6)
# Column mapping: A: ticker, B: name, C: core_sector_top, D: core_sector_sub, E: core_desc, 
# F: moat_strength, G: moat_desc_detail, H: moat_name, I: desc

updated_count = 0
for data in researched_data:
    ticker = data['ticker']
    # Efficiently find the row by ticker
    # Note: tickers might be strings or numbers in Excel
    mask = master_df['ticker'].astype(str) == ticker
    if mask.any():
        idx = master_df[mask].index[0]
        master_df.at[idx, 'core_sector_top'] = data['core_sector_top']
        master_df.at[idx, 'core_sector_sub'] = data['core_sector_sub']
        master_df.at[idx, 'core_desc'] = data['core_desc']
        master_df.at[idx, '해자강도'] = data['moat_strength'] # Column name from XML was '해자강도'
        master_df.at[idx, '해자DESC'] = data['moat_desc'] # Column name from XML was '해자DESC'
        master_df.at[idx, 'moat_name'] = data['moat_name']
        master_df.at[idx, 'desc'] = data['core_desc'] # Usually maps to core_desc for simplicity or specific usage
        updated_count += 1

print(f"Updated {updated_count} stocks in the master sheet.")

# Save back to Excel preserving other sheets
output_path = excel_path # Overwrite original as per request or save new and rename
# To avoid losing other sheets, we write all sheets back
with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
    for sheet_name, df in df_dict.items():
        if sheet_name == 'stock_core_master':
            master_df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Excel file successfully updated.")
