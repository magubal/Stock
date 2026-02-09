import openpyxl
import json

excel_path = r'F:\PSJ\AntigravityWorkPlace\Stock\Test_02\data\MGB_daily\stock_core_master_v2_korean_taxonomy_2026-01-30.xlsx'

print(f"Opening workbook: {excel_path}")
wb = openpyxl.load_workbook(excel_path, data_only=True)
sheet = wb['stock_core_master']

# Get headers
headers = [cell.value for cell in sheet[1]]
col_map = {val: i for i, val in enumerate(headers)}

missing_stocks = []

# Essential columns to check: core_sector_top, core_desc, 해자강도, moat_name
# Based on headers in image: C, E, F, H
target_cols = ['ticker', 'name', 'core_sector_top', 'core_sector_sub', 'core_desc', '해자강도', '해자DESC', 'moat_name', 'desc']

for row_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
    ticker = row[col_map['ticker']].value
    name = row[col_map['name']].value
    sector_top = row[col_map['core_sector_top']].value
    
    if ticker is None:
        continue
        
    # Check if any target information is missing
    # In the image, rows 2-19 are clearly missing core_sector_top etc.
    if sector_top is None or sector_top == "":
        missing_fields = []
        for col in target_cols:
            if row[col_map[col]].value is None or row[col_map[col]].value == "":
                missing_fields.append(col)
        
        missing_stocks.append({
            "ticker": str(ticker),
            "name": name,
            "row": row_idx,
            "missing_fields": missing_fields
        })

print(json.dumps(missing_stocks, ensure_ascii=False, indent=2))
