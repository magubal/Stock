"""
Test DART API Key Validity
"""
import requests
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / ".agent/skills/stock-moat/utils"))

from config import get_dart_api_key

def test_dart_api():
    """Test if DART API key is valid"""

    print("="*60)
    print("DART API 테스트")
    print("="*60)

    # Get API key
    try:
        api_key = get_dart_api_key()
        print(f"\n✅ API Key loaded: {api_key[:10]}...{api_key[-10:]}")
    except Exception as e:
        print(f"\n❌ Failed to load API key: {e}")
        return

    # Test corpCode.xml download
    print("\n1. Testing corpCode.xml download...")
    url = "https://opendart.fss.or.kr/api/corpCode.xml"
    params = {"crtfc_key": api_key}

    try:
        response = requests.get(url, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {len(response.content)} bytes")

        # Check if it's a ZIP file
        if response.content[:2] == b'PK':
            print("   ✅ Response is a valid ZIP file")

            # Try to extract
            import zipfile
            import io
            try:
                zip_file = zipfile.ZipFile(io.BytesIO(response.content))
                files = zip_file.namelist()
                print(f"   ✅ ZIP contents: {files}")

                # Read CORPCODE.xml
                xml_content = zip_file.read('CORPCODE.xml')
                print(f"   ✅ CORPCODE.xml size: {len(xml_content)} bytes")

                # Parse XML and find Samsung
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml_content)

                found = False
                for corp in root.findall('list'):
                    stock_code_elem = corp.find('stock_code')
                    if stock_code_elem is not None and stock_code_elem.text == '005930':
                        corp_code_elem = corp.find('corp_code')
                        corp_name_elem = corp.find('corp_name')
                        print(f"\n   ✅ 삼성전자 found!")
                        print(f"      Corp Code: {corp_code_elem.text if corp_code_elem is not None else 'N/A'}")
                        print(f"      Corp Name: {corp_name_elem.text if corp_name_elem is not None else 'N/A'}")
                        found = True
                        break

                if not found:
                    print(f"   ⚠️  삼성전자 not found in corpCode.xml")

            except zipfile.BadZipFile as e:
                print(f"   ❌ Invalid ZIP file: {e}")

        else:
            print(f"   ❌ Response is NOT a ZIP file")
            print(f"   First 200 bytes: {response.content[:200]}")

            # Check if it's an error message
            try:
                error_text = response.content.decode('utf-8')
                print(f"   Error message: {error_text[:500]}")
            except:
                pass

    except Exception as e:
        print(f"   ❌ Request failed: {e}")

    print("\n" + "="*60)
    print("테스트 완료")
    print("="*60)

if __name__ == "__main__":
    test_dart_api()
