#!/usr/bin/env python3
"""
블로그 글 AI 분석기 — Claude API 기반 투자 관점 요약.
텍스트 우선 분석, 텍스트 부족 시 Vision fallback.
"""
import json
import base64
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent.parent


def analyze_text(blogger: str, title: str, text_content: str, api_key: str = None) -> dict:
    """Claude text API로 블로그 글 분석."""
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}

    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic SDK not installed (pip install anthropic)"}

    prompt = f"""당신은 한국 주식시장 전문 애널리스트입니다.
아래 투자자 블로그 글을 분석하여 JSON으로 응답하세요.

블로거: {blogger}
제목: {title}
본문:
{text_content[:4000]}

응답 형식 (JSON만 출력):
{{
  "summary": "글의 핵심 내용을 3-5문장으로 요약",
  "viewpoint": "투자자의 핵심 관점과 논거를 2-3문장으로 정리",
  "implications": "이 글이 나의 투자에 주는 시사점을 2-3문장으로 정리"
}}"""

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.content[0].text.strip()
    # Extract JSON from response
    try:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": raw, "viewpoint": "", "implications": ""}


def analyze_vision(blogger: str, title: str, image_path: str, api_key: str = None) -> dict:
    """Claude Vision API로 캡처 이미지 분석 (텍스트 부족 시 fallback)."""
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}

    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic SDK not installed"}

    full_path = ROOT / image_path if not Path(image_path).is_absolute() else Path(image_path)
    if not full_path.exists():
        return {"error": f"Image not found: {full_path}"}

    with open(full_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = full_path.suffix.lower()
    media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
        ext.lstrip("."), "image/jpeg"
    )

    prompt = f"""당신은 한국 주식시장 전문 애널리스트입니다.
아래 투자자 블로그 캡처 이미지를 분석하여 JSON으로 응답하세요.

블로거: {blogger}
제목: {title}

이미지를 읽고 아래 형식으로 응답하세요 (JSON만 출력):
{{
  "summary": "글의 핵심 내용을 3-5문장으로 요약",
  "viewpoint": "투자자의 핵심 관점과 논거를 2-3문장으로 정리",
  "implications": "이 글이 나의 투자에 주는 시사점을 2-3문장으로 정리"
}}"""

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": image_data},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )

    raw = resp.content[0].text.strip()
    try:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"summary": raw, "viewpoint": "", "implications": ""}


def analyze_post(blogger: str, title: str, text_content: str = None,
                 image_path: str = None, api_key: str = None) -> dict:
    """Hybrid 분석: 텍스트 우선, Vision fallback."""
    if text_content and len(text_content.strip()) >= 100:
        result = analyze_text(blogger, title, text_content, api_key)
        if "error" not in result:
            result["ai_model"] = "claude-text"
            return result

    if image_path:
        result = analyze_vision(blogger, title, image_path, api_key)
        if "error" not in result:
            result["ai_model"] = "claude-vision"
            return result
        return result

    return {"error": "No text content or image available for analysis"}
