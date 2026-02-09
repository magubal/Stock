"""
DART API Integration for Stock Moat Estimator
Fetches corporate disclosure data from DART (금융감독원 전자공시시스템)
"""

import requests
import time
import sys
from typing import Dict, Optional, List

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class DARTAPI:
    """DART API client with retry logic"""

    BASE_URL = "https://opendart.fss.or.kr"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _request_with_retry(
        self,
        endpoint: str,
        params: Dict
    ) -> Optional[Dict]:
        """Make API request with exponential backoff retry"""
        params['crtfc_key'] = self.api_key

        for attempt in range(self.max_retries):
            try:
                url = f"{self.BASE_URL}{endpoint}"
                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()

                    # Check for API errors
                    if data.get('status') == '000':  # Success
                        return data
                    elif data.get('status') == '013':  # No data
                        print(f"⚠️  No data available")
                        return None
                    else:
                        print(f"⚠️  API error: {data.get('message')}")
                        return None

                elif response.status_code == 429:  # Rate limit
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                else:
                    print(f"❌ HTTP {response.status_code}")
                    return None

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"⏳ Timeout, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Timeout after {self.max_retries} attempts")
                    return None

            except Exception as e:
                print(f"❌ Request error: {e}")
                return None

        return None

    def get_company_info(self, corp_code: str) -> Optional[Dict]:
        """
        Get basic company information

        Args:
            corp_code: DART corp_code (8-digit)

        Returns:
            {
                'corp_name': '삼성전자',
                'corp_code': '00126380',
                'stock_code': '005930',
                'ceo_nm': '한종희',
                'induty_code': '264',
                'hm_url': 'www.samsung.com',
                'ir_url': 'https://...'
            }
        """
        endpoint = "/api/company.json"
        params = {'corp_code': corp_code}

        data = self._request_with_retry(endpoint, params)
        return data if data else None

    def get_corp_code_by_stock_code(self, stock_code: str) -> Optional[str]:
        """
        Get corp_code from stock_code

        Note: This requires loading the full corp code list
        For efficiency, we'll use a different approach (search by name)
        """
        # TODO: Implement corp_code mapping
        # For now, use web search or cached mapping
        pass

    def search_company(self, company_name: str) -> Optional[List[Dict]]:
        """
        Search company by name

        Args:
            company_name: Company name (e.g., '삼성전자')

        Returns:
            List of matching companies with corp_code
        """
        endpoint = "/api/list.json"
        params = {'corp_name': company_name}

        data = self._request_with_retry(endpoint, params)

        if data and 'list' in data:
            return data['list']

        return None

    def get_business_report(
        self,
        corp_code: str,
        year: str = "2024",
        report_code: str = "11011"  # Annual report
    ) -> Optional[Dict]:
        """
        Get business report (사업보고서)

        Args:
            corp_code: DART corp_code
            year: Report year
            report_code: 11011 (annual), 11012 (half), 11013 (quarter), 11014 (quarter)

        Returns:
            Business report data including 사업의 내용
        """
        endpoint = "/api/fnlttSinglAcntAll.json"
        params = {
            'corp_code': corp_code,
            'bsns_year': year,
            'reprt_code': report_code
        }

        data = self._request_with_retry(endpoint, params)
        return data

    def get_business_description(
        self,
        corp_code: str,
        year: str = "2024"
    ) -> Optional[str]:
        """
        Extract business description from annual report

        This is a simplified version.
        Full implementation would parse the actual report text.
        """
        report = self.get_business_report(corp_code, year)

        if not report:
            return None

        # Extract business summary
        # Note: Actual implementation needs HTML parsing
        # For MVP, we'll use company info endpoint

        company_info = self.get_company_info(corp_code)
        if company_info:
            # DART API doesn't directly provide business description
            # We'll need to use web scraping or other sources
            return f"Company: {company_info.get('corp_name')}"

        return None


# Test function
if __name__ == "__main__":
    # Load API key
    import os

    # Hard-coded for testing
    api_key = '7f7abfddcd974b4d07de58eb46b602ca22d0e45d'

    print(f"🔑 DART API Key: {api_key[:10]}...")

    dart = DARTAPI(api_key)

    # Test: Search Samsung Electronics
    print("\n🔍 Testing company search...")
    results = dart.search_company('삼성전자')
    if results:
        print(f"✅ Found {len(results)} results")
        for r in results[:3]:
            print(f"  - {r.get('corp_name')} ({r.get('stock_code')}): {r.get('corp_code')}")
    else:
        print("❌ Search failed")

    # Test: Get company info
    if results and len(results) > 0:
        corp_code = results[0]['corp_code']
        print(f"\n📄 Testing company info for {corp_code}...")
        info = dart.get_company_info(corp_code)
        if info:
            print(f"✅ Company: {info.get('corp_name')}")
            print(f"   CEO: {info.get('ceo_nm')}")
            print(f"   Homepage: {info.get('hm_url')}")
            print(f"   IR: {info.get('ir_url')}")
        else:
            print("❌ Failed to get company info")
