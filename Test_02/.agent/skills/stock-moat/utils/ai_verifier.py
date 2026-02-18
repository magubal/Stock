"""
AI Verifier v2 - Independent moat verification.

Compatible with both:
- New signature verify(company, ticker, classification, report_sections, ...)
- Legacy signature verify(company, ticker, moat_strength, moat_desc, ... , classification)
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class AIVerifier:
    """Independent Moat Evaluator."""

    def __init__(self, api_key: str = None, load_from_env: bool = False):
        # Deterministic behavior for tests:
        # api_key=None => disabled unless caller explicitly requests env loading.
        if api_key is None and load_from_env:
            from config import load_env
            load_env()
            api_key = os.getenv("ANTHROPIC_API_KEY")

        self.api_key = api_key
        self.model = "claude-opus-4-6"
        self.enabled = bool(api_key)

    def verify(
        self,
        company_name: str,
        ticker: str,
        classification: Dict,
        report_sections: Dict,
        financials: Dict = None,
        multi_year_financials: Dict = None,
        bm_analysis: Dict = None,
        evidence_items: List = None,
        # Legacy params (kept for backward compatibility)
        moat_strength: int = None,
        moat_desc: str = "",
        bm_summary: str = "",
        evidence_summary: str = "",
        sustainability_notes: str = "",
    ) -> Dict:
        (
            classification,
            report_sections,
            financials,
            multi_year_financials,
            bm_analysis,
            evidence_items,
            moat_strength,
            moat_desc,
            bm_summary,
            evidence_summary,
            sustainability_notes,
        ) = self._coerce_legacy_inputs(
            classification,
            report_sections,
            financials,
            multi_year_financials,
            bm_analysis,
            evidence_items,
            moat_strength,
            moat_desc,
            bm_summary,
            evidence_summary,
            sustainability_notes,
        )

        if not self.enabled:
            return {
                "verified": False,
                "ai_opinion": "ANTHROPIC_API_KEY not configured",
                "independent_strength": None,
                "adjusted_strength": None,
                "adjustment_reason": "",
                "risk_flags": [],
                "opportunity_flags": [],
                "confidence": 0.0,
                "raw_response": "",
                "error": "API key not set",
            }

        prompt = self._build_independent_prompt(
            company_name=company_name,
            ticker=ticker,
            classification=classification,
            report_sections=report_sections,
            financials=financials,
            multi_year_financials=multi_year_financials,
            bm_analysis=bm_analysis,
            evidence_items=evidence_items,
        )

        response = self._call_claude(prompt)
        if response is None:
            return {
                "verified": False,
                "ai_opinion": "API call failed",
                "independent_strength": None,
                "adjusted_strength": None,
                "adjustment_reason": "",
                "risk_flags": [],
                "opportunity_flags": [],
                "confidence": 0.0,
                "raw_response": "",
                "error": "Claude API call failed",
            }

        result = self._parse_response(response)

        if moat_strength is not None and result.get("independent_strength") is not None:
            gap = abs(result["independent_strength"] - moat_strength)
            result["rule_based_strength"] = moat_strength
            result["score_gap"] = gap
            if gap >= 2:
                result["gap_flag"] = True
                result["adjustment_reason"] = (
                    f"AI({result['independent_strength']}) vs "
                    f"Rule-Based({moat_strength}) gap={gap}"
                )

        result["adjusted_strength"] = result.get("independent_strength", moat_strength)
        return result

    def generate_ai_review_text(self, result: Dict[str, Any]) -> str:
        if not result:
            return "AI review: no result"

        if not result.get("verified"):
            reason = result.get("error") or result.get("ai_opinion") or "disabled"
            return f"AI review skipped: {reason}"

        score = result.get("independent_strength")
        opinion = result.get("ai_opinion", "")
        confidence = result.get("confidence", 0)
        risks = ", ".join(result.get("risk_flags", [])[:3]) or "none"
        opportunities = ", ".join(result.get("opportunity_flags", [])[:3]) or "none"

        return (
            f"AI independent score: {score}/5\n"
            f"Confidence: {confidence}\n"
            f"Opinion: {opinion}\n"
            f"Risks: {risks}\n"
            f"Opportunities: {opportunities}"
        )

    def _coerce_legacy_inputs(
        self,
        classification,
        report_sections,
        financials,
        multi_year_financials,
        bm_analysis,
        evidence_items,
        moat_strength,
        moat_desc,
        bm_summary,
        evidence_summary,
        sustainability_notes,
    ) -> Tuple[Dict, Dict, Dict, Dict, Dict, List, Optional[int], str, str, str, str]:
        # New signature path.
        if isinstance(classification, dict) and isinstance(report_sections, dict):
            return (
                classification,
                report_sections,
                financials if isinstance(financials, dict) else {},
                multi_year_financials if isinstance(multi_year_financials, dict) else {},
                bm_analysis if isinstance(bm_analysis, dict) else {},
                evidence_items if isinstance(evidence_items, list) else [],
                moat_strength,
                moat_desc,
                bm_summary,
                evidence_summary,
                sustainability_notes,
            )

        # Legacy positional path.
        legacy_strength = moat_strength if moat_strength is not None else (
            int(classification) if isinstance(classification, (int, float)) else None
        )
        legacy_classification = evidence_items if isinstance(evidence_items, dict) else {}
        legacy_moat_desc = moat_desc or (report_sections if isinstance(report_sections, str) else "")
        legacy_bm_summary = bm_summary or (financials if isinstance(financials, str) else "")
        legacy_evidence_summary = evidence_summary or (
            multi_year_financials if isinstance(multi_year_financials, str) else ""
        )
        legacy_sustainability_notes = sustainability_notes or (
            bm_analysis if isinstance(bm_analysis, str) else ""
        )

        return (
            legacy_classification,
            {},
            {},
            {},
            {},
            [],
            legacy_strength,
            legacy_moat_desc,
            legacy_bm_summary,
            legacy_evidence_summary,
            legacy_sustainability_notes,
        )

    def _build_independent_prompt(
        self,
        company_name: str,
        ticker: str,
        classification: Dict,
        report_sections: Dict,
        financials: Dict = None,
        multi_year_financials: Dict = None,
        bm_analysis: Dict = None,
        evidence_items: List = None,
    ) -> str:
        sector = classification.get("korean_sector_top") or classification.get("gics_sector") or "unknown"
        industry = classification.get("gics_industry", "")

        report_text = self._extract_report_highlights(report_sections)
        fin_text = self._format_multi_year_financials(financials, multi_year_financials)
        evidence_text = self._format_evidence_items(evidence_items)
        bm_text = self._format_bm_analysis(bm_analysis)

        return (
            "You are an independent equity moat analyst.\n"
            "Evaluate moat strength on a 1-5 scale based only on provided data.\n\n"
            f"Company: {company_name} ({ticker})\n"
            f"Sector: {sector} / {industry}\n\n"
            "[Business report]\n"
            f"{report_text}\n\n"
            "[Financials]\n"
            f"{fin_text}\n\n"
            "[Evidence items]\n"
            f"{evidence_text}\n\n"
            "[Business model]\n"
            f"{bm_text}\n\n"
            "Return strict JSON:\n"
            "{\n"
            "  \"independent_strength\": 1-5,\n"
            "  \"reasoning\": \"...\",\n"
            "  \"moat_types_found\": [\"...\"],\n"
            "  \"risk_flags\": [\"...\"],\n"
            "  \"opportunity_flags\": [\"...\"],\n"
            "  \"opinion\": \"...\",\n"
            "  \"confidence\": 0.0-1.0\n"
            "}"
        )

    def _call_claude(self, prompt: str) -> Optional[str]:
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": self.model,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": self.api_key,
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            content = body.get("content", [])
            if not content:
                return None
            return content[0].get("text", "")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        raw = response_text or ""
        parsed = self._safe_parse_json(raw)

        if parsed is None:
            return {
                "verified": True,
                "independent_strength": None,
                "ai_opinion": raw[:500],
                "risk_flags": [],
                "opportunity_flags": [],
                "confidence": 0.0,
                "raw_response": raw,
            }

        strength = parsed.get("independent_strength")
        if isinstance(strength, str) and strength.isdigit():
            strength = int(strength)
        if isinstance(strength, (int, float)):
            strength = max(1, min(5, int(round(strength))))
        else:
            strength = None

        confidence = parsed.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        return {
            "verified": True,
            "independent_strength": strength,
            "ai_opinion": parsed.get("opinion") or parsed.get("reasoning") or "",
            "risk_flags": parsed.get("risk_flags", []) if isinstance(parsed.get("risk_flags", []), list) else [],
            "opportunity_flags": parsed.get("opportunity_flags", [])
            if isinstance(parsed.get("opportunity_flags", []), list)
            else [],
            "confidence": confidence,
            "raw_response": raw,
        }

    def _safe_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        text = text.strip()
        try:
            obj = json.loads(text)
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            pass

        # Extract first JSON object from mixed text.
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return None
        try:
            obj = json.loads(match.group(0))
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None

    def _extract_report_highlights(self, report_sections: Dict, max_chars: int = 8000) -> str:
        if not report_sections or not isinstance(report_sections, dict):
            return "No report sections"

        keys = [
            "business_overview",
            "management_review",
            "risk_factors",
            "competitive_status",
            "rd_status",
            "business_all",
        ]

        chunks = []
        for k in keys:
            value = report_sections.get(k)
            if isinstance(value, str) and value.strip():
                chunks.append(f"[{k}] {value.strip()}")

        text = "\n\n".join(chunks) if chunks else str(report_sections)[:max_chars]
        return text[:max_chars]

    def _format_multi_year_financials(
        self,
        financials: Optional[Dict],
        multi_year_financials: Optional[Dict]
    ) -> str:
        lines = []
        if isinstance(multi_year_financials, dict) and multi_year_financials:
            for yr in sorted(multi_year_financials.keys()):
                fin = multi_year_financials.get(yr, {}) or {}
                rev = fin.get("revenue", 0)
                op = fin.get("operating_income", 0)
                opm = fin.get("operating_margin")
                lines.append(
                    f"{yr}: revenue={rev:,}, op_income={op:,}, op_margin={opm if opm is not None else 'N/A'}"
                )

        if not lines and isinstance(financials, dict) and financials:
            rev = financials.get("revenue", 0)
            op = financials.get("operating_income", 0)
            opm = financials.get("operating_margin")
            lines.append(f"latest: revenue={rev:,}, op_income={op:,}, op_margin={opm if opm is not None else 'N/A'}")

        return "\n".join(lines) if lines else "No financial data"

    def _format_evidence_items(self, evidence_items: Optional[List], max_items: int = 10) -> str:
        if not evidence_items:
            return "No evidence items"

        sorted_items = sorted(
            evidence_items,
            key=lambda x: getattr(x, "quality_score", 0),
            reverse=True,
        )[:max_items]

        lines = []
        for i, ev in enumerate(sorted_items, 1):
            moat_type = getattr(ev, "moat_type", "unknown")
            quality = getattr(ev, "quality_score", 0)
            text = getattr(ev, "evidence_text", "")
            source = getattr(ev, "source", "")
            lines.append(f"#{i} [{moat_type}] q={quality}: {text[:240]}")
            if source:
                lines.append(f"  source={source}")

        return "\n".join(lines)

    def _format_bm_analysis(self, bm_analysis: Optional[Dict]) -> str:
        if not bm_analysis:
            return "No BM analysis"

        if hasattr(bm_analysis, "__dict__") and not isinstance(bm_analysis, dict):
            bm = bm_analysis.__dict__
        else:
            bm = bm_analysis if isinstance(bm_analysis, dict) else {"raw": str(bm_analysis)}

        keys = [
            "customer",
            "value_proposition",
            "revenue_model",
            "cost_structure",
            "key_resources",
            "distribution",
        ]
        lines = []
        for k in keys:
            v = bm.get(k)
            if v:
                lines.append(f"{k}: {v}")

        return "\n".join(lines) if lines else str(bm)[:1500]
