#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
echo "[$(date)] Starting batch 500 stocks (row 110~)..."
python -u scripts/stock_moat/batch_moat_value.py --start-row 110 --limit 500 --save-every 10 2>&1
echo "[$(date)] Batch complete."
