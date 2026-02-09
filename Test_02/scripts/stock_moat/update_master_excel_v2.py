
import sys
import os
import pandas as pd
import time
from tqdm import tqdm

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}")
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")

from dart_client import DARTClient
from dart_report_parser import DartReportParser
from bm_analyzer import BMAnalyzer
from moat_evaluator_v2 import MoatEvaluatorV2
from moat_report_generator import MoatReportGenerator
from evidence_extractor import EvidenceCollection # Simple Stub
from config import get_dart_api_key

# Stub for Evidence Collection (until Phase 4 NLP is ready)
class SimpleEvidenceCollection(EvidenceCollection):
    def __init__(self):
        self.evidences = []
    def get_by_type(self, type_name):
        return [e for e in self.evidences if e.moat_type == type_name]

def process_all_stocks(input_excel, output_excel, limit=None):
    print(f"📂 Loading {input_excel}...")
    try:
        df = pd.read_excel(input_excel)
    except FileNotFoundError:
        print("❌ Input file not found!")
        return

    # Check for required columns
    required_cols = ['종목명', '종목코드']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Missing column: {col}")
            return

    # Setup Components
    api_key = get_dart_api_key()
    client = DARTClient(api_key)
    parser = DartReportParser()
    bm_analyzer = BMAnalyzer()
    evaluator = MoatEvaluatorV2()
    # reporter = MoatReportGenerator() # Optional: generate individual reports?

    print(f"🚀 Starting analysis for {len(df)} stocks...")
    
    if limit:
        print(f"⚠️ Limit set to {limit} stocks for testing.")
        df = df.head(limit)
    
    # New columns
    results = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        name = row['종목명']
        code = str(row['종목코드']).zfill(6) # Ensure 6 digits
        
        # Skip KOSDAQ small caps (Optional optimization, maybe user wants all)
        # market = row.get('시장구분', '')
        # if 'KOSDAQ' in market and ...
        
        try:
            # 1. Get Data
            corp_code = client.get_corp_code(code)
            if not corp_code:
                results.append({'moat_score': 1, 'note': 'CorpCode Not Found'})
                continue
                
            financials = client.get_financial_statements(corp_code, "2023")
            if not financials:
                 financials = {} # Run with empty financials (will likely fail checks)
                 
            segments = client.get_segment_revenue(corp_code, "2023")
            
            # Report Text (Try to get XML)
            # Only fetch if we suspect moat potential or blindly?
            # Blind fetch is safe but slow. 
            # Optimization: Check financials first. If Rev < 500억/Deficit, maybe skip report download?
            # Let's simple check: if deficit, probably no moat.
            if financials.get('operating_income', 0) < 0:
                 # Skip verifying report for deficit companies (Cost saving)
                 # But Namkwang had deficit? No, small profit.
                 # Let's download anyway to be safe.
                 pass

            xml_text = client.download_report_xml(corp_code, "2023")
            if xml_text:
                report_sections = parser.parse(xml_text)
            else:
                report_sections = {}

            # 2. Analyze
            bm = bm_analyzer.analyze(name, code, report_sections, financials, segments)
            
            # 3. Simulate Evidence (Stub)
            evidences = SimpleEvidenceCollection()
            
            # 4. Evaluate
            # Use existing GICS info if available in row
            classification = {
                'gics_sector': row.get('GICS Sector', ''),
                'gics_industry': row.get('GICS Industry', '')
            }
            
            evaluation = evaluator.evaluate(name, code, evidences, bm, financials, classification)
            
            # 5. Store Result
            results.append({
                'moat_score_v2': evaluation.moat_strength,
                'evidence_based': evaluation.evidence_based,
                'bm_summary': bm_analyzer.generate_bm_summary(bm),
                'moat_desc_v2': evaluation.moat_desc,
                'risks': '; '.join(evaluation.sustainability.get('warnings', [])) if evaluation.sustainability else ""
            })
            
            # Sleep to respect rate limits (DART is strict)
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"❌ Error on {name}: {e}")
            results.append({'moat_score_v2': 0, 'note': f"Error: {str(e)}"})
            time.sleep(1)

    # Merge results back to DF
    result_df = pd.DataFrame(results)
    final_df = pd.concat([df.reset_index(drop=True), result_df], axis=1)
    
    print(f"💾 Saving to {output_excel}...")
    final_df.to_excel(output_excel, index=False)
    print("✅ Done!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit", default=None)
    args = parser.parse_args()

    input_file = "data/MGB_daily/stock_core_master_v2_korean_taxonomy_2026-01-30.xlsx"
    output_file = f"data/MGB_daily/stock_moat_v2_results_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
    
    if not os.path.exists(input_file):
        # Fallback to search if path is wrong? No, we found it.
        # But maybe path separator issue?
        pass

    process_all_stocks(input_file, output_file, limit=args.limit)
