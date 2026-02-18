"""
Cross-Module Context Service
모든 모듈 데이터를 하나의 구조화된 브리핑으로 집계합니다.
AI(Claude/Gemini/ChatGPT)가 이 브리핑을 기반으로 투자 아이디어를 생성합니다.
"""
import os
import json
import glob
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from ..models import (
    StressIndex, LiquidityPrice, LiquidityNews, FedTone, LiquidityMacro,
)
from ..models.idea import Idea
from ..models.daily_work import DailyWork
from ..models.insight import Insight
from ..models.collab import CollabPacket

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class CrossModuleService:
    def __init__(self, db: Session):
        self.db = db

    def get_full_context(self, days: int = 3) -> dict:
        """모든 모듈 데이터를 하나의 브리핑으로 집계.

        기본 모듈 외에 data/custom_sources/*.json 에 놓인 파일도 자동 포함합니다.
        커스텀 소스 JSON 형식:
          {"name": "소스 이름", "description": "설명", "data": {...}}
        """
        ctx = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "period_days": days,
            "liquidity_stress": self._get_liquidity(),
            "disclosures": self._get_disclosures(),
            "daily_work": self._get_daily_work(days),
            "events": self._get_upcoming_events(),
            "sector_momentum": self._get_sector_momentum(),
            "ideas_status": self._get_ideas_summary(),
            "collab_status": self._get_collab_summary(),
        }
        # 커스텀 데이터 소스 자동 로드
        custom = self._get_custom_sources()
        if custom:
            ctx["custom_sources"] = custom
        return ctx

    def _get_liquidity(self) -> dict:
        """최신 유동성 스트레스 요약"""
        si = self.db.query(StressIndex).order_by(desc(StressIndex.date)).first()
        if not si:
            return {"available": False}

        prev = (
            self.db.query(StressIndex)
            .filter(StressIndex.date < si.date)
            .order_by(desc(StressIndex.date))
            .first()
        )

        # VIX 현재값
        vix = self.db.query(LiquidityPrice).filter_by(date=si.date, symbol="^VIX").first()

        # 뉴스 집계
        news_rows = self.db.query(LiquidityNews).filter_by(date=si.date).all()
        top_kw = max(news_rows, key=lambda n: n.count).keyword if news_rows else None

        return {
            "available": True,
            "date": si.date,
            "total_score": round(si.total_score or 0, 3),
            "level": si.level or "normal",
            "change_1d": round((si.total_score or 0) - (prev.total_score or 0), 3) if prev else None,
            "modules": {
                "volatility": round(si.vol_score or 0, 3),
                "credit": round(si.credit_score or 0, 3),
                "funding": round(si.funding_score or 0, 3),
                "treasury": round(si.treasury_score or 0, 3),
                "news": round(si.news_score or 0, 3),
                "fed_tone": round(si.fed_tone_score or 0, 3),
            },
            "vix": vix.close if vix else None,
            "top_news_keyword": top_kw,
            "interpretation": self._interpret_stress(si),
        }

    def _interpret_stress(self, si) -> str:
        """스트레스 수준에 대한 간단한 해석"""
        level = si.level or "normal"
        score = si.total_score or 0
        if level == "crisis":
            return f"위기 수준 ({score:.2f}). 극도의 시장 스트레스. 방어적 포지션 필수."
        elif level == "stress":
            return f"경계 수준 ({score:.2f}). 유동성 악화 신호. 리스크 축소 고려."
        elif level == "caution":
            return f"주의 수준 ({score:.2f}). 일부 지표 악화. 모니터링 강화."
        elif level == "watch":
            return f"관심 수준 ({score:.2f}). 약간의 긴장. 선제적 대응 준비."
        else:
            return f"안정 수준 ({score:.2f}). 정상 유동성. 적극적 투자 가능."

    def _get_disclosures(self) -> dict:
        """최신 공시 요약"""
        disc_dir = os.path.join(_PROJECT_ROOT, "data", "disclosures")
        if not os.path.isdir(disc_dir):
            return {"available": False, "items": []}

        # 가장 최신 날짜 파일 찾기
        json_files = sorted(glob.glob(os.path.join(disc_dir, "20*.json")), reverse=True)
        if not json_files:
            return {"available": False, "items": []}

        latest_file = json_files[0]
        date_str = os.path.basename(latest_file).replace(".json", "")

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                items = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"available": False, "items": []}

        # 유형별 집계
        type_count = {}
        for item in items:
            t = item.get("title", "기타")
            type_count[t] = type_count.get(t, 0) + 1

        # 주요 공시 (실적, 계약, 자사주, 유상증자 등)
        key_types = ["영업(잠정)실적(공정공시)", "단일판매·공급계약체결",
                     "자기주식취득신탁계약체결결정", "유상증자결정", "전환사채권발행결정"]
        notable = [item for item in items if item.get("title") in key_types]

        return {
            "available": True,
            "date": date_str,
            "total_count": len(items),
            "type_summary": type_count,
            "notable_items": notable[:10],
            "companies_mentioned": list(set(item.get("company", "") for item in items)),
        }

    def _get_daily_work(self, days: int) -> dict:
        """최근 일일작업 카테고리별 요약"""
        since = date.today() - timedelta(days=days)
        items = (
            self.db.query(DailyWork)
            .filter(DailyWork.date >= since)
            .order_by(DailyWork.date.desc())
            .all()
        )
        if not items:
            return {"available": False, "categories": {}}

        by_cat = {}
        for w in items:
            cat = w.category or "UNKNOWN"
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append({
                "date": str(w.date),
                "description": (w.description or "")[:150],
                "content_preview": (w.content or "")[:300],
            })

        return {
            "available": True,
            "total_items": len(items),
            "date_range": f"{since} ~ {date.today()}",
            "categories": by_cat,
        }

    def _get_upcoming_events(self) -> dict:
        """향후 이벤트 캘린더"""
        events_path = os.path.join(_PROJECT_ROOT, "data", "market_events.json")
        if not os.path.exists(events_path):
            return {"available": False, "events": []}

        try:
            with open(events_path, "r", encoding="utf-8") as f:
                all_events = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"available": False, "events": []}

        today = date.today().isoformat()
        upcoming = [e for e in all_events if e.get("date", "") >= today]
        upcoming.sort(key=lambda e: e.get("date", ""))

        return {
            "available": True,
            "upcoming_count": len(upcoming),
            "next_7_days": [e for e in upcoming if e.get("date", "") <= (date.today() + timedelta(days=7)).isoformat()],
            "next_30_days": upcoming[:15],
        }

    def _get_sector_momentum(self) -> dict:
        """섹터 모멘텀 캐시 데이터"""
        cache_path = os.path.join(_PROJECT_ROOT, "data", "sector_momentum.json")
        if not os.path.exists(cache_path):
            return {"available": False, "sectors": {}}

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"available": False, "sectors": {}}

        sectors = data.get("sectors", {})
        # 트렌드별 분류
        strong_up = [f"{s}({v['name']})" for s, v in sectors.items() if v.get("trend") == "strong_up"]
        strong_down = [f"{s}({v['name']})" for s, v in sectors.items() if v.get("trend") == "strong_down"]

        return {
            "available": True,
            "generated_at": data.get("generated_at"),
            "sectors": sectors,
            "strong_uptrend": strong_up,
            "strong_downtrend": strong_down,
        }

    def _get_ideas_summary(self) -> dict:
        """아이디어 현황 요약"""
        status_counts = (
            self.db.query(Idea.status, func.count(Idea.id))
            .group_by(Idea.status)
            .all()
        )
        counts = {s: c for s, c in status_counts}

        recent = (
            self.db.query(Idea)
            .filter(Idea.status.in_(["draft", "active", "testing"]))
            .order_by(desc(Idea.created_at))
            .limit(5)
            .all()
        )
        recent_list = [{
            "id": i.id,
            "title": i.title,
            "category": i.category,
            "status": i.status,
            "thesis": (i.thesis or "")[:200],
        } for i in recent]

        return {
            "total": sum(counts.values()),
            "by_status": counts,
            "recent_active": recent_list,
        }

    def _get_custom_sources(self) -> dict:
        """data/custom_sources/*.json 자동 로드.

        사용자가 새 데이터 소스를 추가하려면:
        1. data/custom_sources/ 디렉토리에 JSON 파일 생성
        2. 형식: {"name": "소스 이름", "description": "설명", "data": {...실제 데이터...}}
        3. 서버 재시작 없이 자동 반영됨
        """
        custom_dir = os.path.join(_PROJECT_ROOT, "data", "custom_sources")
        if not os.path.isdir(custom_dir):
            return {}

        result = {}
        for fpath in glob.glob(os.path.join(custom_dir, "*.json")):
            key = os.path.basename(fpath).replace(".json", "")
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                result[key] = {
                    "available": True,
                    "name": data.get("name", key),
                    "description": data.get("description", ""),
                    "data": data.get("data", data),
                }
            except (json.JSONDecodeError, IOError):
                result[key] = {"available": False, "error": "JSON parse error"}
        return result

    def _get_collab_summary(self) -> dict:
        """AI 협업 상태 요약"""
        pending = self.db.query(CollabPacket).filter_by(status="pending").count()
        recent = (
            self.db.query(CollabPacket)
            .order_by(desc(CollabPacket.created_at))
            .limit(3)
            .all()
        )
        recent_list = [{
            "packet_id": p.packet_id,
            "source_ai": p.source_ai,
            "topic": p.topic,
            "status": p.status,
        } for p in recent]

        return {
            "pending_count": pending,
            "recent_packets": recent_list,
        }
