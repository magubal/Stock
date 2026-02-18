"""LLM 기반 인사이트 자동 추출 서비스"""
import json
from typing import List, Dict, Any, Optional


class InsightExtractor:
    def __init__(self, api_key: Optional[str] = None):
        self.client = None
        if api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                pass

    def extract(self, content: str, category: str) -> List[Dict[str, Any]]:
        """content에서 인사이트 추출. API 키 없으면 빈 리스트 반환."""
        if not self.client:
            return []

        prompt = f"""다음 투자 분석 내용에서 핵심 인사이트를 추출하세요.
카테고리: {category}

내용:
{content[:3000]}

각 인사이트를 JSON 배열로 출력하세요. 각 항목:
- "type": "claim" (사실 주장), "prediction" (예측/전망), "pattern" (패턴/추세)
- "text": 인사이트 내용 (1~2문장, 한국어)
- "confidence": 확신도 (0.0~1.0)
- "keywords": 관련 키워드 배열 (한국어)

최대 5개까지만 추출하세요. JSON 배열만 출력하세요."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            # JSON 배열 추출
            if text.startswith("["):
                return json.loads(text)
            # 코드블록 안에 있을 수 있음
            if "```" in text:
                json_str = text.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                return json.loads(json_str.strip())
            return []
        except Exception:
            return []
