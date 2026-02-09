"""
Evidence-Based Moat Analysis Pipeline v2
Full pipeline: DART data → BM decomposition → Evidence extraction →
               Moat evaluation → Sustainability check → AI verification

Usage:
    python scripts/stock_moat/analyze_with_evidence.py --ticker 005930 --name 삼성전자
    python scripts/stock_moat/analyze_with_evidence.py --batch data/ask/stock_list.xlsx
"""

import sys
import os
import argparse
import time
from typing import Dict, List, Optional

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add paths
project_root = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{project_root}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{project_root}/scripts/stock_moat")

from config import get_dart_api_key
from dart_client import DARTClient
from ksic_to_gics_mapper import KSICtoGICSMapper
from dart_report_parser import DARTReportParser
from bm_analyzer import BMAnalyzer
from evidence_extractor import EvidenceExtractor
from moat_evaluator_v2 import MoatEvaluatorV2
from sustainability_checker import SustainabilityChecker
from ai_verifier import AIVerifier


class EvidenceBasedMoatPipeline:
    """Full evidence-based moat analysis pipeline"""

    def __init__(self, dart_api_key: str = None, openai_api_key: str = None):
        if dart_api_key is None:
            dart_api_key = get_dart_api_key()

        self.dart = DARTClient(dart_api_key)
        self.gics_mapper = KSICtoGICSMapper()
        self.report_parser = DARTReportParser()
        self.bm_analyzer = BMAnalyzer()
        self.evidence_extractor = EvidenceExtractor()
        self.moat_evaluator = MoatEvaluatorV2()
        self.sustainability_checker = SustainabilityChecker()
        self.ai_verifier = AIVerifier(openai_api_key)

    def analyze_stock(self, ticker: str, name: str, year: str = "2023") -> Dict:
        """
        Full evidence-based analysis for a single stock.

        Pipeline:
        1. DART: corp_code → company info → KSIC → GICS mapping
        2. DART: Financial statements (DS003)
        3. DART: Business report download + parse (DS001)
        4. BM: 6-element decomposition (Step C)
        5. Evidence: Pattern-based extraction (Step B→D)
        6. Moat: Evidence-based scoring (Step D)
        7. Sustainability: 3-check verification (Step E)
        8. AI: GPT-4o professional investor review

        Returns comprehensive analysis result dict.
        """
        print(f"\n{'='*70}")
        print(f"  Evidence-Based Moat Analysis v2: {name} ({ticker})")
        print(f"{'='*70}")

        result = {
            'ticker': ticker,
            'name': name,
            'status': 'success',
            'error': None
        }

        # ── Step 1: DART Company Info + GICS Classification ───
        print(f"\n[1/8] DART 기업정보 조회...")
        dart_result = self.dart.analyze_stock(ticker)
        if not dart_result:
            result['status'] = 'failed'
            result['error'] = 'DART 기업정보 조회 실패'
            result['해자강도'] = 1
            result['core_desc'] = f'{name} - DART 데이터 없음'
            return result

        corp_code = dart_result['corp_code']
        industry_code = dart_result['industry_code']

        # GICS mapping
        gics_result = self.gics_mapper.map_to_gics(industry_code, name)
        classification = {
            'gics_sector': gics_result['gics_sector'],
            'gics_industry_group': gics_result['gics_industry_group'],
            'gics_industry': gics_result['gics_industry'],
            'korean_sector_top': gics_result['korean_sector_top'],
            'korean_sector_sub': gics_result['korean_sector_sub'],
            'confidence': gics_result['confidence'],
            'source': gics_result['source']
        }

        print(f"    Sector: {classification['korean_sector_top']} / {classification['korean_sector_sub']}")
        print(f"    GICS: {classification['gics_sector']} - {classification['gics_industry']}")

        result['core_sector_top'] = classification['korean_sector_top']
        result['core_sector_sub'] = classification['korean_sector_sub']
        result['classification'] = classification

        # ── Step 2: Financial Statements (DS003) ──────────────
        print(f"\n[2/8] 재무제표 조회...")
        financials = self.dart.get_financial_statements(corp_code, year) or {}
        multi_year = self.dart.get_multi_year_financials(corp_code)

        if financials:
            rev = financials.get('revenue', 0)
            op = financials.get('operating_margin')
            print(f"    Revenue: {rev:,}")
            if op is not None:
                print(f"    Operating Margin: {op:.1%}")
        else:
            print(f"    ⚠️  Financial data not available")

        # ── Step 3: Business Report Download + Parse ──────────
        print(f"\n[3/8] 사업보고서 다운로드...")
        report_text = self.dart.download_business_report(corp_code, year)
        report_sections = {}
        parse_quality = {}

        if report_text:
            report_sections = self.report_parser.parse_report(report_text)
            parse_quality = self.report_parser.get_parse_quality(report_sections)
            print(f"    Sections: {parse_quality['total_sections_found']}/{parse_quality['total_sections_possible']}")
            print(f"    Text: {parse_quality['total_text_length']:,} chars")
        else:
            print(f"    ⚠️  Business report not available")

        # ── Step 4: BM Decomposition (Step C) ─────────────────
        print(f"\n[4/8] BM 6요소 분해...")
        segments = self.dart.get_segment_revenue(corp_code, year)
        bm = self.bm_analyzer.analyze(
            name, ticker, report_sections, financials, segments,
            classification.get('gics_sector', ''),
            classification.get('gics_industry', '')
        )
        bm_summary = self.bm_analyzer.generate_bm_summary(bm)
        print(f"    Completeness: {bm.completeness:.0%}")

        # ── Step 5: Evidence Extraction (Step B→D) ────────────
        print(f"\n[5/8] 해자 증거 추출...")
        evidence = self.evidence_extractor.extract_evidences(
            name, ticker, report_sections, financials
        )
        print(f"    Evidence: {len(evidence.evidences)} items")
        print(f"    Total Quality: {evidence.total_quality:.1f}")
        print(f"    Coverage: {evidence.coverage}")

        evidence_summary = self._format_evidence_summary(evidence)

        # ── Step 6: Moat Evaluation (Step D) ──────────────────
        print(f"\n[6/8] 해자 평가 v2...")
        evaluation = self.moat_evaluator.evaluate(
            name, ticker, evidence, bm, classification
        )
        print(f"    Moat Strength: {evaluation.moat_strength}/5")
        print(f"    Total Score: {evaluation.total_score}/50")
        print(f"    Evidence Based: {evaluation.evidence_based}")

        # ── Step 7: Sustainability Check (Step E) ─────────────
        print(f"\n[7/8] 지속가능성 검증...")
        sustainability = self.sustainability_checker.check(
            name, financials, multi_year, report_sections,
            evaluation.moat_strength
        )
        sustainability_notes = self.sustainability_checker.generate_sustainability_notes(sustainability)
        print(f"    Adjusted Strength: {sustainability['adjusted_strength']}")
        if sustainability['warnings']:
            for w in sustainability['warnings']:
                print(f"    ⚠️  {w}")

        # Apply sustainability adjustment
        final_strength = sustainability['adjusted_strength']

        # ── Re-generate verification_desc with sustainability (4점+) ──
        if final_strength >= 4:
            evaluation.verification_desc = self.moat_evaluator._generate_verification_desc(
                name, final_strength, evaluation.scores, bm,
                evidence_collection=evidence, sustainability=sustainability
            )
            print(f"    검증용desc 생성 완료 ({len(evaluation.verification_desc)}자)")
        elif evaluation.moat_strength >= 4 and final_strength < 4:
            # Was 4+ but sustainability downgraded below 4
            evaluation.verification_desc = (
                f"[참고] 원래 해자강도 {evaluation.moat_strength} → "
                f"지속가능성 검증 후 {final_strength}로 하향\n"
                f"사유: {', '.join(sustainability.get('warnings', ['N/A']))}"
            )

        # ── Step 8: AI Verification (GPT-4o) ──────────────────
        print(f"\n[8/8] AI 검증 (GPT-4o)...")
        ai_result = self.ai_verifier.verify(
            name, ticker, final_strength,
            evaluation.moat_desc, bm_summary, evidence_summary,
            sustainability_notes, classification, financials
        )

        if ai_result.get('verified'):
            ai_adjusted = ai_result.get('adjusted_strength')
            if ai_adjusted is not None and ai_adjusted != final_strength:
                print(f"    AI 조정: {final_strength} → {ai_adjusted}")
                print(f"    사유: {ai_result.get('adjustment_reason', '')}")
                final_strength = ai_adjusted
            print(f"    AI 의견: {ai_result.get('ai_opinion', '')[:100]}")
        else:
            print(f"    ⚠️  AI 검증 스킵: {ai_result.get('error', 'unknown')}")

        ai_review = self.ai_verifier.generate_ai_review_text(ai_result)

        # ── Build core_desc ───────────────────────────────────
        core_desc_parts = [f"{name}"]
        core_desc_parts.append(f"GICS: {classification['gics_sector']} - {classification['gics_industry']}")
        if dart_result.get('homepage'):
            core_desc_parts.append(dart_result['homepage'])
        if financials.get('revenue', 0) > 0:
            core_desc_parts.append(f"매출 {financials['revenue']/1_000_000_000_000:.1f}조원")
        core_desc = ' | '.join(core_desc_parts)

        # ── Compile Final Result ──────────────────────────────
        result.update({
            # Core fields (backward compatible)
            'core_sector_top': classification['korean_sector_top'],
            'core_sector_sub': classification['korean_sector_sub'],
            'core_desc': core_desc,
            '해자강도': final_strength,
            '해자DESC': evaluation.moat_desc,
            '검증용desc': evaluation.verification_desc or '',
            'confidence': classification['confidence'],

            # New v2 fields
            'evidence_summary': evidence_summary,
            'bm_summary': bm_summary,
            'sustainability_notes': sustainability_notes,
            'ai_review': ai_review,

            # Metadata
            'evidence_count': len(evidence.evidences),
            'evidence_quality': evidence.total_quality,
            'bm_completeness': bm.completeness,
            'parse_quality': parse_quality,
            'classification': classification,
        })

        # ── Print Summary ─────────────────────────────────────
        print(f"\n{'='*70}")
        print(f"  RESULT: {name} ({ticker})")
        print(f"{'='*70}")
        print(f"  Sector:    {classification['korean_sector_top']} / {classification['korean_sector_sub']}")
        print(f"  해자강도:  {final_strength}/5")
        print(f"  증거:      {len(evidence.evidences)}건 (quality {evidence.total_quality:.1f})")
        print(f"  BM 완성도: {bm.completeness:.0%}")
        print(f"{'='*70}")

        return result

    def analyze_batch(
        self,
        excel_path: str,
        year: str = "2023",
        limit: int = 0,
        force: bool = False,
        start_from: int = 0
    ) -> List[Dict]:
        """
        Batch analysis: load stocks from Excel, analyze each, save results back.

        Args:
            excel_path: Path to stock_core_master Excel file
            year: Report year for DART data
            limit: Max stocks to process (0 = all)
            force: If True, re-analyze ALL stocks (not just incomplete)
            start_from: Skip first N stocks (for resuming)

        Returns:
            List of analysis results
        """
        from excel_io import ExcelIO

        excel = ExcelIO(excel_path)
        df = excel.load_stock_data()

        if force:
            # Re-analyze all stocks
            target = df.copy()
            print(f"📊 Force mode: processing ALL {len(target)} stocks")
        else:
            target = excel.get_incomplete_stocks(df)

        if start_from > 0:
            target = target.iloc[start_from:]
            print(f"📊 Resuming from index {start_from}")

        if limit > 0:
            target = target.head(limit)

        print(f"\n{'='*70}")
        print(f"  Batch Analysis: {len(target)} stocks")
        print(f"{'='*70}")

        results = []
        updates = []

        for idx, row in target.iterrows():
            ticker = str(row.get('ticker', '')).strip()
            name = str(row.get('name', '')).strip()

            if not ticker or not name:
                continue

            try:
                result = self.analyze_stock(ticker, name, year)
                results.append(result)

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
                updates.append({'ticker': ticker, 'data': update_data})

            except Exception as e:
                print(f"\n❌ Error analyzing {name} ({ticker}): {e}")
                results.append({
                    'ticker': ticker,
                    'name': name,
                    'status': 'failed',
                    'error': str(e)
                })

            # Rate limiting between stocks
            time.sleep(1)

        # Save all results to Excel
        if updates:
            print(f"\n📝 Saving {len(updates)} results to Excel...")
            batch_result = excel.batch_update_stocks(updates, mode='efficient')
            print(f"    Success: {batch_result['success']}, Failed: {batch_result['failed']}")

        # Summary
        success = sum(1 for r in results if r.get('status') == 'success')
        failed = len(results) - success
        print(f"\n{'='*70}")
        print(f"  Batch Complete: {success} success, {failed} failed")
        print(f"{'='*70}")

        return results

    def _format_evidence_summary(self, evidence) -> str:
        """Format evidence collection into summary text"""
        if not evidence.evidences:
            return "증거 없음"

        lines = [f"총 {len(evidence.evidences)}건, quality {evidence.total_quality:.1f}"]
        for moat_type, count in sorted(evidence.coverage.items(), key=lambda x: -x[1]):
            quality = evidence.quality_by_type(moat_type)
            lines.append(f"  {moat_type}: {count}건 (q={quality:.1f})")

        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Evidence-Based Moat Analysis v2')
    parser.add_argument('--ticker', type=str, help='Stock ticker (e.g., 005930)')
    parser.add_argument('--name', type=str, help='Company name (e.g., 삼성전자)')
    parser.add_argument('--year', type=str, default='2023', help='Report year')
    parser.add_argument('--batch', type=str, help='Batch analysis from Excel file')
    parser.add_argument('--force', action='store_true', help='Re-analyze all stocks (not just incomplete)')
    parser.add_argument('--limit', type=int, default=0, help='Max stocks to process (0=all)')
    parser.add_argument('--start-from', type=int, default=0, help='Skip first N stocks (for resuming)')

    args = parser.parse_args()

    pipeline = EvidenceBasedMoatPipeline()

    if args.ticker and args.name:
        result = pipeline.analyze_stock(args.ticker, args.name, args.year)
        return result
    elif args.batch:
        print(f"Batch mode: {args.batch}")
        print(f"  Force={args.force}, Limit={args.limit}, StartFrom={args.start_from}")
        results = pipeline.analyze_batch(
            args.batch, args.year,
            limit=args.limit, force=args.force, start_from=args.start_from
        )
        return results
    else:
        # Demo mode
        print("Evidence-Based Moat Analysis v2 - Demo")
        print("Usage: python analyze_with_evidence.py --ticker 005930 --name 삼성전자")
        print("       python analyze_with_evidence.py --batch data/ask/stock_list.xlsx --force --limit 10")


if __name__ == "__main__":
    main()
