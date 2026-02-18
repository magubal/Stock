#!/bin/bash
cd /f/PSJ/AntigravityWorkPlace/Stock/Test_02
python scripts/stock_moat/analyze_with_evidence.py --ticker "$1" --name "$2" 2>&1
