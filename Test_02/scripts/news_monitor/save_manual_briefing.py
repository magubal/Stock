"""수동 리서치 기반 시장 브리핑을 DB에 저장."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'f:/PSJ/AntigravityWorkPlace/Stock/Test_02')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.news_article import MarketNarrative

DB_PATH = 'f:/PSJ/AntigravityWorkPlace/Stock/Test_02/backend/stock_research.db'
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)
db = Session()

target_date = '2026-02-19'
row = db.query(MarketNarrative).filter_by(date=target_date).first()

if not row:
    print('ERROR: No row found for', target_date)
    db.close()
    sys.exit(1)

existing_idx = row.index_data or {}

key_issues = [
    {
        "title": "Fed 의사록 - 금리 경로 심각한 내부 분열",
        "summary": "FOMC 의사록에서 금리 동결 자체에는 합의했으나, 향후 방향에서 극명한 의견 대립이 드러남. 다수 위원이 디스인플레이션에 시간이 더 걸릴 것으로 전망. 일부 위원은 금리 인상 가능성까지 언급. 발표 직후 10년물 국채 수익률 3bp 상승하여 4.087% 기록. 상반기 금리 인하 기대감이 급격히 후퇴.",
        "impact": "high",
        "category": "통화정책"
    },
    {
        "title": "Palo Alto Networks -9% 급락 (가이던스 실망)",
        "summary": "PANW Q2 매출 $26억(+15% YoY)으로 시장 예상 상회했으나, Q3 non-GAAP EPS 가이던스 $0.78-0.80이 시장 예상 $0.92를 크게 하회하며 주가 9% 급락. CyberArk 인수($250억) 통합 비용이 마진을 압박. 사이버보안 섹터 전반에 매도세 파급.",
        "impact": "high",
        "category": "실적발표"
    },
    {
        "title": "Nvidia +2% 랠리 지속 - Meta AI 데이터센터 수혜",
        "summary": "Meta가 신규 데이터센터에 수백만 개의 Nvidia 칩 사용 계획 발표. Amazon, Micron도 주요 자산운용사 포지션 확대 소식에 동반 상승. AI 인프라 투자 테마가 시장의 핵심 동력으로 지속. 반도체 섹터 전반 강세.",
        "impact": "high",
        "category": "기술/AI"
    },
    {
        "title": "Walmart Q4 실적 프리뷰 - 시총 $1조 소매기업의 시험대",
        "summary": "월마트 FY2026 Q4 실적 내일(2/19) 발표 예정. 컨센서스 EPS $0.73(+10% YoY). 이커머스 성장, 광고 매출, 멤버십 수익이 실적 견인 전망. 다만 선행 P/E 45.5배로 이미 고평가 논란. 소비자 건전성의 바로미터로 시장 주목.",
        "impact": "medium",
        "category": "실적 프리뷰"
    },
    {
        "title": "에너지/금융 섹터 주도 - 'No-Landing' 내러티브 재부상",
        "summary": "에너지 섹터 +1.72%, Goldman Sachs +2.89%로 금융 강세. 1월 산업생산 +0.7%(예상 +0.2% 대폭 상회)로 리플레이션 트레이드 부활. 제조업 생산도 +0.6%로 약 1년 만에 최대 월간 상승. 반면 유틸리티 -1.64%로 최약세.",
        "impact": "medium",
        "category": "섹터 로테이션"
    }
]

narrative = (
    "미국 증시는 수요일 3일 연속 상승 마감. S&P 500은 +0.56%(6,881.31), 나스닥 +0.78%(22,753.63), 다우 +0.26%(49,662.66)를 기록. "
    "VIX는 -3.30%(19.62)로 하락하며 위험선호 심리 개선을 반영. "
    "장 초반에는 AI/반도체 모멘텀과 예상을 크게 상회한 산업생산 지표가 상승을 견인했으나, "
    "오후 2시 FOMC 의사록 공개 이후 분위기 반전. 의사록은 금리 인상 가능성까지 언급하는 등 "
    "위원들 간 심각한 의견 대립을 드러내며 국채 수익률 상승과 함께 지수 고점 대비 하락을 유발. "
    "Nvidia(+2%)는 Meta의 AI 데이터센터 확장 발표에 랠리를 이어갔고, Goldman Sachs(+2.89%)가 금융 섹터를 주도. "
    "반면 Palo Alto Networks(-9%)는 Q3 가이던스 실망으로 당일 최대 낙폭을 기록. "
    "에너지(+1.72%)와 기초소재(+1.43%)가 산업생산 서프라이즈(+0.7% vs 예상 +0.2%)에 힘입어 강세. "
    "시장은 'No-Landing' 경제 시나리오와 Fed의 매파적 신호 사이에서 줄다리기 중. "
    "향후 Walmart 실적(내일)과 인플레이션 지표(금요일)가 다음 방향성을 결정할 전망."
)

market_summary = (
    "3대 지수 모두 완만한 상승 마감. 오전 낙관론과 오후 경계감이 교차한 장세. "
    "오전 랠리는 AI/반도체 모멘텀이 주도했으며, Nvidia가 Meta의 데이터센터 투자 소식에 +2% 상승. "
    "09:15 발표된 산업생산 지표가 예상(+0.2%)을 대폭 상회한 +0.7%를 기록하며 경기순환주와 리플레이션 트레이드에 불을 지폈다. "
    "그러나 14:00 FOMC 의사록 공개 후 분위기 급변. 복수 위원이 금리 인상 가능성을 시사하면서 지수 고점 대비 하락. "
    "다우는 장중 고점 49,897에서 49,662로, S&P는 6,909에서 6,881로 후퇴. "
    "주요 상승주: Goldman Sachs(+2.89%), Nvidia(+2.03%), Amazon(+1.85%). "
    "주요 하락주: Palo Alto Networks(-9%), AMD(-4%), 3M(-2.23%), Boeing(-1.19%)."
)

sentiment_timeline = [
    {
        "time_period": "09:30-11:00 ET (개장~오전 랠리)",
        "market_move": "S&P +0.4%, NASDAQ +0.6%, DOW +0.3%",
        "sentiment_driver": "프리마켓 AI/반도체 모멘텀 이어짐. Nvidia +2%(Meta 데이터센터). 산업생산 +0.7%(예상 +0.2% 대폭 상회). Goldman Sachs 금융 강세 주도.",
        "sentiment": "risk-on"
    },
    {
        "time_period": "11:00-14:00 ET (장중 보합)",
        "market_move": "지수 장중 고점 부근 횡보. DOW 49,845, S&P 6,909",
        "sentiment_driver": "PANW -9% 급락(가이던스 실망)으로 사이버보안 섹터 압박. Fed 의사록 발표 앞두고 관망세. Walmart 실적 기대감 형성. 에너지 원유 강세 지속.",
        "sentiment": "mixed"
    },
    {
        "time_period": "14:00-15:00 ET (FOMC 의사록 공개)",
        "market_move": "S&P 6,909→6,875 후퇴. 10Y 국채 3bp↑ (4.087%)",
        "sentiment_driver": "FOMC 의사록에서 금리 경로 심각한 분열 노출. 복수 위원 금리 인상 가능성 언급. 상반기 금리 인하 기대감 급격히 후퇴. 국채 수익률 급등. 장중 고점 대비 매도세.",
        "sentiment": "risk-off"
    },
    {
        "time_period": "15:00-16:00 ET (장 마감 반등)",
        "market_move": "S&P 6,881 회복(+0.56%). 전 지수 양봉 마감, 다만 고점 대비 후퇴.",
        "sentiment_driver": "기술주 저가 매수세 유입. 견조한 경제지표(산업생산)가 하방 지지. 투자자들 Walmart Q4 실적(내일)과 금요일 인플레 지표 앞두고 신중한 포지셔닝.",
        "sentiment": "mixed"
    }
]

# 섹터별 변동이유 (한국어 리서치 기반)
sector_reasons = {
    "Energy": "산업생산 +0.7% 서프라이즈, WTI 상승 반영. 리플레이션 트레이드 부활",
    "Basic Materials": "산업생산 호조로 경기순환주 수혜. 금/구리 가격 강세 동반",
    "Technology": "Nvidia +2%(Meta AI 데이터센터), AI 인프라 투자 테마 지속",
    "Consumer Cyclical": "Tesla FSD 구독 전환, Amazon +1.85%. 소비 심리 견조",
    "Financial": "Goldman +2.89% 주도. 'No-Landing' 시나리오로 금리 장기 고수준 기대",
    "Communication Services": "메타 AI 투자 수혜. 광고 시장 회복 기대감",
    "Healthcare": "제약/바이오 혼조. FDA 승인 이슈 소폭 반영",
    "Industrials": "산업생산 +0.7%로 제조업 1년 최대 상승. 인프라 투자 수혜",
    "Consumer Defensive": "Walmart Q4 실적 대기. P/E 45.5배 고평가 우려 상존",
    "Real Estate": "국채 수익률 상승(10Y 4.087%)으로 REIT 매도 압력",
    "Utilities": "금리 인상 가능성 시사로 배당주 매력 저하. 채권 대비 열위",
}

# 기존 sector_impact에서 reason만 업데이트 (deep copy로 변경 감지)
import copy
existing_si = copy.deepcopy(row.sector_impact or [])
if existing_si:
    for s in existing_si:
        name = s.get("sector", "")
        if name in sector_reasons:
            s["reason"] = sector_reasons[name]
    row.sector_impact = existing_si
    print(f"sector_impact 업데이트: {len(existing_si)}건")
    for s in existing_si[:3]:
        print(f"  {s['sector']}: {s['reason'][:50]}...")

# DB 업데이트
row.key_issues = key_issues
row.narrative = narrative
row.sentiment_score = 0.18
row.sentiment_label = "cautious-optimistic"
row.generated_by = "manual-research"
row.model_used = "manual-research"

idx_data = existing_idx.copy() if existing_idx else {}
idx_data["market_summary"] = market_summary
idx_data["sentiment_timeline"] = sentiment_timeline
row.index_data = idx_data

db.commit()
db.close()

print("=== 한글 브리핑 저장 완료 ===")
print(f"핵심이슈: {len(key_issues)}건")
print(f"내러티브: {len(narrative)}자")
print(f"시장요약: {len(market_summary)}자")
print(f"센티먼트 타임라인: {len(sentiment_timeline)}구간")
