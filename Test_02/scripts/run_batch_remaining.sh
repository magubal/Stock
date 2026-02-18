#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
echo "[$(date)] Starting remaining stocks from row 420 (~2100 stocks)..."
python -u scripts/stock_moat/batch_moat_value.py --start-row 420 --limit 2100 --save-every 10 2>&1
echo "[$(date)] Batch complete."
