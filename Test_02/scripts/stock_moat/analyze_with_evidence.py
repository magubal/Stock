"""
Evidence-Based Moat Analysis Pipeline v3
Full pipeline: DART data → Oracle TTM → BM decomposition → Evidence extraction →
               Moat evaluation → Growth scoring → Sustainability → AI verification

v3 changes:
- Oracle DB TTM 실적 연동 (Fallback 3계층)
- 성장 추세 기반 해자강도 ±1 가감
- op_multiple (시총/영업이익배수) 산출
- DataQuality/AsOfDate 시점 정합성

Usage:
    python scripts/stock_moat/analyze_with_evidence.py --ticker 005930 --name 삼성전자
    python scripts/stock_moat/analyze_with_evidence.py --batch data/ask/stock_list.xlsx
"""

import sys
import os
import argparse
import time
import json
import urllib.request
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add paths
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / ".agent/skills/stock-moat/utils"))
sys.path.insert(0, str(project_root / "scripts/stock_moat"))

from config import get_dart_api_key, get_oracle_config, get_growth_thresholds_path
from dart_client import DARTClient
from ksic_to_gics_mapper import KSICtoGICSMapper
from dart_report_parser import DARTReportParser
from bm_analyzer import BMAnalyzer
from evidence_extractor import EvidenceExtractor
from moat_evaluator_v2 import MoatEvaluatorV2
from sustainability_checker import SustainabilityChecker
from ai_verifier import AIVerifier
from data_quality import AsOfDate, DataQuality, TTMFinancials, GrowthTrend, format_krw
from oracle_client import OracleFinancialsClient
from financials_resolver import FinancialsResolver
from growth_scorer import GrowthScorer
from investment_value_scorer import InvestmentValueScorer
from forecast_repository import ForecastRepository
from industry_outlook_service import IndustryOutlookService
from fnguide_consensus_client import FnGuideConsensusClient


class EvidenceBasedMoatPipeline:
    """Full evidence-based moat analysis pipeline"""

    def __init__(self, dart_api_key: str = None, anthropic_api_key: str = None):
        if dart_api_key is None:
            dart_api_key = get_dart_api_key()

        self.dart = DARTClient(dart_api_key)
        self.gics_mapper = KSICtoGICSMapper()
        self.report_parser = DARTReportParser()
        self.bm_analyzer = BMAnalyzer()
        self.evidence_extractor = EvidenceExtractor()
        self.moat_evaluator = MoatEvaluatorV2()
        self.sustainability_checker = SustainabilityChecker()
        effective_anthropic_key = anthropic_api_key if anthropic_api_key is not None else os.getenv("ANTHROPIC_API_KEY")
        self.ai_verifier = AIVerifier(effective_anthropic_key, load_from_env=False)

        # v3: Oracle + Growth Scorer + Resolver
        oracle_cfg = get_oracle_config()
        self.oracle_client = OracleFinancialsClient(
            dsn=oracle_cfg.get('dsn'),
            user=oracle_cfg.get('user'),
            password=oracle_cfg.get('password'),
        )
        self._oracle_connected = self.oracle_client.connect()
        self.financials_resolver = FinancialsResolver(
            oracle_client=self.oracle_client if self._oracle_connected else None,
            dart_client=self.dart,
        )
        self.growth_scorer = GrowthScorer(get_growth_thresholds_path())
        self.investment_scorer = InvestmentValueScorer()
        self.forecast_repo = None
        self.industry_outlook_service = None
        self.consensus_client = None
        if self._oracle_connected:
            try:
                self.forecast_repo = ForecastRepository(self.oracle_client)
                self.forecast_repo.ensure_tables()
                self.industry_outlook_service = IndustryOutlookService(self.forecast_repo, ttl_days=30)
                self.consensus_client = FnGuideConsensusClient()
            except Exception as e:
                print(f"    [WARN] Forecast repository init failed: {e}")
                self.forecast_repo = None
                self.industry_outlook_service = None
                self.consensus_client = None

    def analyze_stock(self, ticker: str, name: str, year: str = "auto") -> Dict:
        """
        Full evidence-based analysis for a single stock (v3).

        Pipeline:
        1. DART: corp_code → company info → KSIC → GICS mapping
        2. Financials: Oracle TTM → DART fallback (3계층)
        3. DART: Business report download + parse (DS001)
        4. BM: 6-element decomposition (Step C)
        5. Evidence: Pattern-based extraction (Step B→D)
        6. Moat: Evidence-based scoring (Step D)
        6.5. Growth: 성장 추세 평가 + 해자 ±1 가감
        7. Sustainability: 3-check verification (Step E)
        8. AI: Claude Opus 4.6 independent moat evaluation
        9. Valuation: op_multiple 산출 + as_of_date

        Returns comprehensive analysis result dict.
        """
        print(f"\n{'='*70}")
        print(f"  Evidence-Based Moat Analysis v3: {name} ({ticker})")
        print(f"{'='*70}")

        result = {
            'ticker': ticker,
            'name': name,
            'status': 'success',
            'error': None
        }
        analysis_as_of_date = date.today().isoformat()
        financial_year = year
        if year == "auto":
            financial_year = str(max(2000, int(analysis_as_of_date[:4]) - 1))

        # ── Step 1: DART Company Info + GICS Classification ───
        print(f"\n[1/9] DART 기업정보 조회...")
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

        industry_outlook = self._resolve_industry_outlook(classification, analysis_as_of_date)
        forecast_year = analysis_as_of_date[:4]
        consensus_2026 = self._resolve_consensus(ticker, forecast_year, analysis_as_of_date)
        forecast_scenarios = self._build_forecast_scenarios(
            ticker=ticker,
            fiscal_year=forecast_year,
            consensus=consensus_2026,
            as_of_date=analysis_as_of_date,
        )

        # ── Step 2: Financial Statements (Oracle TTM → DART fallback) ──
        print(f"\n[2/9] 재무제표 조회 (Oracle → DART fallback)...")
        ttm_result = self.financials_resolver.resolve_ttm(
            ticker, corp_code, as_of_date=analysis_as_of_date
        )
        trend_periods = self.financials_resolver.resolve_trend(
            ticker, corp_code, years=3, as_of_date=analysis_as_of_date
        )

        # 기존 DART financials도 유지 (하위 호환: BM/Evidence에서 사용)
        financials = self.dart.get_financial_statements(corp_code, financial_year) or {}
        multi_year = self.dart.get_multi_year_financials(corp_code)

        # TTM 결과를 financials에 병합
        if ttm_result:
            financials['ttm_revenue'] = ttm_result.ttm_revenue
            financials['ttm_op_income'] = ttm_result.ttm_op_income
            financials['ttm_quarter'] = ttm_result.ttm_quarter
            print(f"    TTM Revenue: {format_krw(ttm_result.ttm_revenue)}")
            print(f"    TTM Op Income: {format_krw(ttm_result.ttm_op_income)}")
            print(f"    TTM Op Margin: {ttm_result.ttm_op_margin:.1%}")
        elif financials:
            rev = financials.get('revenue', 0)
            op = financials.get('operating_margin')
            print(f"    Revenue: {rev:,}")
            if op is not None:
                print(f"    Operating Margin: {op:.1%}")

        # ── Step 3: Business Report Download + Parse ──────────
        print(f"\n[3/9] 사업보고서 다운로드 (Target: {year})...")
        
        report_text = None
        target_year = year

        if year == "auto":
            print("    🔍 최신 보고서(사업/반기) 검색 중...")
            latest_report = self.dart.find_latest_report(corp_code)
            if latest_report:
                rcept_no = latest_report.get('rcept_no')
                report_nm = latest_report.get('report_nm')
                print(f"    ✅ Latest report found: {report_nm}")
                
                # Download by rcept_no
                report_text = self.dart.download_report(corp_code, rcept_no)
                target_year = report_nm or "Latest"
            else:
                print(f"    ⚠️  Latest report not found, defaulting to 2024 Annual")
                target_year = "2024"
                report_text = self.dart.download_business_report(corp_code, target_year)
        else:
            # Specific year requested (Annual only)
            report_text = self.dart.download_business_report(corp_code, year)
        
        # Fallback safety
        if not report_text and target_year == "2024":
             print(f"    ⚠️  2024년 보고서 없음. 2023년 시도...")
             target_year = "2023"
             report_text = self.dart.download_business_report(corp_code, target_year)

        report_sections = {}
        parse_quality = {}

        if report_text:
            report_sections = self.report_parser.parse_report(report_text)
            parse_quality = self.report_parser.get_parse_quality(report_sections)
            print(f"    Sections: {parse_quality['total_sections_found']}/{parse_quality['total_sections_possible']}")
            print(f"    Text: {parse_quality['total_text_length']:,} chars")
        else:
            print(f"    ⚠️  Business report not available ({target_year})")

        # ── Step 4: BM Decomposition (Step C) ─────────────────
        print(f"\n[4/9] BM 6요소 분해...")
        segments = self.dart.get_segment_revenue(corp_code, financial_year)
        bm = self.bm_analyzer.analyze(
            name, ticker, report_sections, financials, segments,
            classification.get('gics_sector', ''),
            classification.get('gics_industry', '')
        )
        bm_summary = self.bm_analyzer.generate_bm_summary(bm)
        print(f"    Completeness: {bm.completeness:.0%}")

        # ── Step 5: Evidence Extraction (Step B→D) ────────────
        print(f"\n[5/9] 증거 추출...")
        evidence = self.evidence_extractor.extract_evidences(
            name, ticker, report_sections, financials
        )
        print(f"    Evidence: {len(evidence.evidences)} items")
        print(f"    Total Quality: {evidence.total_quality:.1f}")
        print(f"    Coverage: {evidence.coverage}")
        
        # DEBUG: Print top evidences to understand false positives
        print("\n    [Detailed Evidence Check]")
        sorted_ev = sorted(evidence.evidences, key=lambda x: x.quality_score, reverse=True)
        for i, ev in enumerate(sorted_ev[:5]):
            msg = ev.evidence_text[:100] if ev.evidence_text else "(No text)"
            print(f"    {i+1}. [{ev.moat_type}] (Score: {ev.quality_score}) {msg}...")

        evidence_summary = self._format_evidence_summary(evidence)

        # ── Step 6: Moat Evaluation (Step D) ──────────────────
        print(f"\n[6/9] 해자 평가 v2...")
        evaluation = self.moat_evaluator.evaluate(
            name, ticker, evidence, bm, classification, 
            financials=financials, multi_year_financials=multi_year
        )
        print(f"    Moat Strength: {evaluation.moat_strength}/5")
        print(f"    Total Score: {evaluation.total_score}/50")
        print(f"    Evidence Based: {evaluation.evidence_based}")

        # ── Step 6.5: Growth Scoring ─────────────────────────
        growth_adjustment = 0
        growth_reason = "데이터 없음"
        growth_trend = None

        if trend_periods and len(trend_periods) >= 2:
            print(f"\n[6.5/9] 성장 추세 평가...")
            growth_trend = self.growth_scorer.build_trend(trend_periods)
            growth_adjustment, growth_reason = self.growth_scorer.score(
                growth_trend,
                gics_sector=classification.get('gics_sector', ''),
                ttm_revenue=ttm_result.ttm_revenue if ttm_result else 0,
            )
            growth_trend.growth_score = growth_adjustment
            growth_trend.score_reason = growth_reason

            print(f"    CAGR: {growth_trend.revenue_cagr:.1%}")
            print(f"    Margin Δ: {growth_trend.op_margin_delta:+.1f}%p")
            print(f"    Score: {growth_adjustment:+d} ({growth_reason})")
        else:
            print(f"\n[6.5/9] 성장 추세 평가 SKIP (데이터 부족)")

        # Apply growth adjustment to moat strength before sustainability
        pre_growth_strength = evaluation.moat_strength
        adjusted_by_growth = max(1, min(5, evaluation.moat_strength + growth_adjustment))
        if growth_adjustment != 0:
            print(f"    해자강도: {pre_growth_strength} → {adjusted_by_growth} (성장 {growth_adjustment:+d})")

        # ── Step 7: Sustainability Check (Step E) ─────────────
        print(f"\n[7/9] 지속가능성 검증...")
        sustainability = self.sustainability_checker.check(
            name, financials, multi_year, report_sections,
            adjusted_by_growth
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

        # ── Step 8: AI Independent Evaluation (Claude Opus 4.6 Thinking) ──
        # Cost Optimization: Only verify high-potential stocks (Rule-Based Score >= 4)
        if final_strength >= 4:
            print(f"\n[8/9] AI 독립평가 (Claude Opus 4.6 Thinking)...")
            ai_result = self.ai_verifier.verify(
                company_name=name,
                ticker=ticker,
                classification=classification,
                report_sections=report_sections,
                financials=financials,
                multi_year_financials=multi_year,
                bm_analysis=bm,
                evidence_items=evidence.evidences if evidence else None,
                # Rule-Based score: passed for gap comparison ONLY (not shown to AI)
                moat_strength=final_strength,
            )

            if ai_result.get('verified'):
                ai_ind = ai_result.get('independent_strength')
                if ai_ind is not None:
                    print(f"    AI 독립점수: {ai_ind}/5")
                    if ai_result.get('gap_flag'):
                        print(f"    ⚠️ 괴리감지: Rule-Based({final_strength}) vs AI({ai_ind})")
                    # Use AI score as final (independent evaluation takes priority)
                    final_strength = ai_ind
                print(f"    AI 의견: {ai_result.get('ai_opinion', '')[:100]}")
            else:
                print(f"    ⚠️  AI 평가 스킵: {ai_result.get('error', 'unknown')}")
        else:
            print(f"\n[8/9] AI 독립평가 생략 (Rule-Based {final_strength}점 < 4점)")
            ai_result = {
                'verified': False, 
                'error': 'Skipped (Moat < 4)',
                'ai_opinion': 'Rule-Based 해자강도가 낮아(4점 미만) AI 정밀평가를 생략했습니다.'
            }

        ai_review = self.ai_verifier.generate_ai_review_text(ai_result)

        # ── Step 9: Valuation (op_multiple + as_of_date) ─────
        print(f"\n[9/9] 밸류에이션 산출...")
        op_multiple = None
        market_cap = None
        current_price = None
        shares_outstanding = None
        price_date = analysis_as_of_date
        as_of_date = None

        try:
            # Yahoo Finance v8 API for price
            yahoo_ticker = f"{ticker}.KS"
            yahoo_url = f"https://query2.finance.yahoo.com/v8/finance/chart/{yahoo_ticker}?range=1d&interval=1d"
            req = urllib.request.Request(yahoo_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                yahoo_data = json.loads(resp.read().decode('utf-8'))

            meta = yahoo_data['chart']['result'][0]['meta']
            current_price = meta.get('regularMarketPrice', 0)
            price_date = analysis_as_of_date

            # Shares outstanding: Yahoo meta → DART stockTotqySttus
            shares_outstanding = meta.get('sharesOutstanding', 0)
            if not shares_outstanding:
                shares_outstanding = self.dart.get_shares_outstanding(corp_code)

            # Calculate market cap
            if current_price and shares_outstanding:
                market_cap = int(current_price * shares_outstanding)

            if current_price:
                print(f"    현재가: {current_price:,.0f}원")
            if market_cap:
                print(f"    시가총액: {format_krw(market_cap)}")

                # op_multiple = 시총 / TTM 영업이익
                if ttm_result and ttm_result.ttm_op_income > 0:
                    op_multiple = market_cap / ttm_result.ttm_op_income
                    print(f"    op_multiple: {op_multiple:.1f}x (시총/TTM영업이익)")
                elif ttm_result and ttm_result.ttm_op_income <= 0:
                    print(f"    op_multiple: N/A (영업적자)")
                else:
                    print(f"    op_multiple: N/A (TTM 데이터 없음)")
            else:
                print(f"    ⚠️ 시가총액 조회 실패")

        except Exception as e:
            print(f"    ⚠️ Yahoo 조회 실패: {e}")

        # as_of_date 구성
        as_of_date = AsOfDate(
            price_date=price_date,
            ttm_quarter=ttm_result.ttm_quarter if ttm_result else "",
            report_base=target_year if target_year != "auto" else "",
        )
        if as_of_date.gap_warning:
            print(f"    ⚠️ 시점 괴리: {as_of_date.gap_days}일 (가격 vs TTM)")

        freshness_days = max(as_of_date.gap_days, 0) if as_of_date else 0
        data_warnings = []
        if as_of_date and as_of_date.gap_warning:
            data_warnings.append(f"ttm_gap_days={as_of_date.gap_days}")

        # DataQuality 집계
        data_quality = DataQuality(
            source=ttm_result.data_quality.source if ttm_result and ttm_result.data_quality else "dart_annual",
            freshness_days=freshness_days,
            confidence=ttm_result.data_quality.confidence if ttm_result and ttm_result.data_quality else "low",
            metric_name="op_multiple",
            ttm_quarter=ttm_result.ttm_quarter if ttm_result else "",
            price_date=price_date,
            as_of_date=as_of_date,
            warnings=data_warnings,
        )

        investment_comment = self._compose_investment_comment(
            final_strength=final_strength,
            op_multiple=op_multiple,
            consensus=consensus_2026,
            scenarios=forecast_scenarios,
            industry_outlook=industry_outlook,
            growth_reason=growth_reason,
        )

        # ── Step 9.5: Investment Value Score (0-5) ─────────────
        iv_cagr = growth_trend.revenue_cagr if growth_trend else None
        iv_margin_delta = growth_trend.op_margin_delta if growth_trend else None
        iv_gap_days = as_of_date.gap_days if as_of_date else 0
        investment_value, iv_reason = self.investment_scorer.score(
            moat_strength=final_strength,
            ttm_op_margin=ttm_result.ttm_op_margin if ttm_result else 0.0,
            ttm_op_income=ttm_result.ttm_op_income if ttm_result else 0,
            op_multiple=op_multiple,
            revenue_cagr=iv_cagr,
            margin_delta=iv_margin_delta,
            bm_completeness=bm.completeness if bm else 0.0,
            data_gap_days=iv_gap_days,
        )
        print(f"\n[9.5] 투자가치 채점: {investment_value}/5")
        print(f"    {iv_reason}")

        # ── Build core_desc ───────────────────────────────────
        core_desc_parts = [f"{name}"]
        core_desc_parts.append(f"GICS: {classification['gics_sector']} - {classification['gics_industry']}")
        if dart_result.get('homepage'):
            core_desc_parts.append(dart_result['homepage'])
        if ttm_result and ttm_result.ttm_revenue > 0:
            core_desc_parts.append(f"TTM매출 {format_krw(ttm_result.ttm_revenue)}")
        elif financials.get('revenue', 0) > 0:
            core_desc_parts.append(f"매출 {financials['revenue']/1_000_000_000_000:.1f}조원")
        if op_multiple is not None:
            core_desc_parts.append(f"op_multiple {op_multiple:.1f}x")
        core_desc = ' | '.join(core_desc_parts)

        # ── Compile Final Result ──────────────────────────────
        # Combined description (Rule-Based breakdown + AI Review)
        combined_moat_desc = evaluation.moat_desc
        if ai_review:
            combined_moat_desc += "\n\n" + "="*40 + "\n"
            combined_moat_desc += ai_review
        if investment_comment:
            combined_moat_desc += "\n\n" + "="*40 + "\n"
            combined_moat_desc += f"[Investment Comment]\n{investment_comment}"

        result.update({
            # Core fields (backward compatible)
            'core_sector_top': classification['korean_sector_top'],
            'core_sector_sub': classification['korean_sector_sub'],
            'core_desc': core_desc,
            '해자강도': final_strength,
            '해자DESC': combined_moat_desc,
            '검증용desc': evaluation.verification_desc or '',
            'confidence': classification['confidence'],

            # v2 fields
            'evidence_summary': evidence_summary,
            'bm_summary': bm_summary,
            'sustainability_notes': sustainability_notes,
            'ai_review': ai_review,

            # v3 fields: TTM + Valuation
            'ttm_revenue': ttm_result.ttm_revenue if ttm_result else 0,
            'ttm_op_income': ttm_result.ttm_op_income if ttm_result else 0,
            'ttm_op_margin': f"{ttm_result.ttm_op_margin:.1%}" if ttm_result else "",
            'ttm_quarter': ttm_result.ttm_quarter if ttm_result else "",
            'current_price': current_price or 0,
            'market_cap': market_cap or 0,
            'op_multiple': round(op_multiple, 1) if op_multiple is not None else None,

            # v3 fields: Growth
            'growth_adjustment': growth_adjustment,
            'growth_reason': growth_reason,
            'revenue_cagr': f"{growth_trend.revenue_cagr:.1%}" if growth_trend else "",
            'op_margin_delta': f"{growth_trend.op_margin_delta:+.1f}%p" if growth_trend else "",

            # v3 fields: Data Quality
            'data_source': data_quality.source,
            'data_confidence': data_quality.confidence,
            'data_freshness_days': data_quality.freshness_days,
            'data_warnings': ' | '.join(data_quality.warnings) if data_quality.warnings else '',
            'price_date': price_date,
            'as_of_date': as_of_date.to_dict() if as_of_date else {},
            'industry_outlook': industry_outlook,
            'consensus_2026': consensus_2026,
            'forecast_scenarios': forecast_scenarios,
            'investment_comment': investment_comment,

            # v3 fields: Investment Value
            'investment_value': investment_value,
            'investment_value_reason': iv_reason,

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
        print(f"  Sector:      {classification['korean_sector_top']} / {classification['korean_sector_sub']}")
        print(f"  해자강도:    {final_strength}/5")
        if growth_adjustment != 0:
            print(f"    (성장 {growth_adjustment:+d}: {growth_reason})")
        print(f"  증거:        {len(evidence.evidences)}건 (quality {evidence.total_quality:.1f})")
        print(f"  BM 완성도:   {bm.completeness:.0%}")
        if ttm_result:
            print(f"  TTM 매출:    {format_krw(ttm_result.ttm_revenue)}")
            print(f"  TTM 영업이익: {format_krw(ttm_result.ttm_op_income)} ({ttm_result.ttm_op_margin:.1%})")
        if op_multiple is not None:
            print(f"  op_multiple: {op_multiple:.1f}x")
        if current_price:
            print(f"  현재가:      {current_price:,.0f}원")
        if market_cap:
            print(f"  시가총액:    {format_krw(market_cap)}")
        print(f"  투자가치:    {investment_value}/5")
        print(f"  데이터출처:  {data_quality.label()}")
        if as_of_date and as_of_date.gap_warning:
            print(f"  ⚠️ 시점괴리:  {as_of_date.gap_days}일")
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
                    # v3 fields
                    'ttm_revenue': result.get('ttm_revenue', 0),
                    'ttm_op_income': result.get('ttm_op_income', 0),
                    'ttm_op_margin': result.get('ttm_op_margin', ''),
                    'ttm_quarter': result.get('ttm_quarter', ''),
                    'current_price': result.get('current_price', 0),
                    'market_cap': result.get('market_cap', 0),
                    'op_multiple': result.get('op_multiple'),
                    'growth_adjustment': result.get('growth_adjustment', 0),
                    'growth_reason': result.get('growth_reason', ''),
                    'revenue_cagr': result.get('revenue_cagr', ''),
                    'op_margin_delta': result.get('op_margin_delta', ''),
                    'data_source': result.get('data_source', ''),
                    'data_confidence': result.get('data_confidence', ''),
                    'data_freshness_days': result.get('data_freshness_days', 0),
                    'data_warnings': result.get('data_warnings', ''),
                    'price_date': result.get('price_date', ''),
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

    def _resolve_industry_outlook(self, classification: Dict, as_of_date: str) -> Dict:
        if not self.industry_outlook_service:
            return {
                "summary": "",
                "key_factors": [],
                "source": "disabled",
                "confidence": "low",
                "as_of_date": as_of_date,
                "valid_until": as_of_date,
                "reused": False,
            }

        try:
            return self.industry_outlook_service.get_or_build(classification, as_of_date)
        except Exception as e:
            return {
                "summary": f"industry_outlook_error: {e}",
                "key_factors": [],
                "source": "error",
                "confidence": "low",
                "as_of_date": as_of_date,
                "valid_until": as_of_date,
                "reused": False,
            }

    def _resolve_consensus(self, ticker: str, fiscal_year: str, as_of_date: str) -> Dict:
        if not self.consensus_client:
            return {
                "ticker": ticker,
                "fiscal_year": fiscal_year,
                "revenue_est": None,
                "op_income_est": None,
                "unit": "억원",
                "source": "disabled",
                "confidence": "low",
                "as_of_date": as_of_date,
                "freshness_days": None,
                "reused": False,
                "raw": {},
            }

        live = None
        try:
            live = self.consensus_client.fetch_consensus(ticker, fiscal_year, as_of_date=as_of_date)
        except Exception:
            live = None

        if live and (live.get("revenue_est") is not None or live.get("op_income_est") is not None):
            if self.forecast_repo:
                try:
                    self.forecast_repo.save_consensus(live)
                except Exception as e:
                    live.setdefault("raw", {})
                    live["raw"]["save_error"] = str(e)
            return live

        if self.forecast_repo:
            try:
                cached = self.forecast_repo.get_latest_consensus(ticker, fiscal_year)
                if cached:
                    return cached
            except Exception:
                pass

        return {
            "ticker": ticker,
            "fiscal_year": fiscal_year,
            "revenue_est": None,
            "op_income_est": None,
            "unit": "억원",
            "source": "fnguide_unavailable",
            "confidence": "low",
            "as_of_date": as_of_date,
            "freshness_days": None,
            "reused": False,
            "raw": {},
        }

    def _build_forecast_scenarios(
        self,
        ticker: str,
        fiscal_year: str,
        consensus: Dict,
        as_of_date: str,
    ) -> List[Dict]:
        revenue = consensus.get("revenue_est") if consensus else None
        op_income = consensus.get("op_income_est") if consensus else None
        if revenue is None and op_income is None:
            return []

        def _scaled(value, factor):
            if value is None:
                return None
            return round(value * factor, 2)

        scenarios = [
            {
                "scenario": "bear",
                "revenue_est": _scaled(revenue, 0.93),
                "op_income_est": _scaled(op_income, 0.85),
                "probability": 25,
            },
            {
                "scenario": "base",
                "revenue_est": _scaled(revenue, 1.0),
                "op_income_est": _scaled(op_income, 1.0),
                "probability": 50,
            },
            {
                "scenario": "bull",
                "revenue_est": _scaled(revenue, 1.08),
                "op_income_est": _scaled(op_income, 1.18),
                "probability": 25,
            },
        ]

        if self.forecast_repo:
            try:
                self.forecast_repo.save_scenarios(
                    ticker=ticker,
                    fiscal_year=fiscal_year,
                    scenarios=scenarios,
                    as_of_date=as_of_date,
                    source=consensus.get("source", "scenario_model"),
                    confidence=consensus.get("confidence", "medium"),
                )
            except Exception:
                pass

        return scenarios

    def _compose_investment_comment(
        self,
        *,
        final_strength: int,
        op_multiple: Optional[float],
        consensus: Dict,
        scenarios: List[Dict],
        industry_outlook: Dict,
        growth_reason: str,
    ) -> str:
        outlook_text = (industry_outlook or {}).get("summary", "")
        unit = (consensus or {}).get("unit", "억원")
        rev = (consensus or {}).get("revenue_est")
        opi = (consensus or {}).get("op_income_est")

        scenario_map = {item.get("scenario"): item for item in (scenarios or [])}
        bear = scenario_map.get("bear", {})
        base = scenario_map.get("base", {})
        bull = scenario_map.get("bull", {})

        valuation_view = "밸류 부담이 낮아 보입니다."
        if op_multiple is None:
            valuation_view = "밸류는 데이터 부족으로 판단 보류입니다."
        elif op_multiple >= 30:
            valuation_view = f"op_multiple {op_multiple:.1f}x로 밸류 부담 구간입니다."
        elif op_multiple >= 20:
            valuation_view = f"op_multiple {op_multiple:.1f}x로 중립 밸류 구간입니다."
        else:
            valuation_view = f"op_multiple {op_multiple:.1f}x로 상대 저평가 구간 가능성이 있습니다."

        moat_view = f"해자강도 {final_strength}/5"
        parts = [moat_view, valuation_view]
        if growth_reason:
            parts.append(f"성장판정: {growth_reason}")
        if rev is not None or opi is not None:
            parts.append(f"2026E 컨센서스 매출 {rev} {unit}, 영업이익 {opi} {unit}")
        if any([bear, base, bull]):
            parts.append(
                "시나리오(B/Base/Bu): "
                f"{bear.get('op_income_est', '-')}/{base.get('op_income_est', '-')}/{bull.get('op_income_est', '-')}"
            )
        if outlook_text:
            parts.append(f"업황요약: {outlook_text}")

        return " | ".join(parts)

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
    parser.add_argument('--year', type=str, default='auto', help='Report year (default: auto)')
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
