#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
python scripts/stock_moat/analyze_with_evidence.py --ticker 049130 --name Hauri 2>&1
echo "===SEPARATOR==="
python scripts/stock_moat/analyze_with_evidence.py --ticker 008120 --name Msonic 2>&1
