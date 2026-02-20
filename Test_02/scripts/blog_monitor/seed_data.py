#!/usr/bin/env python3
"""
[SEED] blog-investor-digest DEMO 시드 데이터.
실제 데이터가 없을 때 대시보드 테스트용으로 사용.
source="DEMO" 규칙 준수.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = ROOT / "backend" / "stock_research.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)

from app.models.blog_post import BlogPost, BlogSummary

KST = timezone(timedelta(hours=9))

DEMO_POSTS = [
    {
        "blogger": "daybyday",
        "title": "[DEMO] 미국 증시 3대 지수 동반 상승 마감",
        "link": "https://blog.naver.com/demo/post001",
        "text_content": "[DEMO] 나스닥 +1.2% 상승, S&P500 +0.8% 상승으로 마감. 빅테크 실적 호조에 따른 매수세 유입. 엔비디아 +3.5%, 애플 +1.8% 강세.",
    },
    {
        "blogger": "daybyday",
        "title": "[DEMO] 특징주: AI 반도체 관련주 급등",
        "link": "https://blog.naver.com/demo/post002",
        "text_content": "[DEMO] 엔비디아 신제품 발표 예고에 AI 관련주 전반 강세. SK하이닉스 +4.2%, 삼성전자 +2.1% 동반 상승. HBM 수요 확대 전망이 호재로 작용.",
    },
    {
        "blogger": "라틴카페",
        "title": "[DEMO] 시장 관전 포인트: FOMC 의사록 분석",
        "link": "https://blog.naver.com/demo/post003",
        "text_content": "[DEMO] 연준 의사록 공개. 인플레이션 둔화 확인되나 금리 인하 시점은 불투명. 점도표상 연내 1회 인하 전망. 채권시장은 이미 2회 인하를 반영 중이라 괴리 존재.",
    },
    {
        "blogger": "유수암바람",
        "title": "[DEMO] 매매 일지: 포트폴리오 리밸런싱",
        "link": "https://blog.naver.com/demo/post004",
        "text_content": "[DEMO] 반도체 비중 축소(40%→30%), 방산주 비중 확대(10%→20%). 지정학 리스크 대비 포지션 조정. 한화에어로스페이스 신규 매수.",
    },
]

DEMO_SUMMARIES = [
    {
        "post_link": "https://blog.naver.com/demo/post001",
        "summary": "[DEMO] 미국 3대 지수가 빅테크 실적 호조에 동반 상승. 엔비디아와 애플이 상승을 주도했으며, 기술주 중심의 매수세가 나타남.",
        "viewpoint": "[DEMO] 빅테크 실적이 시장 전체 심리를 끌어올리는 국면. 단기적으로는 추가 상승 여력이 있으나 밸류에이션 부담도 존재.",
        "implications": "[DEMO] AI 반도체 중심의 상승 추세가 지속되고 있어, 국내 반도체 수출주에 간접적 호재. 다만 고점 부담 고려하여 비중 조절 필요.",
        "ai_model": "DEMO",
    },
    {
        "post_link": "https://blog.naver.com/demo/post003",
        "summary": "[DEMO] 연준 의사록에서 인플레이션 둔화는 확인되었으나, 금리 인하 시점에 대한 위원들의 의견이 나뉘어 있음이 확인됨.",
        "viewpoint": "[DEMO] 시장이 기대하는 금리 인하 횟수와 연준의 시그널 간 괴리가 존재. 이 괴리가 해소되는 과정에서 변동성 확대 가능.",
        "implications": "[DEMO] 채권 듀레이션 관리에 주의 필요. 주식시장은 금리 민감도가 높은 성장주보다 실적 기반 가치주에 비중을 둘 시점.",
        "ai_model": "DEMO",
    },
]


def seed():
    session = Session()
    inserted_posts = 0
    inserted_summaries = 0

    today = datetime.now(KST)

    for p in DEMO_POSTS:
        existing = session.query(BlogPost).filter(BlogPost.link == p["link"]).first()
        if existing:
            continue

        post = BlogPost(
            blogger=p["blogger"],
            title=p["title"],
            link=p["link"],
            text_content=p["text_content"],
            image_path=None,
            image_size_kb=0,
            collected_at=today,
            source="DEMO",
        )
        session.add(post)
        session.flush()
        inserted_posts += 1

    session.commit()

    for s in DEMO_SUMMARIES:
        post = session.query(BlogPost).filter(BlogPost.link == s["post_link"]).first()
        if not post:
            continue

        existing = session.query(BlogSummary).filter(
            BlogSummary.post_id == post.id,
            BlogSummary.ai_model == "DEMO",
        ).first()
        if existing:
            continue

        summary = BlogSummary(
            post_id=post.id,
            summary=s["summary"],
            viewpoint=s["viewpoint"],
            implications=s["implications"],
            is_edited=False,
            ai_model=s["ai_model"],
        )
        session.add(summary)
        inserted_summaries += 1

    session.commit()
    session.close()

    print(f"[SEED] Blog DEMO: {inserted_posts} posts, {inserted_summaries} summaries inserted")


if __name__ == "__main__":
    print("[SEED] blog-investor-digest DEMO data")
    seed()
