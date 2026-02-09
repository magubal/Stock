# 텔레그램 데이터 수집 스킬

## 개요

Stock Research ONE의 7단계 플라이휠 시스템 중 **1단계: 데이터 수집**을 담당하는 텔레그램 기반 데이터 수집 모듈입니다.

## 주요 기능

### 🤖 텔레그램 Bot API 연동
- 실시간 메시지 수집
- 채널/그룹 모니터링
- 멀티 채널 동시 관리

### 🔍 키워드 필터링
- 종목코드 기반 필터링
- 투자 관련 키워드 추출
- 맞춤형 필터 설정

### 📊 투자 심리 분석
- 감성 분석 (긍정/부정/중립)
- 긴급성 평가
- 신뢰도 측정
- 투자 심리 리포트 생성

### 📡 실시간 모니터링
- 실시간 데이터 스트리밍
- 이벤트 기반 알림
- 통계 대시보드

### 📋 채널 관리
- 증권사 공식 채널
- 뉴스 미디어 채널
- 커뮤니티 채널
- 섹터별 전문 채널

## 파일 구조

```
data-collection/
├── package.json                    # 의존성 및 스크립트 설정
├── telegram-collector.js           # 텔레그램 Bot API 연동 클래스
├── message-preprocessor.js          # 텍스트 전처리 및 심리 분석
├── channel-manager.js               # 채널 관리 시스템
├── realtime-processor.js            # 실시간 데이터 처리 코디네이터
├── config/
│   ├── telegram-config.js          # 텔레그램 설정
│   └── keywords.js                 # 키워드 설정
├── utils/
│   ├── logger.js                   # 로깅 유틸리티
│   └── helpers.js                  # 헬퍼 함수
└── tests/
    ├── telegram-collector.test.js
    ├── message-preprocessor.test.js
    └── channel-manager.test.js
```

## 사용 방법

### 1. 설치
```bash
npm install
```

### 2. 설정
```bash
# .env 파일 생성
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_API_KEY=your_api_key_here
```

### 3. 실행
```bash
# 개발 모드
npm run dev

# 프로덕션 모드
npm start
```

## API 사용 예제

### 기본 데이터 수집
```javascript
const RealtimeDataProcessor = require('./realtime-processor');

const config = {
    telegram: {
        token: process.env.TELEGRAM_BOT_TOKEN,
        channels: ['@korea_stock_realtime', '@miraeasset_news'],
        keywords: ['삼성전자', 'LG에너지솔루션', '반도체'],
        stocks: ['005930', '373220']
    }
};

const processor = new RealtimeDataProcessor(config);

// 이벤트 리스너 설정
processor.on('messageProcessed', (message) => {
    console.log('New message processed:', message);
});

processor.on('urgentMessage', (message) => {
    console.log('Urgent message detected:', message);
});

// 데이터 수집 시작
await processor.start();
```

### 채널 관리
```javascript
const ChannelManager = require('./channel-manager');

const channelManager = new ChannelManager();

// 새 채널 추가
channelManager.addChannel('@custom_channel', {
    name: '커스텀 채널',
    category: 'community',
    priority: 'high',
    keywords: ['AI', '기술주']
});

// 카테고리별 채널 조회
const brokerChannels = channelManager.getChannelsByCategory('major_brokers');
```

### 메시지 분석
```javascript
const MessagePreprocessor = require('./message-preprocessor');

const preprocessor = new MessagePreprocessor();

const message = "삼성전자 주가 오늘 급등! 목표가 85,000원 상향조정";
const processed = preprocessor.preprocessText(message);

console.log(processed.sentiment);    // { sentiment: 'positive', confidence: 0.8 }
console.log(processed.entities);     // { stocks: [], companies: ['삼성전자'], prices: ['85,000원'] }
console.log(processed.urgency);      // { urgency: 'high', score: 2 }
```

## 채널 카테고리

| 카테고리 | 설명 | 우선순위 | 예시 |
|---------|------|---------|------|
| major_brokers | 주요 증권사 공식 채널 | High | 미래에셋증권, 키움증권 |
| news_media | 경제/증시 뉴스 미디어 | High | 매일경제, 한국경제 |
| stock_communities | 주식 정보 공유 커뮤니티 | Medium | 주식 마스터, 투자 Korea |
| sector_specific | 특정 산업/섹터 전문 | Medium | 반도체 동향, 바이오 주식 |
| international | 해외 증시 및 글로벌 시장 | Low | 월스트리트 한국, 글로벌 마켓 |
| realtime | 실시간 주식 정보 및 시그널 | High | 국내 주식 실시간, 주식 시그널 |

## 감성 분석 기준

### 긍정적 표현
- 상승, 오름, 급등, 대박, 수익, 추천, 매수, 강력매수, 목표가 상향

### 부정적 표현  
- 하락, 내림, 급락, 대패, 손실, 우려, 매도, 강력매도, 목표가 하향

### 중립적 표현
- 보합, 횡보, 관망, 대기, 분석, 예측, 전망, 정보, 공시, 실적

## 통계 기능

### 실시간 통계
- 처리된 메시지 수
- 성공/실패율
- 채널별 활동량
- 감성 분포

### 투자 심리 분석
- 시장 분위기 (bullish/bearish/neutral)
- 주요 언급 종목
- 시간별 활동 패턴
- 채널별 특성 분석

## 설정 옵션

### 텔레그램 설정
```javascript
telegram: {
    token: 'BOT_TOKEN',
    channels: ['@channel1', '@channel2'],
    keywords: ['키워드1', '키워드2'],
    stocks: ['005930', '000660'],
    pollingInterval: 60000
}
```

### 필터 설정
```javascript
filters: {
    minReliability: 70,    // 최소 신뢰도
    minUrgency: 'medium',  // 최소 긴급성
    sentiment: 'positive', // 특정 감성만
    excludeSpam: true      // 스팸 필터링
}
```

## 주의사항

1. **데이터 수집 정책**: 텔레그램 이용약약을 준수하여 데이터 수집
2. **개인정보 보호**: 수집된 데이터에서 개인정보 자동 마스킹 처리
3. **서비스 안정성**: 과도한 API 호출 방지를 위한 레이트 리미팅 적용
4. **데이터 정확성**: 수집된 데이터의 신뢰도 평가 및 필터링 기능 제공

## 확장 기능

- 머신러닝 기반 감성 분석 모델 통합
- 차트 및 시각화 데이터 자동 추출
- 소셜 미디어 연동 확장 (Twitter, YouTube 등)
- 알림 시스템 연동 (Slack, Discord 등)
- 데이터베이스 연동 및 대용량 데이터 처리

## 지원

문제 발생 시 아래 채널로 연락주세요:
- GitHub Issues: 프로젝트 저장소
- 내부 팀 채널: Stock Research ONE 팀