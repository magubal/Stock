#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
echo "[$(date)] Starting batch 100 stocks..."
python -u scripts/stock_moat/batch_moat_value.py --start-row 10 --limit 100 2>&1
echo "[$(date)] Batch complete."
