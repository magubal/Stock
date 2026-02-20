"""
Research Service
----------------
Skill: research
Workflows: /06-review-improvement, /07-trend-research

기업분석, 트렌드 리서치, 인사이트 정리
"""

from datetime import datetime


class ResearchService:
    """Research Skill Implementation"""
    
    def __init__(self, config):
        self.config = config
    
    def evaluate_company(self, symbol, company_data=None):
        """
        기업 가치 분석 (investment-philosophy.md 기반)
        
        위대한 기업 찾기 기준:
        1. 고객가치제안을 명확히 이해
        2. 변화에 민감하게 반응
        3. 환경을 지배하거나 바꾸는 기업
        """
        evaluation_framework = {
            'customer_value_proposition': {
                'name': '고객가치제안',
                'criteria': [
                    {'item': '철학/미션', 'description': '차별적 혜택을 주는 명확한 철학이 있는가', 'score': None},
                    {'item': '실질적 행동', 'description': '철학을 실행하는 구체적 행동이 있는가', 'score': None},
                    {'item': '경쟁력 증거', 'description': '실질적 경쟁력 상승의 증거가 있는가', 'score': None}
                ]
            },
            'industry_evaluation': {
                'name': '산업 평가 (빅트렌드)',
                'criteria': [
                    {'item': '빅트렌드 부합', 'description': '트렌드 중심 산업 vs 쇠퇴 산업', 'score': None},
                    {'item': '해자요인', 'description': '과점/독점적 요인 多 vs 진입장벽 낮음', 'score': None},
                    {'item': '성장 변수', 'description': '변수 적음(리스크↓) vs 변수 많음(리스크↑)', 'score': None}
                ]
            },
            'competitive_advantage': {
                'name': '경쟁력 평가',
                'criteria': [
                    {'item': '차별적 혜택', 'description': '경쟁사 대비 차별적 혜택 수준', 'score': None},
                    {'item': '실행력', 'description': '고객가치제안의 실행력', 'score': None},
                    {'item': '경쟁력 상승', 'description': '경쟁력 상승 증거 유무', 'score': None}
                ]
            }
        }
        
        return {
            'symbol': symbol,
            'evaluation': evaluation_framework,
            'summary': '평가 미완료 - 데이터 입력 필요',
            'philosophy': '훌륭한 기업을 발굴하고 검증하는 과정',
            'timestamp': datetime.now().isoformat()
        }
    
    def research_trend(self, topic):
        """
        트렌드 리서치 (Workflow: /07-trend-research)
        
        탐색 영역:
        - 탐색(on): 새로운 흐름 발견
        - 탐사(off): 심층 분석
        - 탐구: 본질 파악
        """
        research_framework = {
            'topic': topic,
            'exploration': {
                'on': {'name': '탐색', 'focus': '새로운 흐름 발견', 'status': 'pending'},
                'off': {'name': '탐사', 'focus': '심층 분석', 'status': 'pending'},
                'deep': {'name': '탐구', 'focus': '본질 파악', 'status': 'pending'}
            },
            'keywords': ['탐색', '탐사', '탐구'],
            'timestamp': datetime.now().isoformat()
        }
        
        return research_framework
    
    def create_review(self, symbol, trade_result=None):
        """
        복기 및 개선 (Workflow: /06-review-improvement)
        """
        review_template = {
            'symbol': symbol,
            'review_items': [
                {'item': '진입 타이밍', 'evaluation': None, 'lesson': None},
                {'item': '목표가 설정', 'evaluation': None, 'lesson': None},
                {'item': '손절 라인', 'evaluation': None, 'lesson': None},
                {'item': '시나리오 정확도', 'evaluation': None, 'lesson': None},
                {'item': '심리 관리', 'evaluation': None, 'lesson': None}
            ],
            'improvements': [],
            'timestamp': datetime.now().isoformat()
        }
        
        return review_template
    
    def create_insight(self, title, content, category='general'):
        """
        인사이트 정리
        
        Categories: reading, market_letter, expert_opinion, general
        """
        return {
            'title': title,
            'content': content,
            'category': category,
            'source': None,
            'tags': [],
            'created_at': datetime.now().isoformat()
        }
