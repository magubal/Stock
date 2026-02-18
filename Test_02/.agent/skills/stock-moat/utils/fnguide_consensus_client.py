"""FnGuide consensus scraper (best-effort)."""

import re
from datetime import date
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup


class FnGuideConsensusClient:
    BASE_URLS = [
        "https://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A{ticker}&cID=&MenuYn=Y&ReportGB=&NewMenuID=Y&stkGb=701",
        "https://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?pGB=1&gicode=A{ticker}&cID=&MenuYn=Y&ReportGB=&NewMenuID=103&stkGb=701",
    ]

    def __init__(self, timeout: int = 12):
        self.timeout = timeout

    def fetch_consensus(self, ticker: str, fiscal_year: str, as_of_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        as_of = as_of_date or date.today().isoformat()
        target = str(fiscal_year)
        aggregate_raw = []
        best = {"revenue_est": None, "op_income_est": None, "unit": "억원"}

        for url_tpl in self.BASE_URLS:
            url = url_tpl.format(ticker=ticker)
            html = self._fetch(url)
            if not html:
                continue
            parsed = self._parse_tables(html, target)
            aggregate_raw.append({"url": url, "parsed": parsed})
            if best["revenue_est"] is None and parsed.get("revenue_est") is not None:
                best["revenue_est"] = parsed.get("revenue_est")
            if best["op_income_est"] is None and parsed.get("op_income_est") is not None:
                best["op_income_est"] = parsed.get("op_income_est")
            if parsed.get("unit"):
                best["unit"] = parsed.get("unit")

        if best["revenue_est"] is None and best["op_income_est"] is None:
            return None

        confidence = "high" if best["revenue_est"] is not None and best["op_income_est"] is not None else "medium"
        return {
            "ticker": ticker,
            "fiscal_year": target,
            "revenue_est": best["revenue_est"],
            "op_income_est": best["op_income_est"],
            "unit": best["unit"],
            "source": "fnguide",
            "confidence": confidence,
            "as_of_date": as_of,
            "freshness_days": 0,
            "raw": {"sources": aggregate_raw},
            "reused": False,
        }

    def _fetch(self, url: str) -> Optional[str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        try:
            res = requests.get(url, headers=headers, timeout=self.timeout)
            if res.status_code != 200:
                return None
            # requests auto-detection occasionally fails on KR pages
            if not res.encoding:
                res.encoding = res.apparent_encoding or "utf-8"
            return res.text
        except Exception:
            return None

    def _parse_tables(self, html: str, target_year: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        unit = self._extract_unit(soup)
        revenue = None
        op_income = None

        for table in tables:
            matrix = self._to_matrix(table)
            if len(matrix) < 2:
                continue

            header = matrix[0]
            year_positions = self._year_positions(header)
            if not year_positions:
                continue

            target_pos = self._pick_year_pos(year_positions, target_year)
            if target_pos is None:
                continue

            for row in matrix[1:]:
                if not row:
                    continue
                metric = self._normalize(row[0])
                if "매출" in metric and revenue is None:
                    revenue = self._to_number(row[target_pos] if target_pos < len(row) else "")
                elif "영업이익" in metric and op_income is None:
                    op_income = self._to_number(row[target_pos] if target_pos < len(row) else "")

            if revenue is not None and op_income is not None:
                break

        return {"revenue_est": revenue, "op_income_est": op_income, "unit": unit}

    def _to_matrix(self, table) -> List[List[str]]:
        rows = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            rows.append([self._normalize(cell.get_text(" ", strip=True)) for cell in cells])
        return rows

    def _year_positions(self, header: List[str]) -> List[tuple]:
        positions = []
        for idx, cell in enumerate(header):
            m = re.search(r"(20\d{2})", cell)
            if m:
                positions.append((idx, m.group(1)))
        return positions

    def _pick_year_pos(self, year_positions: List[tuple], target_year: str) -> Optional[int]:
        for idx, year in year_positions:
            if year == target_year:
                return idx
        # fallback: choose latest year available
        return max(year_positions, key=lambda x: x[1])[0] if year_positions else None

    def _extract_unit(self, soup: BeautifulSoup) -> str:
        text = soup.get_text(" ", strip=True)
        if "단위" in text and "억원" in text:
            return "억원"
        if "백만원" in text:
            return "백만원"
        return "억원"

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    @staticmethod
    def _to_number(value: str) -> Optional[float]:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text in {"-", "N/A", "n/a"}:
            return None
        text = text.replace(",", "")
        text = re.sub(r"[^0-9\.-]", "", text)
        if not text:
            return None
        try:
            return float(text)
        except Exception:
            return None
