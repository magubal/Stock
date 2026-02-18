
import sys
import os
from datetime import datetime

# Add paths
sys.path.insert(0, "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/.agent/skills/stock-moat/utils")
from config import get_dart_api_key
from dart_client import DARTClient

def verify_search():
    api_key = get_dart_api_key()
    dart = DARTClient(api_key)
    
    # Samsung Electronics Corp Code
    corp_code = "00126380" 
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Searching for LATEST report (Annual/Semi-Annual) for Samsung...")
    
    latest = dart.find_latest_report(corp_code)
    
    if latest:
        print(f"    ✅ WINNER: {latest.get('report_nm')}")
        print(f"       Date:   {latest.get('rcept_dt')}")
        print(f"       ID:     {latest.get('rcept_no')}")
    else:
        print("    ❌ No report found.")

if __name__ == "__main__":
    verify_search()
