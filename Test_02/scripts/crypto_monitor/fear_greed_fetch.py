"""Fear & Greed Index fetcher."""
import sys
import json
from datetime import datetime
from urllib.request import urlopen, Request

sys.stdout.reconfigure(encoding='utf-8')

from config import FEAR_GREED_URL, REQUEST_TIMEOUT, DB_PATH


def run(target_date=None):
    """Fear & Greed Index 수집 → DB 저장."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[2]))
    from backend.app.models.crypto import CryptoMetric

    today = target_date or datetime.now().strftime("%Y-%m-%d")
    engine = create_engine(f'sqlite:///{DB_PATH}')
    CryptoMetric.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    result = {"index": None, "label": None}

    try:
        req = Request(FEAR_GREED_URL, headers={"User-Agent": "StockResearchONE/1.0"})
        resp = urlopen(req, timeout=REQUEST_TIMEOUT)
        data = json.loads(resp.read())
        fng = data.get("data", [{}])[0]
        index_val = int(fng.get("value", 0))
        label = fng.get("value_classification", "Unknown")

        metric = db.query(CryptoMetric).filter_by(date=today).first()
        if not metric:
            metric = CryptoMetric(date=today)
            db.add(metric)
        metric.fear_greed_index = index_val
        metric.fear_greed_label = label
        db.commit()

        result["index"] = index_val
        result["label"] = label
        print(f"  [OK] Fear & Greed: {index_val} ({label})")
    except Exception as e:
        print(f"  [SKIP] Fear & Greed: {e}")

    db.close()
    return result


if __name__ == "__main__":
    run()
