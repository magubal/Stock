"""
DART API Client for Business Report Analysis
Fetches and parses 사업보고서 (Business Reports)

Extended for evidence-based-moat v2:
- Cache infrastructure (JSON files)
- Financial statements API (DS003: fnltt_singl_acnt)
- Segment revenue API (DS002)
- Business report download (DS001)
"""

import requests
import time
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Project root for cache directory
PROJECT_ROOT = Path("F:/PSJ/AntigravityWorkPlace/Stock/Test_02")
CACHE_DIR = PROJECT_ROOT / "data" / "dart_cache"

# Cache TTL configuration (days)
CACHE_TTL = {
    'corp_codes': 7,
    'company_info': 30,
    'financials': 90,
    'segments': 90,
    'report_sections': 365,
}


class DARTClient:
    """DART Open API Client with caching and extended API support"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://opendart.fss.or.kr/api"
        self.session = requests.Session()
        self._corp_code_map = None  # In-memory cache for corp codes
        self._api_delay = 2.0  # seconds between API calls

    # ── Cache Infrastructure ──────────────────────────────────

    def _get_cache_path(self, corp_code: str, data_type: str) -> Path:
        """Get cache file path for a given corp_code and data type"""
        if data_type == 'corp_codes':
            return CACHE_DIR / "corp_codes.json"
        return CACHE_DIR / corp_code / f"{data_type}.json"

    def _load_cache(self, corp_code: str, data_type: str) -> Optional[Dict]:
        """Load cached data if not expired"""
        cache_path = self._get_cache_path(corp_code, data_type)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            fetched_at = cached.get('fetched_at')
            if not fetched_at:
                return None

            ttl_days = CACHE_TTL.get(data_type, 30)
            expiry = datetime.fromisoformat(fetched_at) + timedelta(days=ttl_days)

            if datetime.now() > expiry:
                return None

            return cached
        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def _save_cache(self, corp_code: str, data_type: str, data: Dict):
        """Save data to cache with timestamp"""
        cache_path = self._get_cache_path(corp_code, data_type)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        data['fetched_at'] = datetime.now().isoformat()

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _api_call(
        self, url: str, params: dict, timeout: int = 15, max_retries: int = 3
    ) -> Optional[Dict]:
        """Make API call with rate limiting, retry logic, and error handling"""
        for attempt in range(1, max_retries + 1):
            time.sleep(self._api_delay)
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 429:
                    # Rate limited - wait longer and retry
                    wait = self._api_delay * attempt * 2
                    print(f"    ⚠️  Rate limited, waiting {wait:.0f}s (attempt {attempt}/{max_retries})")
                    time.sleep(wait)
                    continue
                if response.status_code >= 500:
                    # Server error - retry
                    if attempt < max_retries:
                        print(f"    ⚠️  Server error {response.status_code}, retrying ({attempt}/{max_retries})")
                        time.sleep(self._api_delay * attempt)
                        continue
                    print(f"    ❌ DART API server error: {response.status_code}")
                    return None
                if response.status_code != 200:
                    print(f"    ❌ DART API HTTP error: {response.status_code}")
                    return None
                data = response.json()
                status_code = data.get("status")
                if status_code == "901":
                    # API key expired/invalid
                    print(f"    ❌ DART API key error (901): {data.get('message', '')}")
                    return None
                if status_code not in ("000", "013"):
                    # 013 = no data (valid but empty)
                    msg = data.get("message", "")
                    if status_code != "013":
                        print(f"    ⚠️  DART API status {status_code}: {msg}")
                    return None
                return data
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    print(f"    ⚠️  Timeout, retrying ({attempt}/{max_retries})")
                    continue
                print(f"    ❌ DART API timeout after {max_retries} attempts")
                return None
            except requests.exceptions.ConnectionError:
                if attempt < max_retries:
                    print(f"    ⚠️  Connection error, retrying ({attempt}/{max_retries})")
                    time.sleep(self._api_delay * attempt)
                    continue
                print(f"    ❌ DART API connection failed after {max_retries} attempts")
                return None
            except Exception as e:
                print(f"    ❌ DART API error: {e}")
                return None
        return None

    # ── Corp Code Lookup (with cache) ─────────────────────────

    def _load_corp_code_map(self) -> Dict[str, str]:
        """Load or download corp_code mapping {stock_code: corp_code}"""
        # Check in-memory cache
        if self._corp_code_map is not None:
            return self._corp_code_map

        # Check file cache
        cached = self._load_cache('', 'corp_codes')
        if cached and 'map' in cached:
            self._corp_code_map = cached['map']
            return self._corp_code_map

        # Download from DART
        print("  📥 Downloading corp code list from DART...")
        import zipfile
        import io
        import xml.etree.ElementTree as ET

        url = f"{self.base_url}/corpCode.xml"
        params = {"crtfc_key": self.api_key}

        try:
            response = self.session.get(url, params=params, timeout=60)
            if response.status_code != 200:
                print(f"    ❌ DART API error: {response.status_code}")
                return {}

            zip_file = zipfile.ZipFile(io.BytesIO(response.content))
            xml_content = zip_file.read('CORPCODE.xml')
            root = ET.fromstring(xml_content)

            code_map = {}
            for corp in root.findall('list'):
                stock_code_elem = corp.find('stock_code')
                corp_code_elem = corp.find('corp_code')
                if (stock_code_elem is not None and corp_code_elem is not None
                        and stock_code_elem.text and stock_code_elem.text.strip()):
                    code_map[stock_code_elem.text.strip()] = corp_code_elem.text.strip()

            # Save to cache
            self._save_cache('', 'corp_codes', {'map': code_map})
            self._corp_code_map = code_map
            print(f"    ✅ Loaded {len(code_map)} corp codes")
            return code_map

        except Exception as e:
            print(f"    ❌ Error loading corp codes: {e}")
            return {}

    def get_corp_code(self, stock_code: str) -> Optional[str]:
        """Get DART corp_code from stock ticker (cached)"""
        code_map = self._load_corp_code_map()
        return code_map.get(stock_code)

    # ── Company Info (기존, 캐시 추가) ─────────────────────────

    def get_company_info(self, corp_code: str) -> Optional[Dict]:
        """Get company overview from DART (with cache)"""
        # Check cache
        cached = self._load_cache(corp_code, 'company_info')
        if cached:
            return cached

        data = self._api_call(
            f"{self.base_url}/company.json",
            {"crtfc_key": self.api_key, "corp_code": corp_code}
        )
        if not data:
            return None

        # Save to cache
        self._save_cache(corp_code, 'company_info', data)
        return data

    # ── Financial Statements (DS003: fnltt_singl_acnt) ────────

    def get_financial_statements(
        self,
        corp_code: str,
        bsns_year: str = "2023",
        reprt_code: str = "11011"
    ) -> Optional[Dict]:
        """
        Fetch single-company key financial accounts from DART.

        API: fnlttSinglAcnt.json
        Returns parsed financials for the year:
        {
            'revenue': int,
            'operating_income': int,
            'net_income': int,
            'total_assets': int,
            'total_liabilities': int,
            'total_equity': int,
            'cost_of_revenue': int,
            'sga_expenses': int,
            'rnd_expenses': int,
            'year': str,
            'raw_accounts': list
        }
        """
        # Check cache (key includes reprt_code to avoid mixing annual/quarterly)
        cache_key = 'financials'
        year_key = f"{bsns_year}_{reprt_code}"
        cached = self._load_cache(corp_code, cache_key)
        if cached and cached.get('years', {}).get(year_key):
            return cached['years'][year_key]

        data = self._api_call(
            f"{self.base_url}/fnlttSinglAcnt.json",
            {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": bsns_year,
                "reprt_code": reprt_code,
                "fs_div": "OFS"  # 개별 재무제표 (CFS=연결)
            }
        )

        if not data or not data.get('list'):
            # Try consolidated (CFS)
            data = self._api_call(
                f"{self.base_url}/fnlttSinglAcnt.json",
                {
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bsns_year": bsns_year,
                    "reprt_code": reprt_code,
                    "fs_div": "CFS"
                }
            )

        if not data or not data.get('list'):
            return None

        # Parse accounts
        parsed = self._parse_financial_accounts(data['list'], bsns_year)

        # Update cache (multi-year structure, keyed by year+reprt_code)
        cache_data = self._load_cache(corp_code, cache_key) or {'years': {}}
        if 'years' not in cache_data:
            cache_data['years'] = {}
        cache_data['years'][year_key] = parsed
        self._save_cache(corp_code, cache_key, cache_data)

        return parsed

    def _parse_financial_accounts(self, accounts: List[Dict], year: str) -> Dict:
        """Parse DART financial statement accounts into structured dict"""
        # Account name mapping (DART account_nm → our key)
        ACCOUNT_MAP = {
            '매출액': 'revenue',
            '수익(매출액)': 'revenue',
            '영업수익': 'revenue',
            '영업이익': 'operating_income',
            '영업이익(손실)': 'operating_income',
            '당기순이익': 'net_income',
            '당기순이익(손실)': 'net_income',
            '자산총계': 'total_assets',
            '부채총계': 'total_liabilities',
            '자본총계': 'total_equity',
            '매출원가': 'cost_of_revenue',
            '판매비와관리비': 'sga_expenses',
            '연구개발비용': 'rnd_expenses',
        }

        result = {
            'year': year,
            'revenue': 0,
            'operating_income': 0,
            'net_income': 0,
            'total_assets': 0,
            'total_liabilities': 0,
            'total_equity': 0,
            'cost_of_revenue': 0,
            'sga_expenses': 0,
            'rnd_expenses': 0,
            'raw_accounts': []
        }

        for acct in accounts:
            acct_nm = acct.get('account_nm', '').strip()
            # Use thstrm_amount (당기) for current year
            amount_str = acct.get('thstrm_amount', '0')

            # Clean amount string
            if amount_str:
                amount_str = amount_str.replace(',', '').replace(' ', '').strip()
                try:
                    amount = int(amount_str)
                except (ValueError, TypeError):
                    amount = 0
            else:
                amount = 0

            # Map to our key
            for dart_name, our_key in ACCOUNT_MAP.items():
                if acct_nm == dart_name:
                    if result[our_key] == 0:  # Don't overwrite if already set
                        result[our_key] = amount
                    break

            result['raw_accounts'].append({
                'account_nm': acct_nm,
                'thstrm_amount': amount,
                'sj_nm': acct.get('sj_nm', ''),  # 재무제표 구분명
            })

        # Calculate derived metrics
        if result['revenue'] > 0:
            result['operating_margin'] = round(result['operating_income'] / result['revenue'], 4)
            if result['cost_of_revenue'] > 0:
                result['cost_ratio'] = round(result['cost_of_revenue'] / result['revenue'], 4)
            if result['sga_expenses'] > 0:
                result['sga_ratio'] = round(result['sga_expenses'] / result['revenue'], 4)
        if result['total_equity'] > 0:
            result['roe'] = round(result['net_income'] / result['total_equity'], 4)
            result['debt_ratio'] = round(result['total_liabilities'] / result['total_equity'], 4)

        return result

    def get_multi_year_financials(
        self,
        corp_code: str,
        years: List[str] = None
    ) -> Dict[str, Dict]:
        """Fetch financials for multiple years (default: last 3 years)"""
        if years is None:
            current_year = datetime.now().year
            years = [str(y) for y in range(current_year - 3, current_year)]

        results = {}
        for year in years:
            fin = self.get_financial_statements(corp_code, bsns_year=year)
            if fin:
                results[year] = fin
                print(f"    ✅ Financials {year}: revenue={fin.get('revenue', 0):,}")

        return results

    # ── Shares Outstanding ──────────────────────────────────

    def get_shares_outstanding(self, corp_code: str) -> int:
        """DART 주식총수현황 API로 보통주 유통주식수 조회.
        Returns: 보통주 유통주식수 (int), 조회 실패 시 0
        """
        from datetime import date as dt_date
        current_year = dt_date.today().year

        # 최근 3년 사업보고서 시도 (최신 보고서가 아직 없을 수 있음)
        for year in range(current_year - 1, current_year - 4, -1):
            try:
                data = self._api_call(
                    f"{self.base_url}/stockTotqySttus.json",
                    {
                        "crtfc_key": self.api_key,
                        "corp_code": corp_code,
                        "bsns_year": str(year),
                        "reprt_code": "11011",
                    }
                )
                if data and data.get('list'):
                    for item in data['list']:
                        se = item.get('se', '')
                        if '보통주' in se:
                            # distb_stock_co = 유통주식수, istc_totqy = 발행총수
                            distb = item.get('distb_stock_co', '0')
                            distb = int(str(distb).replace(',', '').replace('-', '0') or '0')
                            if distb > 0:
                                return distb
                            istc = item.get('istc_totqy', '0')
                            return int(str(istc).replace(',', '').replace('-', '0') or '0')
            except Exception:
                continue

        return 0

    # ── Segment Revenue (DS002) ───────────────────────────────

    def get_segment_revenue(
        self,
        corp_code: str,
        bsns_year: str = "2023",
        reprt_code: str = "11011"
    ) -> Optional[List[Dict]]:
        """
        Fetch segment (business division) revenue from DART.

        Tries multiple API endpoints in order:
        1. /fnlttSinglAcnt.json with sj_div=SCE (사업부문)
        2. Fall back to parsing from financial data

        Returns: [
            {'name': 'DS(반도체)', 'revenue': int, 'ratio': float}
        ]
        """
        # Check cache
        cached = self._load_cache(corp_code, 'segments')
        if cached and cached.get('year') == bsns_year and cached.get('segments'):
            return cached['segments']

        # Try the revenue by segment API
        # DART doesn't have a direct segment API for all companies,
        # so we try to get it from the main financial statement breakdown
        segments = self._try_segment_from_disclosure(corp_code, bsns_year, reprt_code)

        if segments:
            self._save_cache(corp_code, 'segments', {
                'year': bsns_year,
                'segments': segments,
                'corp_code': corp_code
            })
            return segments

        return None

    def _try_segment_from_disclosure(
        self, corp_code: str, bsns_year: str, reprt_code: str
    ) -> Optional[List[Dict]]:
        """Try to get segment data from DART financial statements breakdown"""
        # Try fnltt_singl_acnt with CFS (consolidated) which often has segment-like breakdown
        data = self._api_call(
            f"{self.base_url}/fnlttSinglAcnt.json",
            {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": bsns_year,
                "reprt_code": reprt_code,
                "fs_div": "CFS"
            }
        )

        if not data or not data.get('list'):
            return None

        # Look for revenue breakdown accounts in the income statement
        segments = []
        total_revenue = 0

        for acct in data['list']:
            sj_nm = acct.get('sj_nm', '')  # 재무제표 구분명
            acct_nm = acct.get('account_nm', '').strip()
            amount_str = acct.get('thstrm_amount', '0')

            # Find revenue items (매출액)
            if acct_nm in ('매출액', '수익(매출액)', '영업수익'):
                try:
                    total_revenue = int(amount_str.replace(',', '').replace(' ', ''))
                except (ValueError, TypeError):
                    pass

            # Look for segment-style account names
            # Pattern: 부문별 매출, 사업부문 매출, etc.
            if sj_nm == '손익계산서' and '매출' in acct_nm and acct_nm not in ('매출액', '매출원가', '매출총이익'):
                try:
                    amount = int(amount_str.replace(',', '').replace(' ', ''))
                    if amount > 0:
                        segments.append({
                            'name': acct_nm,
                            'revenue': amount,
                            'ratio': 0.0
                        })
                except (ValueError, TypeError):
                    pass

        # Calculate ratios
        if segments and total_revenue > 0:
            for seg in segments:
                seg['ratio'] = round(seg['revenue'] / total_revenue, 4)
            return segments

        # Fallback: Try to extract from business report if available
        report_text = self.download_business_report(corp_code, bsns_year)
        if report_text:
            extracted = self._extract_segments_from_text(report_text)
            if extracted:
                return extracted

        return None

    def _extract_segments_from_text(self, text: str) -> Optional[List[Dict]]:
        """Extract segment revenue from business report text using pattern matching"""
        segments = []

        # Pattern: "부문명 매출 N억원" or "부문명 N,NNN백만원"
        import re
        # Look for table-like patterns with revenue figures
        patterns = [
            # "XX사업부 매출 N,NNN억원"
            r'([가-힣A-Za-z]+(?:사업|부문|부분|제품))\s*[:\-]?\s*매출[액]?\s*([\d,]+)\s*(?:백만원|억원)',
            # "XX부문 N,NNN (revenue amount)"
            r'([가-힣A-Za-z]+(?:사업|부문|부분))\s+([\d,]+)\s+[\d,]+\s+[\d,]+'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text[:50000])  # First 50K chars
            for name, amount_str in matches:
                try:
                    amount = int(amount_str.replace(',', ''))
                    if amount > 0:
                        segments.append({
                            'name': name.strip(),
                            'revenue': amount,
                            'ratio': 0.0
                        })
                except (ValueError, TypeError):
                    pass

        if not segments:
            return None

        # Calculate ratios
        total = sum(s['revenue'] for s in segments)
        if total > 0:
            for seg in segments:
                seg['ratio'] = round(seg['revenue'] / total, 4)

        return segments if segments else None

    # ── Business Report (DS001) ───────────────────────────────

    def get_business_report(self, corp_code: str, year: str = "2023") -> Optional[Dict]:
        """
        Get latest business report metadata (사업보고서)

        Returns report metadata including rcept_no for further processing
        """
        try:
            data = self._api_call(
                f"{self.base_url}/list.json",
                {
                    "crtfc_key": self.api_key,
                    "corp_code": corp_code,
                    "bgn_de": f"{year}0101",
                    "end_de": f"{int(year)+1}0630",
                    "pblntf_ty": "A",
                    "last_reprt_at": "Y"
                }
            )

            if not data or not data.get("list"):
                return None

            for item in data.get("list", []):
                report_nm = item.get("report_nm", "")
                if "사업보고서" in report_nm:
                    return item

            return None

        except Exception as e:
            print(f"    ❌ Error getting business report: {e}")
            return None

    def find_latest_report(self, corp_code: str) -> Optional[Dict]:
        """
        Find the latest comprehensive report (Annual or Semi-Annual).
        Prioritizes by receipt date (rcept_dt).
        
        Searches: "사업보고서", "반기보고서"
        """
        current_year = datetime.now().year
        candidates = []
        
        # Search range: Current year down to 3 years ago
        for year in range(current_year, current_year - 4, -1):
            try:
                data = self._api_call(
                    f"{self.base_url}/list.json",
                    {
                        "crtfc_key": self.api_key,
                        "corp_code": corp_code,
                        "bgn_de": f"{year}0101",
                        "end_de": f"{int(year)+1}0630",
                        "pblntf_ty": "A", # 정기공시
                        "last_reprt_at": "Y"
                    }
                )
                
                if data and data.get("list"):
                    for item in data.get("list", []):
                        nm = item.get("report_nm", "")
                        # Filter for Annual or Semi-Annual
                        if "사업보고서" in nm or "반기보고서" in nm:
                            candidates.append(item)
            except Exception:
                pass

        if not candidates:
            return None
            
        # Sort by rcept_dt (descending)
        # rcept_dt format: YYYYMMDD
        candidates.sort(key=lambda x: x.get('rcept_dt', '0'), reverse=True)
        
        latest = candidates[0]
        print(f"    ✅ Found latest report: {latest.get('report_nm')} ({latest.get('rcept_dt')})")
        return latest

    def download_business_report(
        self,
        corp_code: str,
        bsns_year: str = "2023"
    ) -> Optional[str]:
        """
        Download and extract business report full text from DART.

        Process:
        1. list.json → find 사업보고서 rcept_no
        2. document.xml → download ZIP containing full report XML(s)
        3. Extract largest XML from ZIP → strip tags → get text

        Returns: Full report text or None
        """
        # Check cache
        cached = self._load_cache(corp_code, 'report_sections')
        if cached and cached.get('year') == bsns_year and cached.get('raw_text'):
            return cached['raw_text']

        # Step 1: Get report metadata
        report = self.get_business_report(corp_code, bsns_year)
        if not report:
            print(f"    ⚠️  No business report found for {bsns_year}")
            return None

        rcept_no = report.get('rcept_no')
        if not rcept_no:
            return None

        print(f"    📄 Report: {report.get('report_nm', '')} (rcept_no: {rcept_no})")

        # Step 2: Download document.xml (DART returns ZIP with full report XML)
        time.sleep(self._api_delay)
        try:
            import zipfile
            import io

            response = self.session.get(
                f"{self.base_url}/document.xml",
                params={"crtfc_key": self.api_key, "rcept_no": rcept_no},
                timeout=60
            )

            if response.status_code != 200:
                print(f"    ⚠️  document.xml HTTP {response.status_code}")
                return None

            raw_content = response.content

            # DART returns a ZIP file containing XML documents
            if raw_content[:2] != b'PK':
                print(f"    ⚠️  document.xml response is not a ZIP file")
                return None

            zf = zipfile.ZipFile(io.BytesIO(raw_content))
            xml_names = [n for n in zf.namelist() if n.endswith('.xml')]

            if not xml_names:
                print(f"    ⚠️  No XML files found in ZIP")
                return None

            # Pick the largest XML file (= main report body)
            largest_xml = max(xml_names, key=lambda n: zf.getinfo(n).file_size)
            xml_bytes = zf.read(largest_xml)

            # Decode XML to text
            try:
                xml_data = xml_bytes.decode('utf-8', errors='ignore')
            except Exception:
                xml_data = xml_bytes.decode('euc-kr', errors='ignore')

            # Strip XML/HTML tags to get clean text
            from html import unescape
            text = re.sub(r'<[^>]+>', ' ', xml_data)
            text = unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) < 100:
                print(f"    ⚠️  Report text too short ({len(text)} chars)")
                return None

            # Truncate if too long (keep first 500K chars)
            if len(text) > 500000:
                text = text[:500000]

            print(f"    ✅ Report downloaded: {len(text):,} chars")

            # Save to cache
            self._save_cache(corp_code, 'report_sections', {
                'year': bsns_year,
                'rcept_no': rcept_no,
                'raw_text': text,
                'text_length': len(text),
                'corp_code': corp_code
            })

            return text

        except Exception as e:
            print(f"    ❌ Error downloading report: {e}")
            return None

    def download_report(self, corp_code: str, rcept_no: str) -> Optional[str]:
        """Download report text directly by rcept_no"""
        # Check cache (using rcept_no as key)
        cached = self._load_cache(corp_code, f'report_{rcept_no}')
        if cached and cached.get('raw_text'):
            return cached['raw_text']

        print(f"    📄 Downloading report (rcept_no: {rcept_no})...")
        time.sleep(self._api_delay)
        
        try:
            import zipfile
            import io
            from html import unescape

            response = self.session.get(
                f"{self.base_url}/document.xml",
                params={"crtfc_key": self.api_key, "rcept_no": rcept_no},
                timeout=60
            )

            if response.status_code != 200:
                print(f"    ⚠️  document.xml HTTP {response.status_code}")
                return None

            raw_content = response.content
            if raw_content[:2] != b'PK':
                return None

            zf = zipfile.ZipFile(io.BytesIO(raw_content))
            xml_names = [n for n in zf.namelist() if n.endswith('.xml')]

            if not xml_names:
                return None

            largest_xml = max(xml_names, key=lambda n: zf.getinfo(n).file_size)
            xml_bytes = zf.read(largest_xml)

            try:
                xml_data = xml_bytes.decode('utf-8', errors='ignore')
            except Exception:
                xml_data = xml_bytes.decode('euc-kr', errors='ignore')

            text = re.sub(r'<[^>]+>', ' ', xml_data)
            text = unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) > 500000:
                text = text[:500000]

            self._save_cache(corp_code, f'report_{rcept_no}', {
                'rcept_no': rcept_no,
                'raw_text': text,
                'fetched_at': datetime.now().isoformat()
            })
            
            return text

        except Exception as e:
            print(f"    ❌ Error downloading report {rcept_no}: {e}")
            return None

    def download_report_xml(
        self,
        corp_code: str,
        bsns_year: str = "2023"
    ) -> Optional[str]:
        """
        Download raw XML of business report (for structured parsing).
        Similar to download_business_report but returns XML string.
        """
        # Check cache
        cached = self._load_cache(corp_code, 'report_xml')
        if cached and cached.get('year') == bsns_year and cached.get('raw_xml'):
            return cached['raw_xml']

        # Reuse logic from download_business_report to get XML bytes
        # (For efficiency, we might want to refactor to share code, but this is safe for now)
        report = self.get_business_report(corp_code, bsns_year)
        if not report:
            return None

        rcept_no = report.get('rcept_no')
        if not rcept_no:
            return None

        time.sleep(self._api_delay)
        try:
            import zipfile
            import io

            response = self.session.get(
                f"{self.base_url}/document.xml",
                params={"crtfc_key": self.api_key, "rcept_no": rcept_no},
                timeout=60
            )

            if response.status_code != 200:
                return None

            raw_content = response.content
            if raw_content[:2] != b'PK':
                return None

            zf = zipfile.ZipFile(io.BytesIO(raw_content))
            xml_names = [n for n in zf.namelist() if n.endswith('.xml')]

            if not xml_names:
                return None

            largest_xml = max(xml_names, key=lambda n: zf.getinfo(n).file_size)
            xml_bytes = zf.read(largest_xml)

            try:
                xml_data = xml_bytes.decode('utf-8', errors='ignore')
            except Exception:
                xml_data = xml_bytes.decode('euc-kr', errors='ignore')

            # Save to cache
            self._save_cache(corp_code, 'report_xml', {
                'year': bsns_year,
                'rcept_no': rcept_no,
                'raw_xml': xml_data,
                'corp_code': corp_code
            })

            return xml_data

        except Exception as e:
            print(f"    ❌ Error downloading XML: {e}")
            return None

    # ── Legacy Methods (backward compatible) ──────────────────

    def get_business_description(self, corp_code: str, rcept_no: str = None) -> Optional[str]:
        """Get business description from company info (legacy)"""
        try:
            company_info = self.get_company_info(corp_code)
            if not company_info:
                return None

            desc_parts = []
            if company_info.get('induty_code'):
                desc_parts.append(f"업종코드: {company_info['induty_code']}")
            if company_info.get('est_dt'):
                desc_parts.append(f"설립일: {company_info['est_dt']}")
            if company_info.get('hm_url'):
                desc_parts.append(f"홈페이지: {company_info['hm_url']}")

            return " | ".join(desc_parts) if desc_parts else None

        except Exception as e:
            print(f"    ❌ Error getting business description: {e}")
            return None

    def analyze_stock(self, stock_code: str) -> Optional[Dict]:
        """
        Complete analysis pipeline for single stock (legacy + extended)

        Returns basic company info + extended data flags
        """
        print(f"  📄 Fetching DART data for {stock_code}...")

        # Step 1: Get corp_code (cached)
        corp_code = self.get_corp_code(stock_code)
        if not corp_code:
            print(f"    ❌ Corp code not found")
            return None

        print(f"    ✅ Corp code: {corp_code}")

        # Step 2: Get company info (cached)
        company_info = self.get_company_info(corp_code)
        if not company_info:
            print(f"    ❌ Company info not found")
            return None

        # Step 3: Extract business information
        corp_name = company_info.get('corp_name', '')
        industry_code = company_info.get('induty_code', '')
        est_dt = company_info.get('est_dt', '')
        homepage = company_info.get('hm_url', '')

        business_desc = f"업종: {industry_code}"
        if est_dt:
            business_desc += f" | 설립: {est_dt}"
        if homepage:
            business_desc += f" | {homepage}"

        print(f"    ✅ Industry: {industry_code}")
        print(f"    ✅ Company: {corp_name}")

        return {
            'corp_code': corp_code,
            'corp_name': corp_name,
            'industry_code': industry_code,
            'business_desc': business_desc,
            'homepage': homepage
        }


# Test function
if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from config import get_dart_api_key

    try:
        api_key = get_dart_api_key()
    except ValueError as e:
        print(str(e))
        exit(1)

    client = DARTClient(api_key)

    # Test with 삼성전자
    print("=" * 60)
    print("DART Client Extended Test")
    print("=" * 60)

    result = client.analyze_stock("005930")

    if result:
        print(f"\n✅ Basic Info:")
        print(f"  Corp Code: {result['corp_code']}")
        print(f"  Company: {result['corp_name']}")
        print(f"  Industry: {result['industry_code']}")

        # Test financial statements
        print(f"\n📊 Financial Statements:")
        fin = client.get_financial_statements(result['corp_code'], "2023")
        if fin:
            print(f"  Revenue: {fin.get('revenue', 0):,}")
            print(f"  Operating Income: {fin.get('operating_income', 0):,}")
            print(f"  Operating Margin: {fin.get('operating_margin', 0):.1%}")
            print(f"  ROE: {fin.get('roe', 0):.1%}")
        else:
            print("  ❌ Financial data not available")

        # Test business report download
        print(f"\n📄 Business Report:")
        report_text = client.download_business_report(result['corp_code'], "2023")
        if report_text:
            print(f"  Text length: {len(report_text):,} chars")
            print(f"  Preview: {report_text[:200]}...")
        else:
            print("  ❌ Report not available")
    else:
        print("❌ Analysis failed")
