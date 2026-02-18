"""
AI 투자전략가 서비스 — 시그널을 투자 관점으로 해석
Claude Sonnet API를 사용하여 시그널의 투자적 의미를 분석합니다.
ANTHROPIC_API_KEY가 없으면 해석 없이 동작합니다.
"""
import os
import json
from typing import Optional


class StrategistService:
    """AI 투자전략가: 시그널을 투자 관점으로 해석"""

    def __init__(self, api_key: str = None):
        self.client = None
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=key)
            except ImportError:
                pass

    @property
    def available(self) -> bool:
        return self.client is not None

    def interpret_signal(self, signal: dict, context: dict) -> dict:
        """
        시그널 + 컨텍스트 → AI 투자 해석
        Returns: {interpretation, hypothesis, actions[], risk_factors[], confidence_adjustment}
        """
        if not self.client:
            return {
                "interpretation": None,
                "hypothesis": None,
                "actions": [],
                "risk_factors": [],
                "confidence_adjustment": 0.0,
                "reason": "ANTHROPIC_API_KEY not configured",
            }

        prompt = f"""당신은 한국 주식시장 전문 투자전략가입니다.

다음 투자 시그널을 분석하고 투자 관점에서 해석해주세요.

## 시그널
- 제목: {signal.get('title', '')}
- 카테고리: {signal.get('category', '')}
- 신뢰도: {signal.get('confidence', 0):.0%}
- 근거 데이터: {json.dumps(signal.get('evidence', []), ensure_ascii=False)}
- 제안 행동: {signal.get('suggested_action', '')}

## 현재 시장 컨텍스트 요약
{self._summarize_context(context)}

다음 형식으로 JSON 응답해주세요:
{{
  "interpretation": "시그널의 투자적 의미 해석 (2-3문장)",
  "hypothesis": "이 시그널이 맞다면 예상되는 시장 시나리오",
  "actions": ["구체적 행동 1", "구체적 행동 2"],
  "risk_factors": ["리스크 1", "리스크 2"],
  "confidence_adjustment": 0.0
}}

confidence_adjustment는 -0.2 ~ +0.2 범위로, AI가 데이터 품질/맥락 판단하여 confidence를 조정합니다.
JSON만 응답하세요."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return self._parse_response(response)
        except Exception as e:
            return {
                "interpretation": None,
                "hypothesis": None,
                "actions": [],
                "risk_factors": [],
                "confidence_adjustment": 0.0,
                "reason": f"API error: {str(e)}",
            }

    def _summarize_context(self, context: dict) -> str:
        """컨텍스트를 간략한 텍스트로 요약"""
        parts = []

        liq = context.get("liquidity_stress", {})
        if liq.get("available"):
            parts.append(f"유동성 스트레스: {liq.get('total_score', 'N/A')} ({liq.get('level', 'N/A')})")
            if liq.get("vix"):
                parts.append(f"VIX: {liq['vix']}")

        sector = context.get("sector_momentum", {})
        if sector.get("available"):
            up = sector.get("strong_uptrend", [])
            down = sector.get("strong_downtrend", [])
            if up:
                parts.append(f"섹터 강세: {', '.join(up[:3])}")
            if down:
                parts.append(f"섹터 약세: {', '.join(down[:3])}")

        events = context.get("events", {})
        if events.get("available"):
            next_7 = events.get("next_7_days", [])
            if next_7:
                parts.append(f"7일내 이벤트 {len(next_7)}건")

        ideas = context.get("ideas_status", {})
        if ideas.get("total"):
            parts.append(f"활성 아이디어 {ideas['total']}건")

        return "\n".join(parts) if parts else "컨텍스트 데이터 부족"

    def _parse_response(self, response) -> dict:
        """Claude API 응답 파싱"""
        try:
            text = response.content[0].text.strip()
            # JSON 블록 추출
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            result = json.loads(text)
            # confidence_adjustment 범위 제한
            adj = result.get("confidence_adjustment", 0.0)
            result["confidence_adjustment"] = max(-0.2, min(0.2, adj))
            return result
        except (json.JSONDecodeError, IndexError, KeyError):
            return {
                "interpretation": response.content[0].text[:500] if response.content else None,
                "hypothesis": None,
                "actions": [],
                "risk_factors": [],
                "confidence_adjustment": 0.0,
            }
