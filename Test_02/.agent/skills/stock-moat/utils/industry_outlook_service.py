"""Industry outlook service with TTL-based reuse."""

from datetime import date, timedelta
from typing import Dict, List, Optional


class IndustryOutlookService:
    def __init__(self, repository, ttl_days: int = 30):
        self.repository = repository
        self.ttl_days = ttl_days

    def get_or_build(self, classification: Dict, as_of_date: str) -> Dict:
        sector_top = classification.get("korean_sector_top", "Unknown")
        sector_sub = classification.get("korean_sector_sub", "Unknown")
        gics_sector = classification.get("gics_sector", "Unknown")
        gics_industry = classification.get("gics_industry", "Unknown")
        sector_key = f"{gics_sector}|{gics_industry}"

        latest = self.repository.get_latest_outlook(sector_key)
        if latest and self._is_valid(latest.get("valid_until"), as_of_date):
            latest["reused"] = True
            latest["freshness_days"] = self._freshness_days(latest.get("as_of_date"), as_of_date)
            return latest

        generated = self._generate_outlook(sector_top, sector_sub, gics_sector, gics_industry, as_of_date)
        self.repository.save_outlook(
            sector_key=sector_key,
            sector_top=sector_top,
            sector_sub=sector_sub,
            summary=generated["summary"],
            key_factors=generated["key_factors"],
            source=generated["source"],
            confidence=generated["confidence"],
            as_of_date=generated["as_of_date"],
            valid_until=generated["valid_until"],
        )

        generated.update(
            {
                "sector_key": sector_key,
                "sector_top": sector_top,
                "sector_sub": sector_sub,
                "reused": False,
                "freshness_days": 0,
            }
        )
        return generated

    def _generate_outlook(
        self,
        sector_top: str,
        sector_sub: str,
        gics_sector: str,
        gics_industry: str,
        as_of_date: str,
    ) -> Dict:
        key_factors = self._sector_factor_map(sector_top, sector_sub)
        summary = (
            f"{sector_top}/{sector_sub} 업황 핵심요소: "
            f"{', '.join(key_factors[:4])}. "
            f"GICS {gics_sector}/{gics_industry} 기준으로 최근 모멘텀, 비용구조, 수요 지속성을 우선 점검."
        )
        valid_until = (date.fromisoformat(as_of_date) + timedelta(days=self.ttl_days)).isoformat()

        return {
            "summary": summary,
            "key_factors": key_factors,
            "source": "generated_research",
            "confidence": "medium",
            "as_of_date": as_of_date,
            "valid_until": valid_until,
        }

    def _sector_factor_map(self, sector_top: str, sector_sub: str) -> List[str]:
        title = f"{sector_top} {sector_sub}"
        if "반도체" in title:
            return [
                "메모리/비메모리 ASP 추이",
                "고객사 재고일수",
                "CAPEX 사이클",
                "AI/데이터센터 수요",
                "환율과 원가 구조",
                "경쟁사 증설/감산",
            ]
        if "금융" in title:
            return [
                "순이자마진(NIM)",
                "대손비용률",
                "대출성장률",
                "건전성 지표",
                "규제 변화",
                "자본정책",
            ]
        if "바이오" in title or "헬스" in title:
            return [
                "파이프라인 임상 단계",
                "허가 일정",
                "약가/상환 정책",
                "생산수율",
                "파트너십",
                "현금 소진 속도",
            ]
        if "에너지" in title or "화학" in title:
            return [
                "원재료 스프레드",
                "가동률",
                "재고/공급 밸런스",
                "정책/규제",
                "수출단가",
                "환율 영향",
            ]
        return [
            "수요 성장률",
            "가격 전가력",
            "원가 구조",
            "경쟁 강도",
            "규제/정책",
            "자본투자 부담",
        ]

    @staticmethod
    def _is_valid(valid_until: Optional[str], as_of_date: str) -> bool:
        if not valid_until:
            return False
        try:
            return date.fromisoformat(valid_until) >= date.fromisoformat(as_of_date)
        except Exception:
            return False

    @staticmethod
    def _freshness_days(saved_as_of: Optional[str], as_of_date: str) -> int:
        if not saved_as_of:
            return 0
        try:
            return max((date.fromisoformat(as_of_date) - date.fromisoformat(saved_as_of)).days, 0)
        except Exception:
            return 0
