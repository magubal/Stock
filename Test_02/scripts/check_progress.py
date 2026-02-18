import sys, openpyxl
sys.stdout.reconfigure(encoding='utf-8')
wb = openpyxl.load_workbook(r'f:\PSJ\AntigravityWorkPlace\Stock\Test_02\data\국내상장종목 해자 투자가치.xlsx')
ws = wb.active
headers = {}
for c in range(1, ws.max_column + 1):
    v = ws.cell(row=1, column=c).value
    if v: headers[v] = c
col_code = headers.get('종목코드')
col_name = headers.get('종목명')
col_date = headers.get('평가일자')
col_moat = headers.get('해자')
col_value = headers.get('투자가치')

last_row = None
total_evaluated = 0
for r in range(2, ws.max_row + 1):
    moat = ws.cell(row=r, column=col_moat).value
    if moat is not None:
        last_row = r
        total_evaluated += 1

if last_row:
    code = ws.cell(row=last_row, column=col_code).value
    name = ws.cell(row=last_row, column=col_name).value
    dt = ws.cell(row=last_row, column=col_date).value
    moat = ws.cell(row=last_row, column=col_moat).value
    val = ws.cell(row=last_row, column=col_value).value
    print(f'Total evaluated: {total_evaluated}')
    print(f'Total stocks: {ws.max_row - 1}')
    print(f'Last row: {last_row}')
    print(f'Last stock: {code} {name}')
    print(f'Date: {dt}, Moat: {moat}/5, Value: {val}/5')
    print(f'Next start: --start-row {last_row + 1}')
