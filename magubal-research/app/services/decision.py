"""
Decision Service
-----------------
Skill: decision
Workflows: /04-decision-scenario, /05-execution-check

의사결정 시나리오, 리스크 평가, 기회 발굴
"""

from datetime import datetime


class DecisionService:
    """Decision Skill Implementation"""
    
    def __init__(self, config):
        self.config = config
    
    def create_scenario(self, symbol, current_price, analysis_result=None):
        """
        시나리오 작성 (Workflow: /04-decision-scenario)
        
        Returns: Multiple scenarios with conditions and actions
        """
        scenarios = []
        
        # 기본 시나리오 템플릿 (investment-philosophy.md 기반)
        base_scenarios = [
            {
                'type': 'bullish',
                'name': '상승 시나리오',
                'condition': '주요 기대요소 실현 시',
                'target_multiplier': 1.15,  # +15%
                'action': '보유 지속, 추가 매수 검토'
            },
            {
                'type': 'neutral',
                'name': '횡보 시나리오',
                'condition': '특별한 변화 없이 유지',
                'target_multiplier': 1.05,  # +5%
                'action': '현 포지션 유지'
            },
            {
                'type': 'bearish',
                'name': '하락 시나리오',
                'condition': '우려요소 현실화 시',
                'target_multiplier': 0.90,  # -10%
                'action': '매도 검토, 손절 라인 확인'
            }
        ]
        
        for template in base_scenarios:
            scenario = {
                'symbol': symbol,
                'type': template['type'],
                'name': template['name'],
                'condition': template['condition'],
                'target_price': round(current_price * template['target_multiplier']),
                'action': template['action'],
                'probability': self._estimate_probability(template['type'], analysis_result),
                'created_at': datetime.now().isoformat()
            }
            scenarios.append(scenario)
        
        return scenarios
    
    def _estimate_probability(self, scenario_type, analysis_result):
        """확률 추정 (분석 결과 기반)"""
        if not analysis_result:
            return 33  # 기본값
        
        sentiment = analysis_result.get('sentiment', 'neutral')
        
        if scenario_type == 'bullish':
            if sentiment == 'positive':
                return 50
            elif sentiment == 'negative':
                return 20
            else:
                return 30
        elif scenario_type == 'bearish':
            if sentiment == 'negative':
                return 50
            elif sentiment == 'positive':
                return 20
            else:
                return 30
        else:
            return 30
    
    def evaluate_risk(self, symbol, is_holder=False):
        """
        리스크 평가
        
        "변화는 기회(매수자)이자 리스크(보유자)이다"
        """
        # 기본 리스크 프레임워크
        risk_factors = {
            'market_risk': '시장 전체 변동성',
            'sector_risk': '섹터 특화 리스크',
            'company_risk': '개별 기업 리스크'
        }
        
        perspective = 'holder' if is_holder else 'buyer'
        
        return {
            'symbol': symbol,
            'perspective': perspective,
            'change_interpretation': '리스크' if is_holder else '기회',
            'risk_factors': risk_factors,
            'recommendation': '변화 모니터링 필요',
            'philosophy': '변화는 기회(매수자)이자 리스크(보유자)이다'
        }
    
    def check_execution(self, symbol, scenario_id=None):
        """
        실질확인 (Workflow: /05-execution-check)
        
        시세 및 실제 행동 확인
        """
        return {
            'symbol': symbol,
            'status': 'pending',
            'message': '시세 및 실제 행동 확인 필요',
            'checklist': [
                '현재가 확인',
                '거래량 확인',
                '시나리오 조건 충족 여부',
                '시장 분위기 확인'
            ],
            'timestamp': datetime.now().isoformat()
        }
    
    def evaluate_opportunity(self, company_info):
        """
        기회 발굴 (고객가치혁신 준비도 평가)
        """
        checklist = {
            'customer_value_proposition': '고객가치제안 명확성',
            'change_sensitivity': '변화 민감성',
            'era_direction_fit': '시대 방향성 적합도',
            'execution_readiness': 'HOW 준비도'
        }
        
        return {
            'company': company_info,
            'evaluation_criteria': checklist,
            'philosophy': '준비된(HOW) 자들 중 최고의 가능성을 지닌 자를 발굴'
        }
