
import sys
import os

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}")
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from dart_client import DARTClient
from dart_report_parser import DartReportParser
from bm_analyzer import BMAnalyzer
from moat_evaluator_v2 import MoatEvaluatorV2
from moat_report_generator import MoatReportGenerator
from evidence_extractor import EvidenceCollection  # We need a stub or simple implementation for now if not exists
from config import get_dart_api_key

# Simple Evidence Collection Stub if the full module isn't ready
class SimpleEvidenceCollection(EvidenceCollection):
    def __init__(self):
        self.evidences = []
    def get_by_type(self, type_name):
        return [e for e in self.evidences if e.moat_type == type_name]

def run_full_analysis(stock_name, stock_code):
    print("="*60)
    print(f"🚀 Starting Full Analysis: {stock_name} ({stock_code})")
    print("="*60)

    # 1. Setup
    api_key = get_dart_api_key()
    client = DARTClient(api_key)
    parser = DartReportParser()
    bm_analyzer = BMAnalyzer()
    evaluator = MoatEvaluatorV2()
    reporter = MoatReportGenerator()
    
    # 2. Phase 1: Data Gathering
    print("Step 1: Data Gathering (DART)...")
    corp_code = client.get_corp_code(stock_code)
    if not corp_code:
        print("❌ Corp code not found")
        return

    # Financials
    financials = client.get_financial_statements(corp_code, "2023")
    segments = client.get_segment_revenue(corp_code, "2023")
    
    # Report Text
    xml_text = client.download_report_xml(corp_code, "2023")
    if not xml_text:
        print("❌ Failed to download report")
        report_sections = {}
    else:
        report_sections = parser.parse(xml_text)
        print(f"   - Business Section: {len(report_sections.get('business_all','')):,} chars")

    # 3. Phase 2: BM Decomposition
    print("Step 2: BM Decomposition...")
    bm = bm_analyzer.analyze(stock_name, stock_code, report_sections, financials, segments)
    print(f"   - BM Completeness: {bm.completeness:.0%}")

    # 4. Phase 3: Moat Evaluation
    # For now, we simulate evidence collection based on BM results 
    # (Real evidence extractor would use NLP/Rules here)
    print("Step 3: Moat Evaluation...")
    evidences = SimpleEvidenceCollection()
    
    # ... (Here we would add logic to convert BM findings to Evidences) ...
    # This part is a simplified bridge for the V2 evaluator
    
    # Mock classification for now
    classification = {'gics_sector': 'Unknown', 'gics_industry': 'Unknown'} 
    
    evaluation = evaluator.evaluate(stock_name, stock_code, evidences, bm, financials, classification)
    print(f"   - Moat Score: {evaluation.moat_strength}/5")

    # 5. Reporting
    print("Step 4: Generating Report...")
    report_md = reporter.generate_report(stock_name, stock_code, evaluation, bm, financials)
    
    # Save report
    output_dir = f"data/reports/{stock_name}_{stock_code}"
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/report.md", "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"✅ Report saved to {output_dir}/report.md")
    print("\n--- Report Preview ---")
    print(report_md[:500] + "...")

if __name__ == "__main__":
    targets = [
        ("Samsung Electronics", "005930"), 
        ("Namkwang Engineering", "001260")
    ]
    for name, code in targets:
        run_full_analysis(name, code)
        print("\n\n")
