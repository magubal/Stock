"""
Analysis Service
-----------------
Skill: analysis
Workflows: /02-context-analysis, /03-importance-evaluation

센티먼트 분석, 영향력 평가, 맥락 연결
"""

from datetime import datetime


class AnalysisService:
    """Analysis Skill Implementation"""
    
    def __init__(self, config):
        self.config = config
        
        # 중요 키워드 (영향력 평가용)
        self.importance_keywords = {
            'high': ['속보', '긴급', '단독', '급등', '급락', '실적', '공시', 'AI', '반도체'],
            'medium': ['상승', '하락', '신고가', '투자', '매수', '매도', '전망', '분석'],
            'low': ['보고서', '리포트', '전문가', '의견']
        }
        
        # 주요 언론사 (신뢰도 가중치용)
        self.major_sources = [
            '연합뉴스', '조선일보', '중앙일보', '동아일보', '한국경제',
            '매일경제', 'SBS', 'KBS', 'MBC', 'JTBC', '서울경제', '파이낸셜뉴스'
        ]
    
    def analyze_sentiment(self, text):
        """
        센티먼트 분석
        Returns: 'positive', 'negative', 'neutral'
        """
        positive_words = ['상승', '호재', '기대', '성장', '증가', '호실적', '강세', '반등']
        negative_words = ['하락', '악재', '우려', '감소', '약세', '폭락', '리스크', '위기']
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count > neg_count:
            return 'positive'
        elif neg_count > pos_count:
            return 'negative'
        else:
            return 'neutral'
    
    def evaluate_importance(self, title, description='', source=''):
        """
        중요도 평가 (Workflow: /03-importance-evaluation)
        Returns: score (0-100), level ('high', 'medium', 'low')
        """
        score = 0
        text = f"{title} {description}".lower()
        
        # 키워드 기반 점수
        for keyword in self.importance_keywords['high']:
            if keyword in text:
                score += 15
        
        for keyword in self.importance_keywords['medium']:
            if keyword in text:
                score += 8
        
        for keyword in self.importance_keywords['low']:
            if keyword in text:
                score += 3
        
        # 주요 언론사 가중치
        for ms in self.major_sources:
            if ms in source:
                score += 10
                break
        
        # 레벨 결정
        if score >= 50:
            level = 'high'
        elif score >= 25:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'score': min(score, 100),
            'level': level,
            'sentiment': self.analyze_sentiment(text)
        }
    
    def analyze_context(self, issue, investor_type='medium_term'):
        """
        맥락 연결 분석 (Workflow: /02-context-analysis)
        
        investor_type: 'short_term', 'medium_term', 'long_term', 'holder', 'potential'
        """
        # 투자자 유형별 관점 (investment-philosophy.md 기반)
        perspectives = {
            'short_term': {
                'focus': '즉각적 변동성 및 수급 심리',
                'timeframe': '1주일 이내'
            },
            'medium_term': {
                'focus': '구조적 변화 및 펀더멘털 영향',
                'timeframe': '3개월 ~ 6개월'
            },
            'long_term': {
                'focus': '빅트렌드 부합 및 성장성',
                'timeframe': '1년 이상'
            },
            'holder': {
                'focus': '기존 평가 유효성 및 대응 시나리오',
                'action': '보유/매도 결정'
            },
            'potential': {
                'focus': '진입 적기 및 기대 수익률',
                'action': '매수 타이밍'
            }
        }
        
        perspective = perspectives.get(investor_type, perspectives['medium_term'])
        importance = self.evaluate_importance(issue)
        
        return {
            'issue': issue,
            'investor_type': investor_type,
            'perspective': perspective,
            'importance': importance,
            'analysis_time': datetime.now().isoformat()
        }
