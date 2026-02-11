"""
시드 데이터 삽입 스크립트
대시보드 데모용 샘플 데이터 생성
"""
import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta
from app.database import SessionLocal, engine
from app.models import (
    Base, InvestorSentiment, MarketData, PortfolioHolding,
    ResearchReport, FlywheelState
)

def seed():
    db = SessionLocal()
    try:
        now = datetime.now()

        # ── 1. 투자자 심리 (최근 30일) ──
        for i in range(30):
            d = now - timedelta(days=29 - i)
            # 점진적으로 긍정으로 변화하는 패턴
            base = -0.3 + (i / 30) * 0.8
            db.add(InvestorSentiment(
                date=d,
                overall_score=round(base, 2),
                market_heat=round(0.3 + (i / 30) * 0.4, 2),
                fear_greed_index=round(base * 0.8, 2),
                short_term_sentiment=round(base + 0.1, 2),
                long_term_sentiment=round(base - 0.05, 2),
            ))

        # ── 2. 포트폴리오 보유 종목 ──
        holdings = [
            ("005930", "삼성전자", 72000, 100, 30),
            ("000660", "SK하이닉스", 135000, 50, 20),
            ("035720", "카카오", 48000, 80, 45),
            ("051910", "LG화학", 520000, 10, 60),
        ]
        for code, name, price, qty, days_ago in holdings:
            db.add(PortfolioHolding(
                stock_code=code,
                stock_name=name,
                buy_price=price,
                buy_date=now - timedelta(days=days_ago),
                quantity=qty,
                is_active=True,
            ))

        # ── 3. 시장 데이터 (보유 종목별 최근 5일) ──
        market_samples = {
            "005930": {"name": "삼성전자", "prices": [73500, 74200, 73800, 75100, 76000], "rsi": 62, "ma60": 71000},
            "000660": {"name": "SK하이닉스", "prices": [138000, 142000, 140500, 145000, 148000], "rsi": 71, "ma60": 130000},
            "035720": {"name": "카카오", "prices": [49000, 47500, 48200, 49800, 50500], "rsi": 55, "ma60": 46000},
            "051910": {"name": "LG화학", "prices": [530000, 525000, 535000, 540000, 545000], "rsi": 58, "ma60": 510000},
        }
        for code, info in market_samples.items():
            for j, price in enumerate(info["prices"]):
                db.add(MarketData(
                    stock_code=code,
                    stock_name=info["name"],
                    date=now - timedelta(days=4 - j),
                    open_price=price * 0.99,
                    high_price=price * 1.01,
                    low_price=price * 0.98,
                    close_price=price,
                    volume=1000000 + j * 50000,
                    moving_avg_5=price * 0.995,
                    moving_avg_20=price * 0.98,
                    moving_avg_60=info["ma60"],
                    rsi=info["rsi"] + j - 2,
                ))

        # ── 4. 증권사 리포트 ──
        reports = [
            ("삼성전자 4Q 실적 서프라이즈 전망", "반도체 회복세가 뚜렷하며 4분기 영업이익이 시장 컨센서스를 상회할 것으로 예상됩니다. HBM 수요 증가와 DRAM 가격 반등이 실적 개선의 핵심 동인입니다.",
             "미래에셋증권", "김분석", 88000, "buy", "005930", "삼성전자", 3),
            ("SK하이닉스 AI 수혜 지속", "HBM3E 양산이 본격화되며 AI 반도체 시장 점유율을 확대하고 있습니다. 2026년 실적 가이던스 상향이 예상됩니다.",
             "한국투자증권", "이투자", 180000, "buy", "000660", "SK하이닉스", 5),
            ("카카오 플랫폼 경쟁력 재평가", "카카오톡 기반 커머스·핀테크 성장이 재가속화 조짐을 보이고 있으나, 콘텐츠 사업 불확실성은 상존합니다.",
             "NH투자증권", "박리서치", 55000, "hold", "035720", "카카오", 7),
            ("LG화학 배터리 분리 효과", "LG에너지솔루션 지분가치 재평가와 석유화학 업황 회복이 동시에 진행 중입니다.",
             "KB증권", "정애널", 620000, "buy", "051910", "LG화학", 2),
            ("2026년 반도체 산업 전망", "AI 인프라 투자 확대로 메모리 반도체 슈퍼사이클이 도래할 가능성이 높습니다. 관련 대장주 비중 확대를 권고합니다.",
             "삼성증권", "최전략", None, "buy", None, None, 1),
            ("국내 소비 트렌드 변화", "MZ세대의 소비 패턴 변화가 플랫폼 기업에 유리한 환경을 조성하고 있습니다.",
             "대신증권", "한매크로", None, "hold", None, None, 10),
        ]
        for title, content, brok, author, target, rec, stock_code, stock_name, days in [
            (*r[:6], r[6], r[7], r[8]) for r in reports
        ]:
            db.add(ResearchReport(
                title=title,
                content=content,
                brokerage=brok,
                author=author,
                target_price=target,
                recommendation=rec,
                published_at=now - timedelta(days=days),
                stock_code=stock_code,
                stock_name=stock_name,
            ))

        # ── 5. 플라이휠 상태 (사이클 1) ──
        steps = [
            (1, "데이터 수집", "completed", now - timedelta(hours=6), now - timedelta(hours=5)),
            (2, "맥락 분석", "completed", now - timedelta(hours=5), now - timedelta(hours=4)),
            (3, "중요도 평가", "completed", now - timedelta(hours=4), now - timedelta(hours=3)),
            (4, "시나리오 작성", "current", now - timedelta(hours=3), None),
            (5, "실질 확인", "pending", None, None),
            (6, "투자 결정", "pending", None, None),
            (7, "사후 검증", "pending", None, None),
        ]
        for step_num, name, status, started, completed in steps:
            db.add(FlywheelState(
                cycle_number=1,
                current_step=step_num,
                step_name=name,
                status=status,
                started_at=started,
                completed_at=completed,
                notes=f"{name} 단계" if status == "completed" else None,
            ))

        db.commit()
        print(f"시드 데이터 삽입 완료!")
        print(f"  - 투자자 심리: 30일치")
        print(f"  - 포트폴리오: {len(holdings)}종목")
        print(f"  - 시장 데이터: {len(market_samples)}종목 × 5일")
        print(f"  - 리포트: {len(reports)}건")
        print(f"  - 플라이휠: 7단계 (4단계 진행 중)")

    except Exception as e:
        db.rollback()
        print(f"에러: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
