"""
Excel I/O Module for Stock Moat Estimator
Handles safe read/write operations on Excel file
"""

import pandas as pd
import os
import shutil
import sys
from datetime import datetime
from typing import Dict, Optional, List

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


class ExcelIO:
    """Safe Excel I/O with atomic operations"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.backup_path = f"{file_path}.backup"

    def load_stock_data(self) -> pd.DataFrame:
        """Load stock_core_master sheet"""
        try:
            df = pd.read_excel(
                self.file_path,
                sheet_name='stock_core_master',
                engine='openpyxl'
            )
            print(f"✅ Loaded {len(df)} stocks from Excel")
            return df
        except Exception as e:
            print(f"❌ Error loading Excel: {e}")
            raise

    def load_sector_taxonomy(self) -> List[str]:
        """Load 229 sector categories from 분류유형(참고) sheet"""
        try:
            df = pd.read_excel(
                self.file_path,
                sheet_name='분류유형(참고)',
                engine='openpyxl'
            )
            # Extract core_sector_top column
            sectors = df['core_sector_top'].dropna().unique().tolist()
            print(f"✅ Loaded {len(sectors)} sector categories")
            return sectors
        except Exception as e:
            print(f"❌ Error loading sector taxonomy: {e}")
            raise

    def get_incomplete_stocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter stocks with missing moat data"""
        incomplete = df[
            df['core_sector_top'].isna() |
            df['해자강도'].isna()
        ].copy()
        print(f"📊 Found {len(incomplete)} incomplete stocks")
        return incomplete

    def get_stock_by_ticker(self, ticker: str) -> Optional[Dict]:
        """Get single stock data by ticker"""
        df = self.load_stock_data()
        stock_row = df[df['ticker'] == ticker]

        if stock_row.empty:
            print(f"❌ Stock {ticker} not found")
            return None

        return stock_row.iloc[0].to_dict()

    def update_stock_row(
        self,
        ticker: str,
        data: Dict,
        create_backup: bool = True
    ) -> bool:
        """
        Atomic update of single stock row

        Args:
            ticker: Stock code
            data: Fields to update {
                'core_sector_top': '반도체',
                'core_sector_sub': '메모리/시스템반도체',
                'core_desc': '...',
                '해자강도': 4,
                '해자DESC': '...',
                '검증용desc': '...'
            }
            create_backup: Whether to create backup before write

        Returns:
            True if successful, False otherwise
        """
        try:
            # 1. Create backup
            if create_backup:
                shutil.copy2(self.file_path, self.backup_path)
                print(f"📦 Backup created: {self.backup_path}")

            # 2. Load Excel
            with pd.ExcelFile(self.file_path, engine='openpyxl') as xls:
                df = pd.read_excel(xls, sheet_name='stock_core_master')

            # 3. Find row index
            row_idx = df[df['ticker'] == ticker].index
            if len(row_idx) == 0:
                print(f"❌ Ticker {ticker} not found")
                return False

            row_idx = row_idx[0]

            # 4. Update fields
            for field, value in data.items():
                if field in df.columns:
                    df.at[row_idx, field] = value
                    print(f"  ✏️  {field}: {value}")

            # 5. Write back to Excel
            with pd.ExcelWriter(
                self.file_path,
                engine='openpyxl',
                mode='a',
                if_sheet_exists='overlay'
            ) as writer:
                df.to_excel(writer, sheet_name='stock_core_master', index=False)

            print(f"✅ Updated ticker {ticker}")

            # 6. Remove backup if successful
            if create_backup and os.path.exists(self.backup_path):
                os.remove(self.backup_path)

            return True

        except Exception as e:
            print(f"❌ Error updating Excel: {e}")

            # Restore from backup
            if create_backup and os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.file_path)
                print(f"🔄 Restored from backup")

            raise

    def batch_update_stocks(
        self,
        updates: List[Dict],
        mode: str = 'efficient'
    ) -> Dict[str, int]:
        """
        Batch update multiple stocks

        Args:
            updates: List of {
                'ticker': '005930',
                'data': { ... }
            }
            mode: 'safe' (one-by-one) or 'efficient' (single Excel operation)

        Returns:
            {'success': count, 'failed': count}
        """
        results = {'success': 0, 'failed': 0}

        if mode == 'safe':
            # Original: One-by-one update
            for update in updates:
                ticker = update['ticker']
                data = update['data']

                try:
                    if self.update_stock_row(ticker, data):
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    print(f"❌ Failed to update {ticker}: {e}")
                    results['failed'] += 1

        elif mode == 'efficient':
            # New: Single Excel operation for entire batch
            try:
                # 1. Create backup
                shutil.copy2(self.file_path, self.backup_path)
                print(f"📦 Batch backup created")

                # 2. Load Excel once
                import pandas as pd
                with pd.ExcelFile(self.file_path, engine='openpyxl') as xls:
                    df = pd.read_excel(xls, sheet_name='stock_core_master')

                # 3. Ensure columns can accept mixed types
                # Convert text columns to object dtype to avoid dtype mismatch
                text_columns = [
                    'core_sector_top', 'core_sector_sub', 'core_desc',
                    '해자DESC', '검증용desc',
                    # v2 new columns
                    'evidence_summary', 'bm_summary', 'sustainability_notes',
                    'ai_review',
                ]
                for col in text_columns:
                    if col not in df.columns:
                        df[col] = None  # Add missing columns
                    df[col] = df[col].astype('object')

                # Ensure numeric columns are numeric
                numeric_columns = ['해자강도', 'evidence_count', 'evidence_quality', 'bm_completeness']
                for col in numeric_columns:
                    if col not in df.columns:
                        df[col] = None
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # 4. Update all rows in memory
                for update in updates:
                    ticker = update['ticker']
                    data = update['data']

                    row_idx = df[df['ticker'] == ticker].index
                    if len(row_idx) == 0:
                        print(f"⚠️  Ticker {ticker} not found, skipping")
                        results['failed'] += 1
                        continue

                    row_idx = row_idx[0]
                    for field, value in data.items():
                        if field in df.columns:
                            # Type conversion before assignment
                            if field in ('해자강도', 'evidence_count', 'evidence_quality', 'bm_completeness'):
                                # Numeric fields
                                try:
                                    if pd.notna(value) if not isinstance(value, (int, float)) else True:
                                        df.at[row_idx, field] = float(value) if isinstance(value, (int, float)) else None
                                    else:
                                        df.at[row_idx, field] = None
                                except (ValueError, TypeError):
                                    df.at[row_idx, field] = None
                            else:
                                # Text fields
                                df.at[row_idx, field] = str(value) if value is not None else None

                    results['success'] += 1

                # 5. Write back once
                with pd.ExcelWriter(
                    self.file_path,
                    engine='openpyxl',
                    mode='a',
                    if_sheet_exists='overlay'
                ) as writer:
                    df.to_excel(writer, sheet_name='stock_core_master', index=False)

                print(f"✅ Batch updated {results['success']} stocks")

                # 6. Remove backup
                if os.path.exists(self.backup_path):
                    os.remove(self.backup_path)

            except Exception as e:
                print(f"❌ Batch update failed: {e}")
                # Restore from backup
                if os.path.exists(self.backup_path):
                    shutil.copy2(self.backup_path, self.file_path)
                    print(f"🔄 Restored from backup")
                results['failed'] = len(updates)

        return results


# Test function
if __name__ == "__main__":
    # Test with actual file path
    file_path = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02/data/ask/stock_core_master_v2_korean_taxonomy_2026-01-30_요청용_011.xlsx"

    excel_io = ExcelIO(file_path)

    # Test: Load data
    df = excel_io.load_stock_data()
    print(f"\n📊 Total stocks: {len(df)}")

    # Test: Get incomplete stocks
    incomplete = excel_io.get_incomplete_stocks(df)
    print(f"📊 Incomplete stocks: {len(incomplete)}")

    # Test: Load sector taxonomy
    sectors = excel_io.load_sector_taxonomy()
    print(f"\n📂 Sector categories: {len(sectors)}")
    print(f"Sample sectors: {sectors[:10]}")
