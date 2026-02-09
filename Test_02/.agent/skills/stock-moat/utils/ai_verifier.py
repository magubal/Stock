"""
AI Verifier - Final quality gate using GPT-4o
Reviews all collected data from a professional investor's perspective.

Responsibilities:
1. Verify moat evaluation consistency with evidence
2. Check for overlooked risks or opportunities
3. Provide professional investor's opinion on moat strength
4. Flag any discrepancies between data and scores

Requires OPENAI_API_KEY in .env
"""

import json
import sys
import os
from typing import Dict, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class AIVerifier:
    """GPT-4o based professional investor review"""

    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_key = api_key
        self.model = "gpt-4o"
        self.enabled = bool(api_key and api_key != "your-openai-api-key-here")

    def verify(
        self,
        company_name: str,
        ticker: str,
        moat_strength: int,
        moat_desc: str,
        bm_summary: str,
        evidence_summary: str,
        sustainability_notes: str,
        classification: Dict,
        financials: Dict = None,
    ) -> Dict:
        """
        Run AI verification on moat evaluation.

        Returns: {
            'verified': bool,
            'ai_opinion': str,
            'adjusted_strength': int or None,
            'adjustment_reason': str,
            'risk_flags': [str],
            'opportunity_flags': [str],
            'confidence': float,  # 0.0-1.0
            'raw_response': str,
            'error': str or None
        }
        """
        if not self.enabled:
            return {
                'verified': False,
                'ai_opinion': 'OPENAI_API_KEY not configured',
                'adjusted_strength': None,
                'adjustment_reason': '',
                'risk_flags': [],
                'opportunity_flags': [],
                'confidence': 0.0,
                'raw_response': '',
                'error': 'API key not set'
            }

        # Build prompt
        prompt = self._build_prompt(
            company_name, ticker, moat_strength, moat_desc,
            bm_summary, evidence_summary, sustainability_notes,
            classification, financials
        )

        # Call GPT-4o
        response = self._call_openai(prompt)

        if response is None:
            return {
                'verified': False,
                'ai_opinion': 'API call failed',
                'adjusted_strength': None,
                'adjustment_reason': '',
                'risk_flags': [],
                'opportunity_flags': [],
                'confidence': 0.0,
                'raw_response': '',
                'error': 'OpenAI API call failed'
            }

        # Parse response
        return self._parse_response(response, moat_strength)

    def _build_prompt(
        self,
        company_name: str,
        ticker: str,
        moat_strength: int,
        moat_desc: str,
        bm_summary: str,
        evidence_summary: str,
        sustainability_notes: str,
        classification: Dict,
        financials: Dict = None,
    ) -> str:
        """Build the verification prompt for GPT-4o"""

        # Financial summary
        fin_text = "재무 데이터 없음"
        if financials:
            parts = []
            rev = financials.get('revenue', 0)
            if rev > 0:
                parts.append(f"매출: {rev/1_000_000_000_000:.1f}조원")
            op = financials.get('operating_margin')
            if op is not None:
                parts.append(f"영업이익률: {op:.1%}")
            roe = financials.get('roe')
            if roe is not None:
                parts.append(f"ROE: {roe:.1%}")
            dr = financials.get('debt_ratio')
            if dr is not None:
                parts.append(f"부채비율: {dr:.0%}")
            fin_text = ', '.join(parts) if parts else "재무 데이터 없음"

        sector = classification.get('korean_sector_top', '미분류')
        gics = classification.get('gics_sector', '')

        return f"""당신은 한국 주식시장 전문 투자자입니다. 아래 기업의 해자(moat) 평가 결과를 검증해주세요.

## 기업 정보
- 회사명: {company_name} ({ticker})
- 섹터: {sector} (GICS: {gics})
- 재무: {fin_text}

## 현재 해자 평가 결과
해자강도: {moat_strength}/5

### 해자 상세
{moat_desc}

### BM 분석
{bm_summary}

### 증거 요약
{evidence_summary}

### 지속가능성 검증
{sustainability_notes}

## 검증 요청
전문투자자 관점에서 아래 항목을 검증해주세요:

1. **점수 적정성**: 현재 해자강도 {moat_strength}점이 증거와 일치하는가?
   - 과대평가(증거 대비 점수가 높음) 또는 과소평가(증거 대비 점수가 낮음)?
   - 조정이 필요하면 몇 점이 적정한가?

2. **간과된 리스크**: 위 데이터에서 놓친 위험 요인이 있는가?

3. **간과된 기회**: 위 데이터에서 놓친 강점이나 기회가 있는가?

4. **최종 의견**: 전문투자자로서 이 회사의 해자에 대한 한 줄 평가

## 응답 형식 (반드시 아래 JSON 형식으로)
```json
{{
  "adjusted_strength": {moat_strength},
  "adjustment_reason": "조정 사유 (변경 없으면 빈 문자열)",
  "risk_flags": ["리스크1", "리스크2"],
  "opportunity_flags": ["기회1"],
  "opinion": "전문투자자 한 줄 평가",
  "confidence": 0.8
}}
```
"""

    def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI GPT-4o API"""
        try:
            import requests

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 한국 주식시장 전문 투자 애널리스트입니다. "
                                       "기업의 경쟁우위(해자)를 객관적으로 평가합니다. "
                                       "증거 없는 추측은 하지 않으며, 보수적으로 판단합니다. "
                                       "반드시 요청된 JSON 형식으로만 응답합니다."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=30
            )

            if response.status_code != 200:
                print(f"    ❌ OpenAI API error: {response.status_code}")
                try:
                    err = response.json()
                    print(f"    ❌ Detail: {err.get('error', {}).get('message', '')}")
                except Exception:
                    pass
                return None

            data = response.json()
            content = data['choices'][0]['message']['content']
            return content

        except Exception as e:
            print(f"    ❌ OpenAI API call failed: {e}")
            return None

    def _parse_response(self, response: str, original_strength: int) -> Dict:
        """Parse GPT-4o response into structured result"""
        result = {
            'verified': True,
            'ai_opinion': '',
            'adjusted_strength': None,
            'adjustment_reason': '',
            'risk_flags': [],
            'opportunity_flags': [],
            'confidence': 0.5,
            'raw_response': response,
            'error': None
        }

        # Try to extract JSON from response
        try:
            # Find JSON block
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)

                result['adjusted_strength'] = parsed.get('adjusted_strength', original_strength)
                result['adjustment_reason'] = parsed.get('adjustment_reason', '')
                result['risk_flags'] = parsed.get('risk_flags', [])
                result['opportunity_flags'] = parsed.get('opportunity_flags', [])
                result['ai_opinion'] = parsed.get('opinion', '')
                result['confidence'] = parsed.get('confidence', 0.5)

                # Validate adjusted strength is within bounds
                if result['adjusted_strength'] is not None:
                    result['adjusted_strength'] = max(1, min(5, result['adjusted_strength']))

                return result
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            result['error'] = f"JSON parsing failed: {e}"

        # Fallback: use raw text as opinion
        result['ai_opinion'] = response[:500]
        return result

    def generate_ai_review_text(self, verify_result: Dict) -> str:
        """Generate AI review text for Excel storage"""
        if not verify_result.get('verified'):
            return f"[AI 검증 미실행] {verify_result.get('error', 'unknown')}"

        lines = ["[AI 검증 (GPT-4o)]"]

        # Opinion
        if verify_result.get('ai_opinion'):
            lines.append(f"의견: {verify_result['ai_opinion']}")

        # Adjustment
        adj = verify_result.get('adjusted_strength')
        reason = verify_result.get('adjustment_reason', '')
        if adj is not None and reason:
            lines.append(f"조정: {adj}점 ({reason})")

        # Risks
        risks = verify_result.get('risk_flags', [])
        if risks:
            lines.append(f"리스크: {'; '.join(risks)}")

        # Opportunities
        opps = verify_result.get('opportunity_flags', [])
        if opps:
            lines.append(f"기회: {'; '.join(opps)}")

        # Confidence
        conf = verify_result.get('confidence', 0)
        lines.append(f"신뢰도: {conf:.0%}")

        return '\n'.join(lines)


# Test
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    from config import load_env
    load_env()

    verifier = AIVerifier()
    print(f"AI Verifier enabled: {verifier.enabled}")
    print(f"Model: {verifier.model}")

    if not verifier.enabled:
        print("\n⚠️  OPENAI_API_KEY not set. AI verification will be skipped.")
        print("To enable, set a valid key in .env file.")
        # Test with mock
        result = verifier.verify(
            "삼성전자", "005930", 3,
            "해자강도: 3/5", "BM 분석 요약", "증거 요약", "지속가능성",
            {'gics_sector': 'IT', 'korean_sector_top': '반도체'}
        )
        print(f"\nMock result: {result}")
    else:
        print("✅ API key configured. Ready for AI verification.")
