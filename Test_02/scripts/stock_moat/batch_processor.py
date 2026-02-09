"""
Batch Processor for Stock Moat Analysis
Processes multiple stocks with progress tracking
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import List, Dict

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from excel_io import ExcelIO
from moat_analyzer import MoatAnalyzer


class BatchProcessor:
    """Process multiple stocks with checkpointing"""

    def __init__(self, mode: str = 'sequential'):
        self.mode = mode  # 'sequential' or 'parallel'
        self.excel_path = f"{project_root}/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"
        self.status_file = f"{project_root}/data/stock_moat/.stock-moat-status.json"
        self.excel_io = ExcelIO(self.excel_path)
        self.analyzer = MoatAnalyzer()

        # Ensure status directory exists
        os.makedirs(os.path.dirname(self.status_file), exist_ok=True)

        # Load or create status
        self.status = self._load_status()

    def _load_status(self) -> Dict:
        """Load processing status from file"""
        if os.path.exists(self.status_file):
            with open(self.status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                'version': '1.0.0',
                'total_stocks': 0,
                'completed_stocks': 0,
                'failed_stocks': 0,
                'in_progress_stocks': [],
                'current_batch': 0,
                'last_updated': datetime.now().isoformat(),
                'high_moat_stocks': [],
                'needs_verification': []
            }

    def _save_status(self):
        """Save status to file"""
        self.status['last_updated'] = datetime.now().isoformat()
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, ensure_ascii=False, indent=2)

    def process_batch(
        self,
        start_idx: int = 0,
        count: int = 10,
        auto_save: bool = True,
        skip_completed: bool = True,
        batch_update_mode: str = 'efficient'  # 'efficient' or 'safe'
    ) -> Dict:
        """
        Process a batch of stocks

        Args:
            start_idx: Starting index
            count: Number of stocks to process
            auto_save: Auto-save to Excel
            skip_completed: Skip already completed stocks
            batch_update_mode: 'efficient' (batch) or 'safe' (one-by-one)

        Returns:
            {
                'success': count,
                'failed': count,
                'skipped': count,
                'results': [...]
            }
        """
        # Load incomplete stocks
        df = self.excel_io.load_stock_data()
        incomplete = self.excel_io.get_incomplete_stocks(df)

        # Select batch
        batch = incomplete.iloc[start_idx:start_idx + count]

        print(f"\n{'='*60}")
        print(f"📦 Batch Processing")
        print(f"{'='*60}")
        print(f"Mode: {self.mode.upper()}")
        print(f"Range: {start_idx} - {start_idx + len(batch)}")
        print(f"Stocks: {len(batch)}")
        print(f"{'='*60}\n")

        results = {
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }

        # Collect results for batch update
        batch_updates = []

        # Process each stock (analysis only)
        for idx, (row_idx, stock) in enumerate(batch.iterrows(), start=1):
            ticker = stock['ticker']
            name = stock['name']

            print(f"\n[{idx}/{len(batch)}] Analyzing: {name} ({ticker})")

            try:
                # Analyze (without saving)
                result = self.analyzer.analyze_stock(
                    ticker=ticker,
                    name=name,
                    auto_save=False  # Don't save yet
                )

                results['results'].append(result)

                # Prepare for batch update
                if auto_save:
                    update_data = {k: v for k, v in result.items()
                                   if k not in ['confidence', 'ticker', 'name']}
                    batch_updates.append({
                        'ticker': ticker,
                        'data': update_data
                    })

                # Track high moat stocks
                if result['해자강도'] >= 4:
                    self.status['high_moat_stocks'].append(ticker)
                    self.status['needs_verification'].append({
                        'ticker': ticker,
                        'name': name,
                        'moat_strength': result['해자강도']
                    })

                # Update progress
                self.status['completed_stocks'] += 1
                results['success'] += 1

                # Small delay for sequential mode
                if self.mode == 'sequential':
                    time.sleep(0.2)

            except Exception as e:
                print(f"❌ Error: {e}")
                results['failed'] += 1

        # Batch update Excel (once for entire batch)
        if auto_save and len(batch_updates) > 0:
            print(f"\n{'='*60}")
            print(f"💾 Batch saving {len(batch_updates)} stocks to Excel...")
            print(f"{'='*60}\n")

            batch_results = self.excel_io.batch_update_stocks(
                batch_updates,
                mode=batch_update_mode
            )

            print(f"✅ Batch saved: {batch_results['success']} stocks")
            if batch_results['failed'] > 0:
                print(f"❌ Failed: {batch_results['failed']} stocks")

        # Final save
        self._save_status()

        print(f"\n{'='*60}")
        print(f"✅ Batch Complete")
        print(f"{'='*60}")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"{'='*60}\n")

        return results

    def process_all(self, batch_size: int = 10, auto_save: bool = True):
        """Process all incomplete stocks in batches"""
        df = self.excel_io.load_stock_data()
        incomplete = self.excel_io.get_incomplete_stocks(df)

        total = len(incomplete)
        self.status['total_stocks'] = total

        print(f"\n{'='*60}")
        print(f"🚀 Processing ALL Stocks")
        print(f"{'='*60}")
        print(f"Total: {total} stocks")
        print(f"Batch size: {batch_size}")
        print(f"Mode: {self.mode}")
        print(f"{'='*60}\n")
        print(f"✅ Auto-confirming batch processing...\n")

        # Process in batches
        start_time = time.time()
        batch_count = 0

        for i in range(0, total, batch_size):
            batch_count += 1
            self.status['current_batch'] = batch_count

            print(f"\n📦 Batch {batch_count}/{(total + batch_size - 1) // batch_size}")

            self.process_batch(
                start_idx=i,
                count=batch_size,
                auto_save=auto_save
            )

            # Estimate remaining time
            elapsed = time.time() - start_time
            completed = self.status['completed_stocks']
            if completed > 0:
                avg_time = elapsed / completed
                remaining = (total - completed) * avg_time
                print(f"\n⏱️  Estimated remaining: {remaining / 60:.1f} minutes\n")

        # Final report
        end_time = time.time()
        total_time = end_time - start_time

        print(f"\n{'='*60}")
        print(f"🎉 ALL DONE!")
        print(f"{'='*60}")
        print(f"Total processed: {self.status['completed_stocks']}")
        print(f"High moat stocks (≥4): {len(self.status['high_moat_stocks'])}")
        print(f"Total time: {total_time / 60:.1f} minutes")
        print(f"{'='*60}\n")

        # Save final status
        self._save_status()

    def show_status(self):
        """Display current processing status"""
        print(f"\n{'='*60}")
        print(f"📊 Stock Moat Analysis Status")
        print(f"{'='*60}")
        print(f"Total: {self.status['total_stocks']}")
        print(f"Completed: {self.status['completed_stocks']}")
        print(f"Failed: {self.status['failed_stocks']}")
        print(f"Current batch: {self.status['current_batch']}")
        print(f"Last updated: {self.status['last_updated']}")
        print(f"{'='*60}")
        print(f"High moat stocks (≥4): {len(self.status['high_moat_stocks'])}")
        print(f"Needs verification: {len(self.status['needs_verification'])}")
        print(f"{'='*60}\n")


# CLI Interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Batch process stock moat analysis')
    parser.add_argument('--mode', choices=['sequential', 'parallel'], default='sequential',
                        help='Processing mode')
    parser.add_argument('--batch', type=int, default=10,
                        help='Batch size')
    parser.add_argument('--start', type=int, default=0,
                        help='Start index')
    parser.add_argument('--count', type=int, default=10,
                        help='Number of stocks to process')
    parser.add_argument('--all', action='store_true',
                        help='Process all incomplete stocks')
    parser.add_argument('--status', action='store_true',
                        help='Show current status')

    args = parser.parse_args()

    processor = BatchProcessor(mode=args.mode)

    if args.status:
        processor.show_status()
    elif args.all:
        processor.process_all(batch_size=args.batch, auto_save=True)
    else:
        processor.process_batch(
            start_idx=args.start,
            count=args.count,
            auto_save=True
        )
