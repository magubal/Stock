from celery import Celery
from ..config import settings

# Celery 설정
celery_app = Celery(
    "stock_research",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.reports", "app.tasks.analysis"]
)

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30분
    task_soft_time_limit=25 * 60,  # 25분
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 스케줄 설정
celery_app.conf.beat_schedule = {
    # 매 6시간마다 리포트 수집
    "collect-reports-every-6-hours": {
        "task": "app.tasks.reports.collect_all_reports",
        "schedule": 3600.0 * 6,  # 6시간
    },
    # 매 1시간마다 뉴스 수집
    "collect-news-every-hour": {
        "task": "app.tasks.news.collect_all_news", 
        "schedule": 3600.0,  # 1시간
    },
    # 매 30분마다 시장 데이터 수집
    "collect-market-data-every-30-minutes": {
        "task": "app.tasks.market.collect_market_data",
        "schedule": 1800.0,  # 30분
    },
    # 매 15분마다 연합뉴스만 수집 (속도 우선)
    "collect-yna-news-every-15-minutes": {
        "task": "app.tasks.news.collect_specific_news_source",
        "schedule": 900.0,  # 15분
        "args": ("yna",)
    },
}