/**
 * 텍스트 전처리 및 투자 심리 분석 모듈
 * 수집된 텔레그램 메시지의 투자 심리를 분석하고 정제
 */

class MessagePreprocessor {
    constructor() {
        this.sentimentDictionary = this.initializeSentimentDictionary();
        this.stockTerms = this.initializeStockTerms();
        this.investmentPatterns = this.initializeInvestmentPatterns();
    }

    /**
     * 감성 사전 초기화
     */
    initializeSentimentDictionary() {
        return {
            // 긍정적 표현
            positive: [
                '상승', '오름', '급등', '상승세', '강세', '최고', '신고', '대박', '수익', '성공',
                '확신', '추천', '매수', '강력매수', '목표가', '상향', '기대', '호재', '긍정적',
                '반등', '회복', '돌파', '상승장', '상한가', '폭등', '큰손', '물량', '매집'
            ],
            // 부정적 표현
            negative: [
                '하락', '내림', '급락', '하락세', '약세', '최저', '신저', '대패', '손실', '실패',
                '우려', '비관', '매도', '강력매도', '하향', '악재', '부정적', '하락장',
                '하한가', '폭락', '작전', '탈주', '이탈', '분산', '환매'
            ],
            // 중립적 표현
            neutral: [
                '보합', '횡보', '관망', '대기', '분석', '예측', '전망', '정보', '뉴스', '공시',
                '발표', '결산', '실적', '보고서', '리서치', '의견', '목표가', '전망치'
            ]
        };
    }

    /**
     * 주식 용어 사전 초기화
     */
    initializeStockTerms() {
        return {
            market: ['코스피', '코스닥', '나스닥', '다우', 'S&P', '상하이', '닛케이'],
            sector: ['반도체', '바이오', 'IT', '금융', '자동차', '화학', '철강', '건설', '통신'],
            type: ['주식', '채권', '선물', '옵션', 'ETF', 'ETN', '펀드', '코인', '암호화폐'],
            analysis: ['기술적', '펀더멘탈', '심리적', '수급', '차트', '보조지표', '이동평균']
        };
    }

    /**
     * 투자 패턴 초기화
     */
    initializeInvestmentPatterns() {
        return {
            bullPatterns: ['상승 돌파', '상승 지속', '바닥 형성', '반등 시작', '급등세'],
            bearPatterns: ['하락 돌파', '하락 지속', '천장 형성', '조정 시작', '급락세'],
            neutralPatterns: ['횡보장', '박스권', '등락 반복', '관망세', '대기 중']
        };
    }

    /**
     * 메시지 텍스트 전처리
     */
    preprocessText(text) {
        return {
            original: text,
            cleaned: this.cleanText(text),
            tokens: this.tokenize(text),
            entities: this.extractEntities(text),
            sentiment: this.analyzeSentiment(text),
            investmentTerms: this.extractInvestmentTerms(text),
            urgency: this.assessUrgency(text),
            reliability: this.assessReliability(text)
        };
    }

    /**
     * 텍스트 정제
     */
    cleanText(text) {
        return text
            .replace(/[^\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F\w\s.#]/g, '') // 한글, 영문, 숫자, 기호 유지
            .replace(/\s+/g, ' ') // 공백 정리
            .trim();
    }

    /**
     * 토큰화
     */
    tokenize(text) {
        return text
            .toLowerCase()
            .split(/[\s,.!?;:()[\]{}'"`]+/)
            .filter(token => token.length > 0);
    }

    /**
     * 엔티티 추출 (종목코드, 금액 등)
     */
    extractEntities(text) {
        const entities = {
            stocks: this.extractStockCodes(text),
            prices: this.extractPrices(text),
            percentages: this.extractPercentages(text),
            dates: this.extractDates(text),
            companies: this.extractCompanies(text)
        };

        return entities;
    }

    /**
     * 종목코드 추출
     */
    extractStockCodes(text) {
        // 6자리 종목코드 추출
        const stockCodePattern = /\b([A-Z0-9]{6})\b|\b(\d{6})\b/g;
        return [...text.matchAll(stockCodePattern)].map(match => match[0]);
    }

    /**
     * 금액 추출
     */
    extractPrices(text) {
        const pricePattern = /(\d{1,3}(?:,\d{3})*\s?원|\d{1,3}(?:,\d{3})*\s?달러|\$[\d,]+)/g;
        return [...text.matchAll(pricePattern)].map(match => match[0]);
    }

    /**
     * 퍼센트 추출
     */
    extractPercentages(text) {
        const percentPattern = /(\d+(?:\.\d+)?%)/g;
        return [...text.matchAll(percentPattern)].map(match => match[0]);
    }

    /**
     * 날짜 추출
     */
    extractDates(text) {
        const datePattern = /(\d{4}[-/]?\d{1,2}[-/]?\d{1,2}|\d{1,2}\/\d{1,2})/g;
        return [...text.matchAll(datePattern)].map(match => match[0]);
    }

    /**
     * 기업명 추출
     */
    extractCompanies(text) {
        // 주요 기업명 목록 (확장 필요)
        const companies = [
            '삼성전자', 'LG에너지솔루션', 'SK하이닉스', '삼성바이오로직스', 'LG화학',
            '현대차', '기아', 'POSCO홀딩스', 'NAVER', '카카오', '삼성SDI',
            '셀트리온', '현대모비스', 'KB금융', '신한지주', '하나금융지주'
        ];
        
        return companies.filter(company => text.includes(company));
    }

    /**
     * 감성 분석
     */
    analyzeSentiment(text) {
        const tokens = this.tokenize(text);
        
        let positiveScore = 0;
        let negativeScore = 0;
        let neutralScore = 0;

        tokens.forEach(token => {
            if (this.sentimentDictionary.positive.some(word => token.includes(word))) {
                positiveScore++;
            }
            if (this.sentimentDictionary.negative.some(word => token.includes(word))) {
                negativeScore++;
            }
            if (this.sentimentDictionary.neutral.some(word => token.includes(word))) {
                neutralScore++;
            }
        });

        const totalScore = positiveScore + negativeScore + neutralScore;
        
        let sentiment = 'neutral';
        let confidence = 0.5;

        if (totalScore > 0) {
            if (positiveScore > negativeScore) {
                sentiment = 'positive';
                confidence = positiveScore / totalScore;
            } else if (negativeScore > positiveScore) {
                sentiment = 'negative';
                confidence = negativeScore / totalScore;
            } else {
                sentiment = 'neutral';
                confidence = neutralScore / totalScore;
            }
        }

        return {
            sentiment,
            confidence,
            scores: {
                positive: positiveScore,
                negative: negativeScore,
                neutral: neutralScore
            }
        };
    }

    /**
     * 투자 용어 추출
     */
    extractInvestmentTerms(text) {
        const terms = {};
        
        Object.entries(this.stockTerms).forEach(([category, wordList]) => {
            const foundTerms = wordList.filter(term => 
                text.toLowerCase().includes(term.toLowerCase())
            );
            if (foundTerms.length > 0) {
                terms[category] = foundTerms;
            }
        });

        return terms;
    }

    /**
     * 긴급성 평가
     */
    assessUrgency(text) {
        const urgencyIndicators = [
            '긴급', '즉시', '지금', '바로', '빨리', '급등', '급락', '대박', '대패',
            '찬스', '마감임박', '오늘', '내일', '급변', '급작스러운'
        ];

        const urgencyScore = urgencyIndicators.filter(indicator => 
            text.includes(indicator)
        ).length;

        let urgency = 'low';
        if (urgencyScore >= 3) urgency = 'high';
        else if (urgencyScore >= 1) urgency = 'medium';

        return { urgency, score: urgencyScore };
    }

    /**
     * 신뢰도 평가
     */
    assessReliability(text) {
        let reliabilityScore = 50; // 기본 50점

        // 신뢰도 증가 요인
        if (text.includes('공시')) reliabilityScore += 20;
        if (text.includes('실적')) reliabilityScore += 15;
        if (text.includes('리서치')) reliabilityScore += 15;
        if (/\d{6}/.test(text)) reliabilityScore += 10; // 종목코드 포함
        if (/\d+%/.test(text)) reliabilityScore += 5; // 구체적 수치

        // 신뢰도 감소 요인
        if (text.includes('라도')) reliabilityScore -= 10;
        if (text.includes('아마')) reliabilityScore -= 15;
        if (text.includes('같아')) reliabilityScore -= 10;
        if (text.includes('??') || text.includes('!!!')) reliabilityScore -= 5;

        let reliability = 'medium';
        if (reliabilityScore >= 70) reliability = 'high';
        else if (reliabilityScore <= 40) reliability = 'low';

        return { reliability, score: Math.max(0, Math.min(100, reliabilityScore)) };
    }

    /**
     * 투자 심리 분석 리포트 생성
     */
    generateInvestmentPsychologyReport(processedMessages) {
        if (!processedMessages.length) {
            return { error: 'No messages to analyze' };
        }

        const totalMessages = processedMessages.length;
        const sentimentCounts = { positive: 0, negative: 0, neutral: 0 };
        const urgencyCounts = { high: 0, medium: 0, low: 0 };
        const reliabilityCounts = { high: 0, medium: 0, low: 0 };
        
        const topStocks = {};
        const topKeywords = {};

        processedMessages.forEach(msg => {
            // 감성 통계
            sentimentCounts[msg.sentiment.sentiment]++;
            
            // 긴급성 통계
            urgencyCounts[msg.urgency.urgency]++;
            
            // 신뢰도 통계
            reliabilityCounts[msg.reliability.reliability]++;
            
            // 종목 빈도
            msg.entities.stocks.forEach(stock => {
                topStocks[stock] = (topStocks[stock] || 0) + 1;
            });
            
            // 키워드 빈도
            msg.tokens.forEach(token => {
                if (token.length > 2) {
                    topKeywords[token] = (topKeywords[token] || 0) + 1;
                }
            });
        });

        // 정렬
        const sortedStocks = Object.entries(topStocks)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10);
            
        const sortedKeywords = Object.entries(topKeywords)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 20);

        return {
            summary: {
                totalMessages,
                sentimentDistribution: sentimentCounts,
                urgencyDistribution: urgencyCounts,
                reliabilityDistribution: reliabilityCounts,
                averageSentiment: this.calculateAverage(sentimentCounts),
                marketMood: this.determineMarketMood(sentimentCounts)
            },
            topStocks: sortedStocks,
            topKeywords: sortedKeywords,
            recommendations: this.generateRecommendations(sentimentCounts, urgencyCounts)
        };
    }

    /**
     * 평균 감성 계산
     */
    calculateAverage(sentimentCounts) {
        const total = sentimentCounts.positive + sentimentCounts.negative + sentimentCounts.neutral;
        if (total === 0) return 0;
        
        return (sentimentCounts.positive - sentimentCounts.negative) / total;
    }

    /**
     * 시장 분위기 결정
     */
    determineMarketMood(sentimentCounts) {
        const total = sentimentCounts.positive + sentimentCounts.negative + sentimentCounts.neutral;
        const positiveRatio = sentimentCounts.positive / total;
        const negativeRatio = sentimentCounts.negative / total;

        if (positiveRatio > 0.6) return 'very_bullish';
        if (positiveRatio > 0.4) return 'bullish';
        if (negativeRatio > 0.6) return 'very_bearish';
        if (negativeRatio > 0.4) return 'bearish';
        return 'neutral';
    }

    /**
     * 투자 추천사항 생성
     */
    generateRecommendations(sentimentCounts, urgencyCounts) {
        const recommendations = [];

        if (sentimentCounts.positive > sentimentCounts.negative * 1.5) {
            recommendations.push('시장 전반이 긍정적이므로 공격적인 투자 전략 고려');
        } else if (sentimentCounts.negative > sentimentCounts.positive * 1.5) {
            recommendations.push('시장 전반이 부정적이므로 방어적인 투자 전략 고려');
        }

        if (urgencyCounts.high > urgencyCounts.low * 2) {
            recommendations.push('급변성이 높으므로 신중한 접근 필요');
        }

        return recommendations;
    }
}

module.exports = MessagePreprocessor;