"""
Data Gap Analyzer — 데이터 갭 분석 + 외부 소스 추천
시그널의 신뢰도를 높일 수 있는 누락/오래된 데이터를 탐지하고
외부 데이터 소스를 추천합니다.
"""
import os
import json
from datetime import datetime
from typing import Optional

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class GapAnalyzer:
    """데이터 갭 분석 + 외부 소스 추천"""

    def __init__(self):
        self.external_sources = self._load_external_sources()

    def _load_external_sources(self) -> list:
        """data/external_sources.json 로드"""
        path = os.path.join(_PROJECT_ROOT, "data", "external_sources.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("sources", [])
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return []

    def analyze(self, signal: dict, context: dict) -> dict:
        """
        시그널 + 컨텍스트를 분석하여 데이터 갭과 외부 소스 추천을 반환.
        Returns: {
            gaps: [{module, reason, impact, staleness_hours}],
            recommendations: [{source_id, name, synergy, confidence_boost, integration, url}],
            enrichments: [{source_id, name, synergy, benefit}]
        }
        """
        gaps = []
        recommendations = []

        # 1) 시그널에 사용된 모듈 중 데이터 없거나 오래된 것 탐지
        evidence = signal.get("evidence", [])
        checked_modules = set()

        for ev in evidence:
            module = ev["module"]
            if module in checked_modules:
                continue
            checked_modules.add(module)

            module_data = context.get(module, {})
            if not module_data or module_data.get("available") is False:
                gaps.append({
                    "module": module,
                    "reason": f"{module} 데이터 없음",
                    "impact": "시그널 신뢰도 저하",
                    "staleness_hours": None,
                })
            else:
                last_updated = module_data.get("generated_at") or module_data.get("date")
                if last_updated:
                    hours_old = self._hours_since(last_updated)
                    if hours_old and hours_old > 24:
                        gaps.append({
                            "module": module,
                            "reason": f"{module} 데이터 {hours_old:.0f}시간 경과",
                            "impact": "최신 상황 미반영 가능",
                            "staleness_hours": round(hours_old, 1),
                        })

        # 2) 시그널에 참여하지 않았지만 관련 있을 수 있는 모듈 확인
        all_modules = ["liquidity_stress", "sector_momentum", "daily_work",
                       "crypto_trends", "disclosures", "events"]
        for mod in all_modules:
            if mod in checked_modules:
                continue
            mod_data = context.get(mod, {})
            if not mod_data or mod_data.get("available") is False:
                gaps.append({
                    "module": mod,
                    "reason": f"{mod} 데이터 미수집",
                    "impact": "추가 교차 검증 불가",
                    "staleness_hours": None,
                })

        # 3) 시그널 카테고리에 맞는 외부 소스 추천
        for source in self.external_sources:
            if source.get("connected"):
                continue  # 이미 연동된 소스는 제외
            src_cat = source.get("category", "")
            if src_cat == signal.get("category") or src_cat == "ALL":
                recommendations.append({
                    "source_id": source["id"],
                    "name": source["name"],
                    "synergy": source.get("synergy", ""),
                    "confidence_boost": source.get("confidence_boost", "+10%"),
                    "integration": source.get("integration_script") or "manual",
                    "url": source.get("url"),
                })

        # 4) 시그널을 강화할 추가 데이터 소스
        enrichments = self._find_enrichment_sources(signal, context)

        return {
            "gaps": gaps,
            "recommendations": recommendations,
            "enrichments": enrichments,
        }

    def _find_enrichment_sources(self, signal: dict, context: dict) -> list:
        """시그널 강화를 위한 추가 데이터 소스 (연동 여부 무관)"""
        enrichments = []
        category = signal.get("category", "")

        # 카테고리별 강화 데이터
        if category == "RISK":
            enrichments.append({
                "source_id": "fred-credit-spread",
                "name": "FRED 신용스프레드",
                "synergy": "신용 리스크 추가 확인으로 시그널 정밀도 향상",
                "benefit": "confidence +10~15%",
            })
        elif category == "SECTOR":
            enrichments.append({
                "source_id": "sector-earnings",
                "name": "섹터별 실적 캘린더",
                "synergy": "실적 시즌과 로테이션 타이밍 교차 검증",
                "benefit": "타이밍 정밀도 향상",
            })
        elif category == "PORTFOLIO":
            enrichments.append({
                "source_id": "dart-disclosure",
                "name": "DART 전자공시 실시간",
                "synergy": "보유종목 이벤트 실시간 알림",
                "benefit": "리스크 조기 감지",
            })

        return enrichments

    def _hours_since(self, timestamp_str: str) -> Optional[float]:
        """타임스탬프로부터 경과 시간(시) 계산"""
        try:
            if "T" in timestamp_str:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.utcnow()
            else:
                ts = datetime.strptime(timestamp_str, "%Y-%m-%d")
                now = datetime.utcnow()
            delta = now - ts.replace(tzinfo=None)
            return delta.total_seconds() / 3600
        except (ValueError, TypeError):
            return None
