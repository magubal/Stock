"""
Parallel Evidence-Based Moat Analysis
Optimized for speed using ThreadPoolExecutor.
"""

import sys
import os
import argparse
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import List, Dict

# Add paths
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from analyze_with_evidence import EvidenceBasedMoatPipeline
from excel_io import ExcelIO

class ParallelAnalyzer:
    def __init__(self, workers: int = 3, year: str = 'auto'):
        self.workers = workers
        self.target_year = year
        self.pipeline = EvidenceBasedMoatPipeline()
        # Disable internal prints for cleaner batch output
        # (Optional: redirect stdout or modify pipeline to be silent)

    def process_stock(self, row) -> Dict:
        ticker = str(row.get('ticker', '')).strip()
        name = str(row.get('name', '')).strip()
        
        if not ticker or not name:
            return None
            
        try:
            # Re-instantiate pipeline per thread if not thread-safe? 
            # DARTClient uses requests.Session which is not strictly thread-safe
            # But we are just reading mainly. Let's try shared pipeline first.
            # actually, let's create a new pipeline instance per thread to be safe
            # regarding session state.
            local_pipeline = EvidenceBasedMoatPipeline()
            year = getattr(self, 'target_year', 'auto')
            result = local_pipeline.analyze_stock(ticker, name, year=year)
            return result
        except Exception as e:
            return {
                'ticker': ticker, 
                'name': name, 
                'status': 'failed', 
                'error': str(e)
            }

    def run_batch(self, excel_path: str, limit: int = 0, force: bool = False, start_from: int = 0):
        excel = ExcelIO(excel_path)
        df = excel.load_stock_data()
        
        if force:
            target = df.copy()
            print(f"📊 Force mode: processing ALL {len(target)} stocks")
        else:
            target = excel.get_incomplete_stocks(df)
            
        if start_from > 0:
            target = target.iloc[start_from:]
        
        if limit > 0:
            target = target.head(limit)
            
        print(f"🚀 Starting Parallel Analysis with {self.workers} workers")
        print(f"TARGET: {len(target)} stocks")
        
        # Pre-warm cache to avoid race conditions on initial download
        print("🔥 Pre-warming DART cache...")
        warmup_pipeline = EvidenceBasedMoatPipeline()
        warmup_pipeline.dart.get_corp_code("005930") # Samsung Electronics
        
        results = []
        updates = []
        
        # Convert DataFrame rows to list of dicts for iteration
        rows = [row for _, row in target.iterrows()]
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_stock = {executor.submit(self.process_stock, row): row for row in rows}
            
            # Process as they complete
            for future in tqdm(as_completed(future_to_stock), total=len(rows)):
                row = future_to_stock[future]
                name = row.get('name')
                
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        
                        if result.get('status') == 'success':
                            # Prepare Excel update
                            update_data = {
                                'core_sector_top': result.get('core_sector_top', ''),
                                'core_sector_sub': result.get('core_sector_sub', ''),
                                'core_desc': result.get('core_desc', ''),
                                '해자강도': result.get('해자강도', 1),
                                '해자DESC': result.get('해자DESC', ''),
                                '검증용desc': result.get('검증용desc', ''),
                                'evidence_summary': result.get('evidence_summary', ''),
                                'bm_summary': result.get('bm_summary', ''),
                                'sustainability_notes': result.get('sustainability_notes', ''),
                                'ai_review': result.get('ai_review', ''),
                                'evidence_count': result.get('evidence_count', 0),
                                'evidence_quality': result.get('evidence_quality', 0.0),
                                'bm_completeness': result.get('bm_completeness', 0.0),
                            }
                            updates.append({'ticker': result['ticker'], 'data': update_data})
                            
                except Exception as e:
                    print(f"❌ Exception for {name}: {e}")

        # Batch Save
        if updates:
            print(f"\n📝 Saving {len(updates)} results to Excel...")
            # Use efficient batch update
            excel.batch_update_stocks(updates, mode='efficient')
            
        print("✅ Analysis Complete")
        return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch', required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--start-from', type=int, default=0)
    parser.add_argument('--year', type=str, default='auto')
    
    args = parser.parse_args()
    
    analyzer = ParallelAnalyzer(workers=args.workers, year=args.year)
    analyzer.run_batch(args.batch, args.limit, args.force, args.start_from)
