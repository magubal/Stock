#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
echo "[$(date)] Testing batch with 2 stocks..."
python -u scripts/stock_moat/batch_moat_value.py --start-row 8 --limit 2 2>&1
echo "[$(date)] Done."
