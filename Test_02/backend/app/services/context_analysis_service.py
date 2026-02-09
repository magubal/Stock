"""
AI 맥락 분석 엔진 - 2단계: 맥락연결/영향분석
투자자심리 → 가능행동 유형 분석 및 시나리오 생성
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from enum import Enum

class SentimentType(Enum):
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"

class ImpactLevel(Enum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"

class InvestorType(Enum):
    SHORT_TERM = "short_term"      # 단기 투자자
    MID_LONG_TERM = "mid_long_term"  # 중장기 투자자
    HOLDER = "holder"               # 보유자
    POTENTIAL = "potential"         # 잠재 투자자

@dataclass
class SentimentScore:
    """감성 분석 결과"""
    sentiment: SentimentType
    score: float  # -1.0 ~ 1.0
    confidence: float  # 0.0 ~ 1.0
    keywords: List[str]

@dataclass
class MarketImpact:
    """시장 영향 분석"""
    level: ImpactLevel
    market_scope: str  # 시장 전체, 섹터, 종목
    direction: str  # 상승, 하락, 보합
    duration_estimate: str  # 단기, 중기, 장기
    confidence: float

@dataclass
class InvestorBehavior:
    """투자자 행동 유형 예측"""
    investor_type: InvestorType
    behavior_type: str  # 매수, 매도, 관망
    probability: float  # 0.0 ~ 1.0
    reasoning: str
    timing_expectation: str  # 즉시, 단기, 중장기

@dataclass
class ContextAnalysis:
    """종합적인 맥락 분석 결과"""
    news_id: str
    title: str
    content_summary: str
    sentiment_score: SentimentScore
    market_impact: MarketImpact
    investor_behaviors: List[InvestorBehavior]
    key_factors: List[str]
    related_stocks: List[str]
    analysis_timestamp: datetime
    confidence_score: float

class ContextAnalyzer:
    """AI 맥락 분석 엔진"""
    
    def __init__(self):
        self.positive_keywords = [
            '상승', '급등', '호조', '강세', '개선', '성장', '호황', '반등', '상향', '긍정',
            '기대', '선호', '매수', '수혜', '실적개선', '목표가상향', '투자의견상향'
        ]
        
        self.negative_keywords = [
            '하락', '급락', '약세', '부진', '악화', '위기', '불황', '조정', '하향', '부정',
            '우려', '위험', '매도', '피해', '실적악화', '목표가하향', '투자의견하향'
        ]
        
        self.stock_pattern = re.compile(r'[A-Z\d]{4,6}|삼성|LG|SK|현대|기자|포스코|HMM|셀트리온|바이오|뱅크')
        self.sector_pattern = re.compile(
            r'(반도체|자동차|조선|철강|화학|바이오|IT|게임|금융|은행|보험|증권|건설|통신|운송|항공|유통|식품|의료|에너지)'
        )
    
    def analyze_sentiment(self, text: str) -> SentimentScore:
        """텍스트 감성 분석"""
        text_lower = text.lower()
        
        # 긍정/부정 키워드 카운트
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        
        # 감성 점수 계산 (-1.0 ~ 1.0)
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            score = 0.0
            sentiment = SentimentType.NEUTRAL
            confidence = 0.5
        else:
            score = (positive_count - negative_count) / total_keywords
            if score > 0.6:
                sentiment = SentimentType.VERY_POSITIVE
            elif score > 0.2:
                sentiment = SentimentType.POSITIVE
            elif score > -0.2:
                sentiment = SentimentType.NEUTRAL
            elif score > -0.6:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.VERY_NEGATIVE
            
            confidence = min(0.9, total_keywords * 0.1 + 0.3)
        
        # 키워드 추출
        keywords = []
        for keyword in self.positive_keywords + self.negative_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return SentimentScore(
            sentiment=sentiment,
            score=score,
            confidence=confidence,
            keywords=keywords[:10]  # 상위 10개만
        )
    
    def extract_market_impact(self, text: str, sentiment_score: SentimentScore) -> MarketImpact:
        """시장 영향 분석"""
        text_lower = text.lower()
        
        # 영향 레벨 추정
        impact_keywords = {
            ImpactLevel.VERY_HIGH: ['폭발', '충격', '이례적', '역사적', '전면재검토', '대규모'],
            ImpactLevel.HIGH: ['급변', '큰 폭', '상당', '중대', '핵심', '주요'],
            ImpactLevel.MEDIUM: ['일부', '부분', '제한적', '예상', '잠재'],
            ImpactLevel.LOW: ['소폭', '미미', '제한', '일시적'],
            ImpactLevel.VERY_LOW: ['참고', '관망', '단순', '정보']
        }
        
        impact_level = ImpactLevel.MEDIUM
        for level, keywords in impact_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                impact_level = level
                break
        
        # 시장 범위 추정
        market_scope = "종목"
        if any(word in text_lower for word in ['시장 전체', '전체 시장', '코스피', '코스닥']):
            market_scope = "시장 전체"
        elif any(word in text_lower for word in ['섹터', '업종', '산업']):
            market_scope = "섹터"
        
        # 방향성 추정
        if sentiment_score.score > 0.1:
            direction = "상승"
        elif sentiment_score.score < -0.1:
            direction = "하락"
        else:
            direction = "보합"
        
        # 기간 추정
        duration_keywords = {
            "단기": ['당일', '단기', '즉시', '급변', '일시적'],
            "중기": ['향후', '수개월', '분기', '예상'],
            "장기": ['장기', '구조적', '지속적', '본질적']
        }
        
        duration_estimate = "중기"
        for duration, keywords in duration_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                duration_estimate = duration
                break
        
        return MarketImpact(
            level=impact_level,
            market_scope=market_scope,
            direction=direction,
            duration_estimate=duration_estimate,
            confidence=sentiment_score.confidence * 0.8
        )
    
    def predict_investor_behaviors(self, 
                                   text: str, 
                                   sentiment_score: SentimentScore,
                                   market_impact: MarketImpact) -> List[InvestorBehavior]:
        """투자자별 행동 예측"""
        behaviors = []
        
        # 단기 투자자 행동 예측
        short_term_behavior = self._predict_short_term_behavior(text, sentiment_score, market_impact)
        behaviors.append(short_term_behavior)
        
        # 중장기 투자자 행동 예측
        mid_long_term_behavior = self._predict_mid_long_term_behavior(text, sentiment_score, market_impact)
        behaviors.append(mid_long_term_behavior)
        
        # 보유자 행동 예측
        holder_behavior = self._predict_holder_behavior(text, sentiment_score, market_impact)
        behaviors.append(holder_behavior)
        
        # 잠재 투자자 행동 예측
        potential_behavior = self._predict_potential_behavior(text, sentiment_score, market_impact)
        behaviors.append(potential_behavior)
        
        return behaviors
    
    def _predict_short_term_behavior(self, text: str, sentiment_score: SentimentScore, 
                                   market_impact: MarketImpact) -> InvestorBehavior:
        """단기 투자자 행동 예측"""
        text_lower = text.lower()
        
        if market_impact.level in [ImpactLevel.VERY_HIGH, ImpactLevel.HIGH]:
            if sentiment_score.sentiment in [SentimentType.VERY_POSITIVE, SentimentType.POSITIVE]:
                return InvestorBehavior(
                    investor_type=InvestorType.SHORT_TERM,
                    behavior_type="매수",
                    probability=0.8,
                    reasoning="급격한 호재로 단기 수급 개선 기대",
                    timing_expectation="즉시"
                )
            else:
                return InvestorBehavior(
                    investor_type=InvestorType.SHORT_TERM,
                    behavior_type="매도",
                    probability=0.7,
                    reasoning="급격한 악재로 손실 확산 우려",
                    timing_expectation="즉시"
                )
        
        return InvestorBehavior(
            investor_type=InvestorType.SHORT_TERM,
            behavior_type="관망",
            probability=0.6,
            reasoning="명확한 단기 방향성 부재",
            timing_expectation="단기"
        )
    
    def _predict_mid_long_term_behavior(self, text: str, sentiment_score: SentimentScore,
                                       market_impact: MarketImpact) -> InvestorBehavior:
        """중장기 투자자 행동 예측"""
        if market_impact.duration_estimate in ["중기", "장기"]:
            if sentiment_score.sentiment in [SentimentType.POSITIVE, SentimentType.VERY_POSITIVE]:
                return InvestorBehavior(
                    investor_type=InvestorType.MID_LONG_TERM,
                    behavior_type="매수",
                    probability=0.7,
                    reasoning="중장기 펀더멘털 개선 기대",
                    timing_expectation="중장기"
                )
        
        return InvestorBehavior(
            investor_type=InvestorType.MID_LONG_TERM,
            behavior_type="관망",
            probability=0.8,
            reasoning="단기 변동성 대비 중장기 관점 검토",
            timing_expectation="중장기"
        )
    
    def _predict_holder_behavior(self, text: str, sentiment_score: SentimentScore,
                               market_impact: MarketImpact) -> InvestorBehavior:
        """보유자 행동 예측"""
        text_lower = text.lower()
        
        # 가격부담 감지 키워드
        price_pressure_keywords = ['가격부담', '과열', '급등', '상승부담']
        
        if any(keyword in text_lower for keyword in price_pressure_keywords):
            return InvestorBehavior(
                investor_type=InvestorType.HOLDER,
                behavior_type="매도",
                probability=0.6,
                reasoning="가격부담감으로 인한 익실현 고려",
                timing_expectation="단기"
            )
        
        if sentiment_score.sentiment in [SentimentType.NEGATIVE, SentimentType.VERY_NEGATIVE]:
            return InvestorBehavior(
                investor_type=InvestorType.HOLDER,
                behavior_type="매도",
                probability=0.5,
                reasoning="부정적 요소로 인한 보유 리스크 고려",
                timing_expectation="단기"
            )
        
        return InvestorBehavior(
            investor_type=InvestorType.HOLDER,
            behavior_type="관망",
            probability=0.7,
            reasoning="기존 보유 전략 유지",
            timing_expectation="중장기"
        )
    
    def _predict_potential_behavior(self, text: str, sentiment_score: SentimentScore,
                                  market_impact: MarketImpact) -> InvestorBehavior:
        """잠재 투자자 행동 예측"""
        if sentiment_score.sentiment in [SentimentType.POSITIVE, SentimentType.VERY_POSITIVE]:
            return InvestorBehavior(
                investor_type=InvestorType.POTENTIAL,
                behavior_type="매수",
                probability=0.6,
                reasoning="진입 기회로 판단",
                timing_expectation="단기"
            )
        
        return InvestorBehavior(
            investor_type=InvestorType.POTENTIAL,
            behavior_type="관망",
            probability=0.8,
            reasoning="추가 관망 및 신호 확인",
            timing_expectation="단기"
        )
    
    def extract_key_factors(self, text: str) -> List[str]:
        """핵심 요인 추출"""
        # 핵심 이슈 키워드 패턴
        issue_patterns = [
            r'실적.*?(개선|악화|상향|하향)',
            r'목표가.*?(상향|하향)',
            r'투자의견.*?(상향|하향)',
            r'정부.*?(정책|규제|지원)',
            r'원/달러.*?(환율|변동)',
            r'금리.*?(인상|하락|동결)',
            r'수출.*?(증가|감소)',
            r'부동산.*?(규제|완화|가격)',
            r'미국.*?(연준|금리|경제)',
            r'중국.*()(경제|규제|무역)'
        ]
        
        factors = []
        for pattern in issue_patterns:
            matches = re.findall(pattern, text)
            if matches:
                factors.append(matches[0])
        
        # 관련 종목/섹터 추출
        stocks = self.stock_pattern.findall(text)
        sectors = self.sector_pattern.findall(text)
        
        factors.extend([f"{stock} 관련" for stock in stocks[:3]])
        factors.extend([f"{sector} 섹터" for sector in sectors[:2]])
        
        return factors[:8]  # 상위 8개 요인만
    
    def extract_related_stocks(self, text: str) -> List[str]:
        """관련 종목 추출"""
        stocks = self.stock_pattern.findall(text)
        # 종목코드 정규화 (6자리 숫자 또는 주요 기업명)
        normalized_stocks = []
        for stock in stocks:
            if stock.isdigit() and len(stock) >= 4:
                normalized_stocks.append(stock[:6])
            elif stock in ['삼성', 'LG', 'SK', '현대', '기자', '포스코', 'HMM', '셀트리온']:
                normalized_stocks.append(stock)
        
        return list(set(normalized_stocks))[:5]  # 중복 제거, 상위 5개
    
    def analyze_content(self, news_id: str, title: str, content: str) -> ContextAnalysis:
        """종합 콘텐츠 분석"""
        # 내용 요약 (첫 200자)
        content_summary = content[:200] + "..." if len(content) > 200 else content
        
        # 감성 분석
        full_text = title + " " + content
        sentiment_score = self.analyze_sentiment(full_text)
        
        # 시장 영향 분석
        market_impact = self.extract_market_impact(full_text, sentiment_score)
        
        # 투자자 행동 예측
        investor_behaviors = self.predict_investor_behaviors(full_text, sentiment_score, market_impact)
        
        # 핵심 요인 추출
        key_factors = self.extract_key_factors(full_text)
        
        # 관련 종목 추출
        related_stocks = self.extract_related_stocks(full_text)
        
        # 종합 신뢰도 점수
        confidence_score = min(0.95, (sentiment_score.confidence + market_impact.confidence) / 2 + 0.1)
        
        return ContextAnalysis(
            news_id=news_id,
            title=title,
            content_summary=content_summary,
            sentiment_score=sentiment_score,
            market_impact=market_impact,
            investor_behaviors=investor_behaviors,
            key_factors=key_factors,
            related_stocks=related_stocks,
            analysis_timestamp=datetime.now(),
            confidence_score=confidence_score
        )

# 사용 예시
if __name__ == "__main__":
    analyzer = ContextAnalyzer()
    
    # 테스트용 뉴스 데이터
    test_news = {
        "id": "test_001",
        "title": "삼성전자, 4분기 실적 시장 예상 상회... 반도체 회복세 기대감↑",
        "content": "삼성전자가 4분기 실적이 시장 예상을 상회할 것이라는 전망이 나오고 있다. 반도체 업황의 점진적 회복세와 함께 메모리 반도체 가격 상승이 실적 개선에 기여할 것으로 보인다. 증권사들은 연이어 삼성전자의 목표가를 상향 조정하며 투자의견을 '매수'로 유지하고 있다. 다만, 세계 경제 둔화 우려로 단기적인 변동성은 불가피할 것으로 전망된다."
    }
    
    # 분석 실행
    analysis = analyzer.analyze_content(
        test_news["id"],
        test_news["title"], 
        test_news["content"]
    )
    
    # 결과 출력
    print(f"분석 결과 (ID: {analysis.news_id})")
    print(f"제목: {analysis.title}")
    print(f"요약: {analysis.content_summary}")
    print(f"감성: {analysis.sentiment_score.sentiment.value} (점수: {analysis.sentiment_score.score:.2f})")
    print(f"시장영향: {analysis.market_impact.direction} ({analysis.market_impact.level.value})")
    print(f"핵심요인: {', '.join(analysis.key_factors)}")
    print(f"관련종목: {', '.join(analysis.related_stocks)}")
    print(f"신뢰도: {analysis.confidence_score:.2f}")
    
    print("\n투자자별 행동 예측:")
    for behavior in analysis.investor_behaviors:
        print(f"- {behavior.investor_type.value}: {behavior.behavior_type} ({behavior.probability:.0%}) - {behavior.reasoning}")