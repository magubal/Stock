"""
Data Collector API - 데이터 수집 트리거 엔드포인트
POST /api/v1/collector/liquidity  - 유동성 데이터 수집
POST /api/v1/collector/crypto     - 크립토 데이터 수집
POST /api/v1/collector/run-all    - 전체 순차 수집
GET  /api/v1/collector/status     - 수집 상태 조회
"""
import sys
import os
import time
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/collector", tags=["collector"])

_scripts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_DB_PATH = os.path.join(_scripts_root, 'backend', 'stock_research.db')


def _log_collection(collector: str, status: str, duration: float, steps: dict, triggered_by: str):
    """수집 결과를 collector_log 테이블에 기록."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.app.models.crypto import CollectorLog

        engine = create_engine(f'sqlite:///{_DB_PATH}')
        CollectorLog.__table__.create(engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        db = Session()

        utc_now = datetime.now(timezone.utc)
        kst_now = utc_now + timedelta(hours=9)
        today = kst_now.strftime("%Y-%m-%d")

        db.add(CollectorLog(
            date=today,
            collector=collector,
            status=status,
            duration=round(duration, 1),
            details=steps,
            triggered_by=triggered_by,
        ))
        db.commit()
        db.close()
    except Exception as e:
        print(f"  [WARN] collector_log 기록 실패: {e}")


def _load_module_from_file(name, filepath):
    """파일 경로에서 모듈을 직접 로드 (sys.path 의존 없이)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_liquidity_collector() -> dict:
    """유동성 스트레스 데이터 수집 (run_eod.py 래핑)."""
    start = time.time()
    liq_dir = os.path.join(_scripts_root, 'scripts', 'liquidity_monitor')

    # 각 스크립트를 파일 경로로 직접 로드 (config 충돌 방지)
    # 먼저 config를 올바른 경로에서 로드하여 sys.modules에 등록
    config_path = os.path.join(liq_dir, 'config.py')
    liq_config = _load_module_from_file('config', config_path)
    old_config = sys.modules.get('config')
    sys.modules['config'] = liq_config

    original_path = sys.path[:]
    sys.path.insert(0, liq_dir)
    sys.path.insert(0, _scripts_root)

    # 기존 liquidity 모듈 캐시 제거 (재로드 보장)
    mods_to_remove = [k for k in sys.modules if k.startswith('scripts.liquidity_monitor.') or
                      k in ('fred_fetch', 'price_fetch', 'news_fetch', 'fed_speech_fetch', 'stress_calculator')]
    for k in mods_to_remove:
        del sys.modules[k]

    steps = {}
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        from scripts.liquidity_monitor.fred_fetch import run as fred_run
        fred_run()
        steps["fred"] = "success"
    except Exception as e:
        steps["fred"] = f"skipped: {e}"

    try:
        from scripts.liquidity_monitor.price_fetch import run as price_run
        price_run()
        steps["price"] = "success"
    except Exception as e:
        steps["price"] = f"skipped: {e}"

    try:
        from scripts.liquidity_monitor.news_fetch import run as news_run
        news_run()
        steps["news"] = "success"
    except Exception as e:
        steps["news"] = f"skipped: {e}"

    try:
        from scripts.liquidity_monitor.fed_speech_fetch import run as fed_run
        fed_run()
        steps["fed_tone"] = "success"
    except Exception as e:
        steps["fed_tone"] = f"skipped: {e}"

    try:
        from scripts.liquidity_monitor.stress_calculator import calculate
        calculate(today)
        steps["stress_calc"] = "success"
    except Exception as e:
        steps["stress_calc"] = f"skipped: {e}"

    sys.path = original_path
    # config 복원
    if old_config is not None:
        sys.modules['config'] = old_config
    else:
        sys.modules.pop('config', None)

    elapsed = time.time() - start
    ok_count = sum(1 for v in steps.values() if v == "success")
    status = "success" if ok_count == 5 else ("partial" if ok_count > 0 else "failed")

    _log_collection("liquidity", status, elapsed, steps, "api")

    return {
        "collector": "liquidity",
        "status": status,
        "duration": round(elapsed, 1),
        "date": today,
        "steps": steps,
    }


def _run_crypto_collector() -> dict:
    """크립토 데이터 수집 (run_crypto.py 래핑)."""
    crypto_dir = os.path.join(_scripts_root, 'scripts', 'crypto_monitor')

    # crypto config를 올바른 경로에서 로드
    config_path = os.path.join(crypto_dir, 'config.py')
    crypto_config = _load_module_from_file('config', config_path)
    old_config = sys.modules.get('config')
    sys.modules['config'] = crypto_config

    original_path = sys.path[:]
    sys.path.insert(0, crypto_dir)
    sys.path.insert(0, _scripts_root)

    # 기존 crypto 모듈 캐시 제거
    mods_to_remove = [k for k in sys.modules if k.startswith('scripts.crypto_monitor.') or
                      k in ('coingecko_fetch', 'defi_fetch', 'fear_greed_fetch', 'run_crypto')]
    for k in mods_to_remove:
        del sys.modules[k]

    try:
        from scripts.crypto_monitor.run_crypto import run as crypto_run
        result = crypto_run()
    except Exception as e:
        result = {"collector": "crypto", "status": "failed", "duration": 0, "date": "", "steps": {"error": str(e)}}
    finally:
        sys.path = original_path
        if old_config is not None:
            sys.modules['config'] = old_config
        else:
            sys.modules.pop('config', None)

    _log_collection("crypto", result["status"], result.get("duration", 0), result.get("steps", {}), "api")
    return result


def _run_all_collectors() -> dict:
    """순차 수집: 유동성 → 크립토."""
    start = time.time()
    results = []

    result_liq = _run_liquidity_collector()
    results.append(result_liq)

    result_crypto = _run_crypto_collector()
    results.append(result_crypto)

    total = time.time() - start
    all_ok = all(r["status"] == "success" for r in results)
    any_ok = any(r["status"] != "failed" for r in results)

    return {
        "status": "success" if all_ok else ("partial" if any_ok else "failed"),
        "total_duration": round(total, 1),
        "collectors": results,
    }


@router.post("/liquidity")
async def collect_liquidity():
    """유동성 스트레스 데이터 수집 트리거."""
    try:
        result = await asyncio.to_thread(_run_liquidity_collector)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crypto")
async def collect_crypto():
    """크립토 데이터 수집 트리거."""
    try:
        result = await asyncio.to_thread(_run_crypto_collector)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-all")
async def collect_all():
    """전체 순차 수집: 유동성 → 크립토."""
    try:
        result = await asyncio.to_thread(_run_all_collectors)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_table_counts() -> dict:
    """주요 DB 테이블별 row count 조회."""
    import sqlite3
    counts = {}
    tables = [
        "liquidity_macro", "liquidity_price", "liquidity_news", "fed_tone", "stress_index",
        "crypto_price", "crypto_defi", "crypto_sentiment",
        "disclosures", "moat_evaluations",
        "daily_work", "insights", "ideas",
        "naver_blog_data", "news_analysis",
    ]
    try:
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.cursor()
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM [{t}]")
                counts[t] = cur.fetchone()[0]
            except Exception:
                counts[t] = 0
        conn.close()
    except Exception:
        pass
    return counts


@router.get("/status")
async def get_collector_status():
    """각 수집기 최근 실행 상태 + 테이블 건수 조회."""
    try:
        from sqlalchemy import create_engine, desc
        from sqlalchemy.orm import sessionmaker
        from backend.app.models.crypto import CollectorLog

        engine = create_engine(f'sqlite:///{_DB_PATH}')
        CollectorLog.__table__.create(engine, checkfirst=True)
        Session = sessionmaker(bind=engine)
        db = Session()

        collectors = {}
        for name in ["liquidity", "crypto", "news", "disclosure", "moat", "idea"]:
            row = db.query(CollectorLog).filter_by(collector=name).order_by(desc(CollectorLog.created_at)).first()
            if row:
                collectors[name] = {
                    "date": row.date,
                    "status": row.status,
                    "duration": row.duration,
                    "triggered_by": row.triggered_by,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
            else:
                collectors[name] = None

        db.close()

        table_counts = _get_table_counts()

        return {"collectors": collectors, "table_counts": table_counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
