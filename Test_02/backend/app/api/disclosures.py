from fastapi import APIRouter, HTTPException, Query
import json
import os
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/v1/disclosures", tags=["Disclosures"])

# Paths
# backend/app/api/disclosures.py -> backend/app/api -> backend/app -> backend -> root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DASHBOARD_DATA_DIR = os.path.join(BASE_DIR, "dashboard", "data")
DATA_DIR = os.path.join(BASE_DIR, "data", "disclosures")

@router.get("")
async def get_disclosures(date: str = Query(None, description="Date (YYYY-MM-DD)")):
    """
    Get disclosures data.
    If date is not provided or is today, returns the latest processed data from dashboard/data.
    Otherwise, attempts to find processed data in data/disclosures.
    """
    kst_now = datetime.now(timezone.utc) + timedelta(hours=9)
    today = kst_now.strftime("%Y-%m-%d")
    
    target_date = date if date else today
    
    # Try processed file first
    if target_date == today:
        file_path = os.path.join(DASHBOARD_DATA_DIR, "latest_disclosures.json")
    else:
        file_path = os.path.join(DATA_DIR, f"processed_{target_date}.json")
        
    if not os.path.exists(file_path):
        # Fallback for today: check data/disclosures/YYYY-MM-DD.json (raw) if processed doesn't exist?
        # The analyzer should have run. If not, maybe raw data exists.
        # For now, just return 404 if processed data is missing.
        raise HTTPException(status_code=404, detail=f"Not Found: {file_path}")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
