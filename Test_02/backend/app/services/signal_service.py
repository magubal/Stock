"""
Signal Detection Engine — 규칙 기반 Cross-Data 시그널 탐지
data/signal_rules.json의 규칙을 CrossModuleService 컨텍스트에 적용하여
투자 시그널을 자동 생성합니다.
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from ..models.signal import Signal
from ..models.idea import Idea
from .cross_module_service import CrossModuleService

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# ── Module Data Extractors ──
# CrossModuleService 컨텍스트를 규칙 엔진이 이해하는 flat key-value로 변환

def _calc_defensive_trend(sector_data: dict) -> Optional[str]:
    """방어주(Utilities, Healthcare, Consumer Staples) 트렌드 판단"""
    sectors = sector_data.get("sectors", {})
    defensive_symbols = ["XLU", "XLV", "XLP"]
    up_count = 0
    for sym in defensive_symbols:
        info = sectors.get(sym, {})
        trend = info.get("trend", "")
        if trend in ("up", "strong_up"):
            up_count += 1
    if up_count >= 2:
        return "up"
    return "flat"


def _calc_rotation(sector_data: dict) -> Optional[str]:
    """섹터 로테이션 시그널: 상위/하위 섹터 격차가 클 때"""
    sectors = sector_data.get("sectors", {})
    if not sectors:
        return None
    changes = []
    for sym, info in sectors.items():
        pct = info.get("change_pct")
        if pct is not None:
            changes.append((sym, pct))
    if len(changes) < 4:
        return None
    changes.sort(key=lambda x: x[1], reverse=True)
    top_avg = sum(c[1] for _, c in zip(range(3), changes)) / 3
    bot_avg = sum(c[1] for _, c in zip(range(3), reversed(changes))) / 3
    if top_avg - bot_avg > 5:
        return f"{changes[0][0]}→{changes[-1][0]}"
    return None


def _calc_top_pct(sector_data: dict) -> Optional[float]:
    """최고 성과 ETF의 변동률"""
    sectors = sector_data.get("sectors", {})
    if not sectors:
        return None
    best = max(
        (info.get("change_pct", 0) for info in sectors.values()),
        default=0,
    )
    return best


def _count_portfolio_ideas(ideas_data: dict) -> int:
    """PORTFOLIO 카테고리 활성 아이디어 수"""
    recent = ideas_data.get("recent_active", [])
    return sum(1 for i in recent if i.get("category") == "PORTFOLIO")


def _count_high_impact(events_data: dict) -> int:
    """고임팩트 이벤트 수"""
    next_7 = events_data.get("next_7_days", [])
    return sum(1 for e in next_7 if e.get("impact") in ("high", "critical"))


def _days_to_next(events_data: dict) -> Optional[int]:
    """다음 이벤트까지 남은 일수"""
    next_7 = events_data.get("next_7_days", [])
    if not next_7:
        return None
    try:
        next_date = datetime.fromisoformat(next_7[0]["date"])
        return (next_date.date() - datetime.utcnow().date()).days
    except (KeyError, ValueError):
        return None


def _get_crypto_data(ctx: dict) -> dict:
    """크립토 트렌드 데이터 추출 (파일 기반)"""
    crypto = ctx.get("crypto_trends", {})
    if crypto:
        return crypto
    # crypto_trends.json 파일에서 직접 로드 시도
    cache_path = os.path.join(_PROJECT_ROOT, "data", "crypto_trends.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


MODULE_EXTRACTORS = {
    "liquidity_stress": lambda ctx: {
        "total_score": ctx.get("liquidity_stress", {}).get("total_score"),
        "level": ctx.get("liquidity_stress", {}).get("level"),
        "vix": ctx.get("liquidity_stress", {}).get("vix"),
        "change_1d": ctx.get("liquidity_stress", {}).get("change_1d"),
    },
    "sector_momentum": lambda ctx: {
        "defensive_trend": _calc_defensive_trend(ctx.get("sector_momentum", {})),
        "rotation_signal": _calc_rotation(ctx.get("sector_momentum", {})),
        "top_performer_pct": _calc_top_pct(ctx.get("sector_momentum", {})),
    },
    "daily_work": lambda ctx: {
        "has_recent": ctx.get("daily_work", {}).get("available", False),
        "categories": list(ctx.get("daily_work", {}).get("categories", {}).keys()),
        "count": ctx.get("daily_work", {}).get("total_items", 0),
    },
    "crypto_trends": lambda ctx: {
        "btc_7d_change": _get_crypto_data(ctx).get("btc_7d_change"),
        "fear_greed": _get_crypto_data(ctx).get("fear_greed_value"),
    },
    "disclosures": lambda ctx: {
        "risk_count": _count_risk_disclosures(ctx.get("disclosures", {})),
        "total_count": ctx.get("disclosures", {}).get("total_count", 0),
    },
    "ideas_status": lambda ctx: {
        "active_portfolio_ideas": _count_portfolio_ideas(ctx.get("ideas_status", {})),
        "active_count": sum(ctx.get("ideas_status", {}).get("by_status", {}).values()) if ctx.get("ideas_status", {}).get("by_status") else 0,
    },
    "events": lambda ctx: {
        "upcoming_high_impact": _count_high_impact(ctx.get("events", {})),
        "next_event_days": _days_to_next(ctx.get("events", {})),
    },
}


def _count_risk_disclosures(disc_data: dict) -> int:
    """리스크 관련 공시 건수 (유상증자, 전환사채 등)"""
    notable = disc_data.get("notable_items", [])
    risk_keywords = ["유상증자", "전환사채", "감자", "상장폐지", "횡령", "소송"]
    count = 0
    for item in notable:
        title = item.get("title", "")
        if any(kw in title for kw in risk_keywords):
            count += 1
    return count


class SignalDetectionEngine:
    """규칙 기반 시그널 탐지 엔진"""

    def __init__(self, db: Session):
        self.db = db
        self.rules = self._load_rules()
        self.cross_module = CrossModuleService(db)

    def _load_rules(self) -> list:
        """data/signal_rules.json 로드"""
        rules_path = os.path.join(_PROJECT_ROOT, "data", "signal_rules.json")
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("rules", [])
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

    def generate_signals(self, days: int = 3) -> list[dict]:
        """
        1) CrossModuleService에서 전체 컨텍스트 수집
        2) MODULE_EXTRACTORS로 flat data 변환
        3) 각 규칙의 conditions 평가
        4) min_conditions 이상 매치되면 Signal 생성
        5) DB 저장 + 결과 반환
        """
        context = self.cross_module.get_full_context(days)
        extracted = self._extract_module_data(context)
        signals = []

        for rule in self.rules:
            matched_conditions = []
            evidence_items = []

            for cond in rule["conditions"]:
                module_data = extracted.get(cond["module"], {})

                # category_filter 처리: daily_work에서 특정 카테고리만 확인
                if cond.get("category_filter"):
                    categories = module_data.get("categories", [])
                    if cond["category_filter"] not in categories:
                        continue

                if self._evaluate_condition(cond, module_data):
                    matched_conditions.append(cond)
                    evidence_items.append({
                        "module": cond["module"],
                        "field": cond["field"],
                        "value": module_data.get(cond["field"]),
                        "label": cond["label"],
                        "timestamp": context.get("generated_at"),
                    })

            if len(matched_conditions) >= rule["min_conditions"]:
                confidence = min(1.0,
                    rule["confidence_base"]
                    + (len(matched_conditions) - rule["min_conditions"])
                    * rule.get("confidence_boost_per_extra", 0.1)
                )
                signal = self._create_signal(rule, confidence, evidence_items)
                signals.append(signal)

        return signals

    def _extract_module_data(self, context: dict) -> dict:
        """컨텍스트를 모듈별 flat dict로 변환"""
        result = {}
        for module_name, extractor in MODULE_EXTRACTORS.items():
            try:
                result[module_name] = extractor(context)
            except Exception:
                result[module_name] = {}
        return result

    def _evaluate_condition(self, cond: dict, module_data: dict) -> bool:
        """단일 조건 평가"""
        value = module_data.get(cond["field"])
        if value is None:
            return False
        op = cond["operator"]
        target = cond["value"]
        if op == ">":
            return value > target
        if op == "<":
            return value < target
        if op == "==":
            return value == target
        if op == "!=":
            return value != target
        if op == ">=":
            return value >= target
        if op == "<=":
            return value <= target
        if op == "in":
            return value in target
        if op == "contains":
            return target in value if isinstance(value, (str, list)) else False
        return False

    def _create_signal(self, rule: dict, confidence: float, evidence: list) -> dict:
        """Signal 레코드 생성 + DB 저장"""
        now = datetime.utcnow()
        date_str = now.strftime("%Y%m%d")

        # 같은 rule, 같은 날짜 기존 시그널 확인 (중복 방지)
        existing = (
            self.db.query(Signal)
            .filter(Signal.rule_id == rule["id"])
            .filter(Signal.signal_id.like(f"{rule['id']}-{date_str}%"))
            .filter(Signal.status.in_(["new", "reviewed"]))
            .first()
        )
        if existing:
            # 기존 시그널 confidence 업데이트
            existing.confidence = confidence
            existing.evidence = json.dumps(evidence, ensure_ascii=False)
            self.db.commit()
            self.db.refresh(existing)
            return self._signal_to_dict(existing)

        # 시퀀스 번호
        count = (
            self.db.query(Signal)
            .filter(Signal.signal_id.like(f"{rule['id']}-{date_str}%"))
            .count()
        )
        seq = str(count + 1).zfill(3)
        signal_id = f"{rule['id']}-{date_str}-{seq}"

        data_sources = list(set(e["module"] for e in evidence))
        expires_at = now + timedelta(hours=rule.get("expires_hours", 48))

        db_signal = Signal(
            signal_id=signal_id,
            rule_id=rule["id"],
            title=rule["title"],
            description=rule.get("description"),
            category=rule["category"],
            signal_type="cross",
            confidence=round(confidence, 3),
            data_sources=json.dumps(data_sources, ensure_ascii=False),
            evidence=json.dumps(evidence, ensure_ascii=False),
            suggested_action=rule.get("suggested_action"),
            status="new",
            expires_at=expires_at,
        )
        self.db.add(db_signal)
        self.db.commit()
        self.db.refresh(db_signal)

        return self._signal_to_dict(db_signal)

    def accept_signal(self, signal_id: int) -> Optional[dict]:
        """시그널 채택 → Idea 자동 생성"""
        signal = self.db.query(Signal).filter(Signal.id == signal_id).first()
        if not signal:
            return None

        # Idea 생성
        evidence = json.loads(signal.evidence) if signal.evidence else []
        evidence_summary = ", ".join(
            f"{e['label']}: {e['value']}" for e in evidence
        )
        idea = Idea(
            title=f"{signal.title} — {evidence_summary[:100]}",
            content=f"시그널 기반 자동 생성\n\n근거: {evidence_summary}\n\n제안: {signal.suggested_action or ''}",
            source=f"Signal:{signal.signal_id}",
            category=signal.category,
            thesis=signal.suggested_action,
            status="draft",
            priority=2 if signal.confidence >= 0.7 else 3,
        )
        self.db.add(idea)

        # 시그널 상태 업데이트
        signal.status = "accepted"
        signal.reviewed_at = datetime.utcnow()
        signal.related_idea_id = idea.id

        self.db.commit()
        self.db.refresh(idea)
        self.db.refresh(signal)

        # related_idea_id 업데이트 (commit 후 idea.id 확정)
        signal.related_idea_id = idea.id
        self.db.commit()

        return {
            "signal_id": signal.signal_id,
            "status": "accepted",
            "idea": {
                "id": idea.id,
                "title": idea.title,
                "category": idea.category,
                "status": idea.status,
                "source": idea.source,
            },
        }

    @staticmethod
    def _signal_to_dict(signal: Signal) -> dict:
        """Signal ORM → dict 변환"""
        return {
            "id": signal.id,
            "signal_id": signal.signal_id,
            "rule_id": signal.rule_id,
            "title": signal.title,
            "description": signal.description,
            "category": signal.category,
            "signal_type": signal.signal_type,
            "confidence": signal.confidence,
            "data_sources": json.loads(signal.data_sources) if signal.data_sources else [],
            "evidence": json.loads(signal.evidence) if signal.evidence else [],
            "suggested_action": signal.suggested_action,
            "ai_interpretation": signal.ai_interpretation,
            "data_gaps": json.loads(signal.data_gaps) if signal.data_gaps else [],
            "status": signal.status,
            "related_idea_id": signal.related_idea_id,
            "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
            "reviewed_at": signal.reviewed_at.isoformat() if signal.reviewed_at else None,
        }
