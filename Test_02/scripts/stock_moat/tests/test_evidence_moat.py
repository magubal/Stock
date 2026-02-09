"""
Tests for Evidence-Based Moat Analysis v2

Covers:
- KSIC→GICS mapping (critical bug fixes)
- BM 6-element decomposition
- Evidence extraction + quality scoring
- Moat evaluation with fail-safe downgrade
- Sustainability checker
- AI verifier (mock mode)
- Pipeline integration
"""

import sys
import os
import pytest

# Add paths
PROJECT_ROOT = "F:/PSJ/AntigravityWorkPlace/Stock/Test_02"
sys.path.insert(0, f"{PROJECT_ROOT}/.agent/skills/stock-moat/utils")
sys.path.insert(0, f"{PROJECT_ROOT}/scripts/stock_moat")


# ── KSIC → GICS Mapping Tests ──────────────────────────────

class TestKSICtoGICSMapper:
    """Test KSIC to GICS sector mapping including critical bug fixes"""

    @pytest.fixture
    def mapper(self):
        from ksic_to_gics_mapper import KSICtoGICSMapper
        return KSICtoGICSMapper()

    def test_semiconductor_mapping(self, mapper):
        """삼성전자 (26110) → IT sector"""
        result = mapper.map_to_gics('26110', '삼성전자')
        assert result['gics_sector'] == 'Information Technology'
        assert result['confidence'] >= 0.7

    def test_construction_mapping_critical_fix(self, mapper):
        """남광토건 (41xxx) → Industrials, NOT IT (critical bug fix)"""
        result = mapper.map_to_gics('41226', '남광토건')
        assert result['gics_sector'] != 'Information Technology'
        assert result['gics_sector'] == 'Industrials'

    def test_fallback_4_is_industrials(self, mapper):
        """Fallback for '4' prefix should be Industrials, not IT"""
        result = mapper.map_to_gics('49999', '테스트건설')
        assert result['gics_sector'] == 'Industrials'

    def test_finance_mapping(self, mapper):
        """Finance sector (64xxx-66xxx)"""
        result = mapper.map_to_gics('64110', '테스트은행')
        assert result['gics_sector'] == 'Financials'

    def test_utility_mapping(self, mapper):
        """Utilities sector (35xxx)"""
        result = mapper.map_to_gics('35111', '한국전력')
        assert result['gics_sector'] == 'Utilities'

    def test_unknown_code_returns_result(self, mapper):
        """Unknown KSIC code should still return a result, not crash"""
        result = mapper.map_to_gics('99999', '미지의기업')
        assert result is not None
        assert 'gics_sector' in result


# ── BM Analyzer Tests ──────────────────────────────────────

class TestBMAnalyzer:
    """Test BM 6-element decomposition"""

    @pytest.fixture
    def analyzer(self):
        from bm_analyzer import BMAnalyzer
        return BMAnalyzer()

    def test_analyze_with_report_data(self, analyzer):
        """BM analysis with report sections should produce 6 elements"""
        report_sections = {
            'business_overview': '삼성전자는 반도체, 디스플레이, 스마트폰 등을 생산하는 글로벌 전자기업입니다. '
                                 '주요 고객은 애플, 구글 등 글로벌 IT 기업이며 B2B 매출이 70% 이상입니다.',
            'major_products': 'DRAM, NAND Flash, 파운드리, 갤럭시 시리즈 스마트폰',
            'competition': '반도체 분야에서 SK하이닉스, 마이크론과 경쟁합니다.',
            'rnd': '연구개발비 25조원 투자',
        }
        financials = {
            'revenue': 258_000_000_000_000,
            'operating_income': 6_500_000_000_000,
            'operating_margin': 0.025,
        }

        bm = analyzer.analyze(
            '삼성전자', '005930', report_sections, financials, None,
            'Information Technology', 'Semiconductors'
        )

        assert bm is not None
        assert bm.customer is not None
        assert bm.revenue_model is not None
        assert bm.differentiation is not None
        assert bm.cost_structure is not None
        assert bm.growth_condition is not None
        assert bm.failure_condition is not None
        assert 0.0 <= bm.completeness <= 1.0

    def test_analyze_minimal_data(self, analyzer):
        """BM analysis with minimal data should not crash"""
        bm = analyzer.analyze(
            '테스트', '000000', {}, {}, None, '', ''
        )
        assert bm is not None
        assert bm.completeness >= 0.0

    def test_generate_bm_summary(self, analyzer):
        """BM summary should be a non-empty string"""
        bm = analyzer.analyze(
            '테스트', '000000', {}, {'revenue': 1_000_000_000}, None, '', ''
        )
        summary = analyzer.generate_bm_summary(bm)
        assert isinstance(summary, str)
        assert len(summary) > 0


# ── Evidence Extractor Tests ───────────────────────────────

class TestEvidenceExtractor:
    """Test evidence extraction and quality scoring"""

    @pytest.fixture
    def extractor(self):
        from evidence_extractor import EvidenceExtractor
        return EvidenceExtractor()

    def test_extract_from_report(self, extractor):
        """Evidence extraction from report text"""
        report_sections = {
            'business_overview': '삼성전자는 글로벌 반도체 시장 점유율 1위 기업으로 '
                                 'DRAM 시장에서 42.5%의 점유율을 보유하고 있습니다. '
                                 '전환비용이 높은 반도체 장비와 공정 기술로 인해 '
                                 '경쟁사 대비 원가우위를 확보하고 있습니다.',
            'rnd': '연구개발비 25조원 투자. 특허 보유 건수 18만건 이상.',
        }
        financials = {
            'revenue': 258_000_000_000_000,
            'operating_margin': 0.15,
            'rnd_expenses': 25_000_000_000_000,
        }

        evidence = extractor.extract_evidences(
            '삼성전자', '005930', report_sections, financials
        )

        assert evidence is not None
        assert len(evidence.evidences) > 0
        assert evidence.total_quality > 0

    def test_extract_no_data(self, extractor):
        """No data should return empty evidence, not crash"""
        evidence = extractor.extract_evidences(
            '테스트', '000000', {}, {}
        )
        assert evidence is not None
        assert len(evidence.evidences) == 0

    def test_evidence_quality_scoring(self, extractor):
        """Evidence with numbers should score higher"""
        report_sections = {
            'business_overview': '시장 점유율 42.5% 달성. 경쟁사 대비 원가우위 확보.',
        }
        evidence = extractor.extract_evidences(
            '테스트', '000000', report_sections, {}
        )

        # Evidence with numbers should have higher quality
        for ev in evidence.evidences:
            if ev.has_numbers:
                assert ev.quality_score >= 1.5


# ── Moat Evaluator v2 Tests ───────────────────────────────

class TestMoatEvaluatorV2:
    """Test evidence-based moat evaluation with fail-safe downgrade"""

    @pytest.fixture
    def evaluator(self):
        from moat_evaluator_v2 import MoatEvaluatorV2
        return MoatEvaluatorV2()

    @pytest.fixture
    def evidence_extractor(self):
        from evidence_extractor import EvidenceExtractor
        return EvidenceExtractor()

    @pytest.fixture
    def bm_analyzer(self):
        from bm_analyzer import BMAnalyzer
        return BMAnalyzer()

    def test_evaluate_with_strong_evidence(self, evaluator, evidence_extractor, bm_analyzer):
        """Strong evidence should yield moat strength >= 3"""
        report_sections = {
            'business_overview': '글로벌 반도체 시장 점유율 1위, DRAM 42.5%, NAND 35.2%. '
                                 '전환비용이 매우 높은 산업 특성상 진입장벽 확보. '
                                 '규모의 경제를 통한 원가우위 달성. '
                                 '삼성전자 브랜드 가치 세계 5위.',
            'rnd': '연구개발비 25조원, 특허 18만건 보유. R&D 투자 업계 최대.',
        }
        financials = {
            'revenue': 258_000_000_000_000,
            'operating_margin': 0.15,
        }

        evidence = evidence_extractor.extract_evidences(
            '삼성전자', '005930', report_sections, financials
        )
        bm = bm_analyzer.analyze(
            '삼성전자', '005930', report_sections, financials, None,
            'Information Technology', 'Semiconductors'
        )
        classification = {
            'gics_sector': 'Information Technology',
            'gics_industry': 'Semiconductors',
        }

        evaluation = evaluator.evaluate(
            '삼성전자', '005930', evidence, bm, classification
        )

        assert evaluation is not None
        assert evaluation.moat_strength >= 3
        assert evaluation.moat_strength <= 5
        assert evaluation.evidence_based is True

    def test_evaluate_no_evidence_capped_at_2(self, evaluator, evidence_extractor, bm_analyzer):
        """No evidence should cap moat strength at 2 (fail-safe)"""
        evidence = evidence_extractor.extract_evidences(
            '테스트', '000000', {}, {}
        )
        bm = bm_analyzer.analyze(
            '테스트', '000000', {}, {}, None, '', ''
        )
        classification = {'gics_sector': '', 'gics_industry': ''}

        evaluation = evaluator.evaluate(
            '테스트', '000000', evidence, bm, classification
        )

        assert evaluation.moat_strength <= 2

    def test_moat_desc_format(self, evaluator, evidence_extractor, bm_analyzer):
        """Moat description should be non-empty string"""
        evidence = evidence_extractor.extract_evidences(
            '테스트', '000000', {}, {}
        )
        bm = bm_analyzer.analyze(
            '테스트', '000000', {}, {}, None, '', ''
        )
        classification = {'gics_sector': '', 'gics_industry': ''}

        evaluation = evaluator.evaluate(
            '테스트', '000000', evidence, bm, classification
        )

        assert isinstance(evaluation.moat_desc, str)
        assert len(evaluation.moat_desc) > 0


# ── Sustainability Checker Tests ───────────────────────────

class TestSustainabilityChecker:
    """Test 3-check sustainability verification (Step E)"""

    @pytest.fixture
    def checker(self):
        from sustainability_checker import SustainabilityChecker
        return SustainabilityChecker()

    def test_check_healthy_company(self, checker):
        """Healthy company with growth should not be downgraded"""
        financials = {
            'revenue': 258_000_000_000_000,
            'operating_margin': 0.15,
            'rnd_expenses': 25_000_000_000_000,
            'sga_expenses': 15_000_000_000_000,
        }
        multi_year = {
            '2021': {'revenue': 230_000_000_000_000},
            '2022': {'revenue': 250_000_000_000_000},
            '2023': {'revenue': 258_000_000_000_000},
        }

        result = checker.check(
            '삼성전자', financials, multi_year, {}, 4
        )

        assert result is not None
        assert 'adjusted_strength' in result
        assert result['adjusted_strength'] >= 3

    def test_check_no_data(self, checker):
        """No data should not crash"""
        result = checker.check('테스트', {}, {}, {}, 3)
        assert result is not None
        assert 'adjusted_strength' in result

    def test_never_upgrades(self, checker):
        """Sustainability check should never upgrade, only downgrade"""
        result = checker.check('테스트', {}, {}, {}, 2)
        assert result['adjusted_strength'] <= 2


# ── AI Verifier Tests ──────────────────────────────────────

class TestAIVerifier:
    """Test AI verifier in mock mode (no API key)"""

    @pytest.fixture
    def verifier(self):
        from ai_verifier import AIVerifier
        return AIVerifier(api_key=None)

    def test_disabled_without_api_key(self, verifier):
        """Should be disabled without API key"""
        assert verifier.enabled is False

    def test_verify_returns_structure(self, verifier):
        """Verify should return proper structure even when disabled"""
        result = verifier.verify(
            '삼성전자', '005930', 3,
            '해자 설명', 'BM 요약', '증거 요약', '지속가능성',
            {'gics_sector': 'IT', 'korean_sector_top': '반도체'}
        )

        assert 'verified' in result
        assert result['verified'] is False
        assert 'error' in result

    def test_generate_review_text(self, verifier):
        """Review text generation should work even when disabled"""
        result = verifier.verify(
            '테스트', '000000', 2,
            '', '', '', '',
            {'gics_sector': '', 'korean_sector_top': ''}
        )
        text = verifier.generate_ai_review_text(result)
        assert isinstance(text, str)
        assert len(text) > 0


# ── DART Client Tests (unit, no API calls) ─────────────────

class TestDARTClientUnit:
    """Unit tests for DART client (no actual API calls)"""

    @pytest.fixture
    def client(self):
        from dart_client import DARTClient
        return DARTClient(api_key="test_key")

    def test_parse_financial_accounts(self, client):
        """Financial account parsing should handle standard DART format"""
        accounts = [
            {'account_nm': '매출액', 'thstrm_amount': '258,000,000,000', 'sj_nm': '손익계산서'},
            {'account_nm': '영업이익', 'thstrm_amount': '6,500,000,000', 'sj_nm': '손익계산서'},
            {'account_nm': '당기순이익', 'thstrm_amount': '5,000,000,000', 'sj_nm': '손익계산서'},
            {'account_nm': '자산총계', 'thstrm_amount': '400,000,000,000', 'sj_nm': '재무상태표'},
            {'account_nm': '부채총계', 'thstrm_amount': '100,000,000,000', 'sj_nm': '재무상태표'},
            {'account_nm': '자본총계', 'thstrm_amount': '300,000,000,000', 'sj_nm': '재무상태표'},
        ]

        result = client._parse_financial_accounts(accounts, '2023')

        assert result['revenue'] == 258_000_000_000
        assert result['operating_income'] == 6_500_000_000
        assert result['net_income'] == 5_000_000_000
        assert result['total_assets'] == 400_000_000_000
        assert 'operating_margin' in result
        assert 'roe' in result
        assert 'debt_ratio' in result

    def test_parse_financial_empty(self, client):
        """Empty accounts should return zeros"""
        result = client._parse_financial_accounts([], '2023')
        assert result['revenue'] == 0
        assert result['operating_income'] == 0

    def test_cache_path_structure(self, client):
        """Cache paths should be properly structured"""
        from dart_client import CACHE_DIR
        path = client._get_cache_path('00126380', 'financials')
        assert '00126380' in str(path)
        assert 'financials' in str(path)

    def test_cache_path_corp_codes(self, client):
        """Corp codes cache should be at root level"""
        path = client._get_cache_path('', 'corp_codes')
        assert 'corp_codes.json' in str(path)


# ── Report Parser Tests ────────────────────────────────────

class TestDARTReportParser:
    """Test DART report text parsing"""

    @pytest.fixture
    def parser(self):
        from dart_report_parser import DARTReportParser
        return DARTReportParser()

    def test_parse_empty_text(self, parser):
        """Empty text should return empty sections"""
        result = parser.parse_report('')
        assert isinstance(result, dict)

    def test_parse_with_sections(self, parser):
        """Text with section markers should be parsed"""
        text = """
        II. 사업의 내용
        1. 사업의 개요
        삼성전자는 글로벌 전자기업으로 반도체, 디스플레이, IT 모바일 등의 사업을 영위합니다.

        2. 주요 제품 및 서비스
        DRAM, NAND Flash, 파운드리, 갤럭시 스마트폰

        3. 경쟁 현황
        반도체: SK하이닉스, 마이크론
        스마트폰: 애플, 샤오미

        4. 연구개발 현황
        연구개발비 25조원 투자. 반도체 미세공정 기술 개발 중.
        """

        result = parser.parse_report(text)
        assert isinstance(result, dict)

    def test_parse_quality(self, parser):
        """Parse quality should report coverage"""
        result = parser.parse_report('사업의 개요 테스트 텍스트')
        quality = parser.get_parse_quality(result)
        assert 'total_sections_found' in quality
        assert 'total_sections_possible' in quality
        assert 'total_text_length' in quality


# ── Integration Test ───────────────────────────────────────

class TestPipelineIntegration:
    """Integration tests for the full pipeline (without API calls)"""

    def test_evidence_to_evaluation_flow(self):
        """Test the evidence → moat evaluation flow end-to-end"""
        from evidence_extractor import EvidenceExtractor
        from moat_evaluator_v2 import MoatEvaluatorV2
        from bm_analyzer import BMAnalyzer
        from sustainability_checker import SustainabilityChecker

        extractor = EvidenceExtractor()
        evaluator = MoatEvaluatorV2()
        bm_analyzer = BMAnalyzer()
        checker = SustainabilityChecker()

        report_sections = {
            'business_overview': '시장 점유율 42.5% 1위. 전환비용 높은 반도체 산업.',
        }
        financials = {
            'revenue': 258_000_000_000_000,
            'operating_margin': 0.15,
        }

        # Step 1: Extract evidence
        evidence = extractor.extract_evidences(
            '삼성전자', '005930', report_sections, financials
        )

        # Step 2: Analyze BM
        bm = bm_analyzer.analyze(
            '삼성전자', '005930', report_sections, financials, None,
            'Information Technology', 'Semiconductors'
        )

        # Step 3: Evaluate moat
        classification = {
            'gics_sector': 'Information Technology',
            'gics_industry': 'Semiconductors',
        }
        evaluation = evaluator.evaluate(
            '삼성전자', '005930', evidence, bm, classification
        )

        # Step 4: Sustainability check
        sustainability = checker.check(
            '삼성전자', financials, {}, report_sections,
            evaluation.moat_strength
        )

        # Verify pipeline output
        assert evaluation.moat_strength >= 1
        assert evaluation.moat_strength <= 5
        assert sustainability['adjusted_strength'] <= evaluation.moat_strength
        assert isinstance(evaluation.moat_desc, str)

    def test_construction_company_low_moat(self):
        """Construction company should get low moat (1-2) with minimal data"""
        from evidence_extractor import EvidenceExtractor
        from moat_evaluator_v2 import MoatEvaluatorV2
        from bm_analyzer import BMAnalyzer

        extractor = EvidenceExtractor()
        evaluator = MoatEvaluatorV2()
        bm_analyzer = BMAnalyzer()

        evidence = extractor.extract_evidences(
            '남광토건', '001260', {}, {}
        )
        bm = bm_analyzer.analyze(
            '남광토건', '001260', {}, {}, None,
            'Industrials', 'Construction & Engineering'
        )
        classification = {
            'gics_sector': 'Industrials',
            'gics_industry': 'Construction & Engineering',
        }

        evaluation = evaluator.evaluate(
            '남광토건', '001260', evidence, bm, classification
        )

        # Construction company with no evidence = low moat
        assert evaluation.moat_strength <= 2
