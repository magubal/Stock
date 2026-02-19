"""
Crypto Data API - 크립토 데이터 조회 엔드포인트
GET /api/v1/crypto/latest   - 최신 코인 가격 + 시장 지표
GET /api/v1/crypto/history   - 최근 N일 히스토리
"""
import os
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/v1/crypto", tags=["crypto"])

_scripts_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
_DB_PATH = os.path.join(_scripts_root, 'backend', 'stock_research.db')


@router.get("/latest")
async def get_latest_crypto():
    """최신 크립토 데이터: 코인 가격 + 시장 지표."""
    try:
        from sqlalchemy import create_engine, desc
        from sqlalchemy.orm import sessionmaker
        from backend.app.models.crypto import CryptoPrice, CryptoMetric

        engine = create_engine(f'sqlite:///{_DB_PATH}')
        Session = sessionmaker(bind=engine)
        db = Session()

        # 최신 metric
        metric = db.query(CryptoMetric).order_by(desc(CryptoMetric.date)).first()
        if not metric:
            db.close()
            return {"date": None, "metrics": {}, "prices": []}

        latest_date = metric.date

        # 해당 날짜 코인 가격
        prices = db.query(CryptoPrice).filter_by(date=latest_date).order_by(desc(CryptoPrice.market_cap)).all()

        result = {
            "date": latest_date,
            "metrics": {
                "total_market_cap": metric.total_market_cap,
                "total_volume_24h": metric.total_volume_24h,
                "btc_dominance": metric.btc_dominance,
                "eth_btc_ratio": metric.eth_btc_ratio,
                "fear_greed_index": metric.fear_greed_index,
                "fear_greed_label": metric.fear_greed_label,
                "defi_tvl": metric.defi_tvl,
                "stablecoin_mcap": metric.stablecoin_mcap,
            },
            "prices": [
                {
                    "coin_id": p.coin_id,
                    "symbol": p.symbol,
                    "price_usd": p.price_usd,
                    "market_cap": p.market_cap,
                    "volume_24h": p.volume_24h,
                    "change_24h": p.change_24h,
                    "change_7d": p.change_7d,
                }
                for p in prices
            ],
        }

        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_crypto_history(
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
):
    """최근 N일 크립토 시장 지표 히스토리."""
    try:
        from sqlalchemy import create_engine, desc
        from sqlalchemy.orm import sessionmaker
        from backend.app.models.crypto import CryptoMetric

        engine = create_engine(f'sqlite:///{_DB_PATH}')
        Session = sessionmaker(bind=engine)
        db = Session()

        metrics = (
            db.query(CryptoMetric)
            .order_by(desc(CryptoMetric.date))
            .limit(days)
            .all()
        )

        result = {
            "days": days,
            "count": len(metrics),
            "history": [
                {
                    "date": m.date,
                    "total_market_cap": m.total_market_cap,
                    "btc_dominance": m.btc_dominance,
                    "fear_greed_index": m.fear_greed_index,
                    "fear_greed_label": m.fear_greed_label,
                    "defi_tvl": m.defi_tvl,
                    "stablecoin_mcap": m.stablecoin_mcap,
                    "eth_btc_ratio": m.eth_btc_ratio,
                }
                for m in metrics
            ],
        }

        db.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
