"""
Market Daily Digest - Service Layer
종합정리 조회, 저장, 히스토리, AI 총평 생성
"""
import json
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from ..models.daily_digest import DailyDigest


class DailyDigestService:
    def __init__(self, db: Session):
        self.db = db

    async def get_digest(self, date: str) -> dict:
        """특정 날짜 종합정리 조회"""
        if not date:
            kst_now = datetime.now(timezone.utc) + timedelta(hours=9)
            date = kst_now.strftime("%Y-%m-%d")

        row = self.db.query(DailyDigest).filter_by(date=date).first()
        if not row:
            return {"date": date, "exists": False}

        return {
            "date": row.date,
            "exists": True,
            "module_summaries": row.module_summaries or {},
            "mindmap_data": row.mindmap_data,
            "ai_summary": row.ai_summary or "",
            "user_summary": row.user_summary or "",
            "ai_model": row.ai_model or "",
            "sentiment_score": row.sentiment_score,
            "sentiment_label": row.sentiment_label or "",
            "source": row.source or "REAL",
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }

    async def save_digest(self, data: dict) -> dict:
        """종합정리 upsert (date 기준)"""
        date = data.get("date")
        if not date:
            raise HTTPException(status_code=400, detail={"detail": "date 필수", "error_code": "DATE_REQUIRED"})

        row = self.db.query(DailyDigest).filter_by(date=date).first()
        if row:
            # Update
            if "module_summaries" in data:
                row.module_summaries = data["module_summaries"]
            if "mindmap_data" in data:
                row.mindmap_data = data["mindmap_data"]
            if "ai_summary" in data:
                row.ai_summary = data["ai_summary"]
            if "user_summary" in data:
                row.user_summary = data["user_summary"]
            if "ai_model" in data:
                row.ai_model = data["ai_model"]
            if "sentiment_score" in data:
                row.sentiment_score = data["sentiment_score"]
            if "sentiment_label" in data:
                row.sentiment_label = data["sentiment_label"]
        else:
            # Insert
            row = DailyDigest(
                date=date,
                module_summaries=data.get("module_summaries"),
                mindmap_data=data.get("mindmap_data"),
                ai_summary=data.get("ai_summary"),
                user_summary=data.get("user_summary"),
                ai_model=data.get("ai_model"),
                sentiment_score=data.get("sentiment_score"),
                sentiment_label=data.get("sentiment_label"),
                source=data.get("source", "REAL"),
            )
            self.db.add(row)

        self.db.commit()
        return {"status": "ok", "date": date, "action": "updated" if row.updated_at else "created"}

    async def get_history(self, limit: int = 30) -> dict:
        """저장된 날짜 목록 (최신순)"""
        rows = (
            self.db.query(DailyDigest.date, DailyDigest.sentiment_label, DailyDigest.source)
            .order_by(desc(DailyDigest.date))
            .limit(limit)
            .all()
        )
        return {
            "total": len(rows),
            "dates": [
                {"date": r.date, "sentiment": r.sentiment_label or "", "source": r.source or "REAL"}
                for r in rows
            ],
        }

    async def ai_analyze(self, date: str, module_summaries: dict, model: str = None) -> dict:
        """AI 총평 생성 — Claude API proxy"""
        import os

        model = model or "claude-sonnet-4-5-20250929"

        # API 키 로드
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("ANTHROPIC_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break

        if not api_key:
            raise HTTPException(
                status_code=400,
                detail={"detail": "ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.", "error_code": "API_KEY_MISSING"},
            )

        system_prompt = """당신은 한국 시장 전문 애널리스트입니다.
아래 7개 시장 모니터링 모듈의 당일 데이터를 종합하여 다음을 작성하세요:

## 시장 흐름 요약
(3줄 요약)

## 핵심 인사이트
(bullet 3~5개)

## 리스크 요인
(bullet 2~3개)

## 총평
(투자 관점 2~3문장)

## 시장 심리
- 방향: (Bullish/Neutral/Bearish 중 하나)
- 점수: (-1.0 ~ 1.0, 소수점 2자리)

마크다운 형식으로 작성하세요. 한국어로 답변하세요."""

        user_content = f"날짜: {date}\n\n모듈 데이터:\n{json.dumps(module_summaries, ensure_ascii=False, indent=2)}"

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = await asyncio.to_thread(
                client.messages.create,
                model=model,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            summary_text = response.content[0].text

            # 심리 점수 추출 시도
            sentiment_score = 0.0
            sentiment_label = "Neutral"
            for line in summary_text.split("\n"):
                line_lower = line.strip().lower()
                if "bullish" in line_lower:
                    sentiment_label = "Bullish"
                    sentiment_score = 0.5
                elif "bearish" in line_lower:
                    sentiment_label = "Bearish"
                    sentiment_score = -0.5
                if "점수:" in line or "score:" in line_lower:
                    import re
                    nums = re.findall(r'-?\d+\.?\d*', line)
                    if nums:
                        val = float(nums[0])
                        if -1.0 <= val <= 1.0:
                            sentiment_score = val

            return {
                "status": "ok",
                "summary": summary_text,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "model_used": model,
            }
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail={"detail": "anthropic 패키지가 설치되지 않았습니다: pip install anthropic", "error_code": "MISSING_PACKAGE"},
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"detail": f"AI 분석 실패: {str(e)}", "error_code": "AI_ANALYZE_ERROR"},
            )
