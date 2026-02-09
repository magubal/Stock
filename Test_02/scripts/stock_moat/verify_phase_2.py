
import sys
import os
import json

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}")
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from dart_client import DARTClient
from dart_report_parser import DartReportParser
from bm_analyzer import BMAnalyzer
from config import get_dart_api_key

def verify_bm_extraction():
    print("=" * 60)
    print("Verification: Phase 2 BM Extraction (Real Data)")
    print("=" * 60)

    api_key = get_dart_api_key()
    client = DARTClient(api_key)
    parser = DartReportParser()
    analyzer = BMAnalyzer()

    targets = [
        ("Samsung Electronics", "005930"), 
        ("Namkwang Engineering", "001260")
    ]

    for name, code in targets:
        print(f"\nAnalyzing {name} ({code})...")
        
        # 1. Get Corp Code
        corp_code = client.get_corp_code(code)
        if not corp_code:
            print(f"❌ Failed to find corp code for {code}")
            continue
            
        # 2. Download Report XML (Phase 1)
        print("  📥 Downloading Report XML...")
        xml_text = client.download_report_xml(corp_code, "2023")
        if not xml_text:
            print("  ❌ Failed to download report XML")
            continue
            
        # 3. Parse Sections (Phase 1)
        print(f"  📖 Parsing {len(xml_text):,} chars...")
        sections = parser.parse(xml_text)
        if not sections.get('business_all') and not sections.get('business_summary'):
            print("  ❌ Failed to parse business section")
            continue
        print(f"     Found Business Section: {len(sections.get('business_all', '')):,} chars")
            
        # 4. Get Financials (Phase 1)
        print("  💰 Fetching Financials...")
        financials = client.get_financial_statements(corp_code, "2023")
        if not financials:
            print("  ⚠️ Financials not found (using empty)")
            financials = {}
            
        # 5. Get Segments (Phase 1)
        print("  📊 Fetching Segments...")
        segments = client.get_segment_revenue(corp_code, "2023")
        if segments:
            print(f"     Segments: {[s['name'] for s in segments]}")
        else:
            print("     Segments: None")
            
        # 6. Run BM Analyzer (Phase 2)
        print("  🧠 Running BM Analyzer...")
        bm = analyzer.analyze(name, code, sections, financials, segments)
        
        # 7. Print Result
        print("-" * 40)
        print(analyzer.generate_bm_summary(bm))
        print("-" * 40)
        
        # Validation
        confirmed_count = sum(1 for e in bm.elements_list if e and e.label == 'confirmed')
        print(f"  ✅ Completeness: {confirmed_count}/6 confirmed elements")

if __name__ == "__main__":
    verify_bm_extraction()
