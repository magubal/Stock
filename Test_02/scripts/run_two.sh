#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
python scripts/stock_moat/analyze_with_evidence.py --ticker 003610 --name Bangrim 2>&1
echo "===SEPARATOR==="
python scripts/stock_moat/analyze_with_evidence.py --ticker 005900 --name DongyangConst 2>&1
