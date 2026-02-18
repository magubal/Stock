#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
python scripts/stock_moat/analyze_with_evidence.py --ticker 008340 --name DaejuCores 2>&1
echo "===SEPARATOR==="
python scripts/stock_moat/analyze_with_evidence.py --ticker 008870 --name Geumbi 2>&1
