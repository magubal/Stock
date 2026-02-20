"""
Configuration Management
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    """Base Configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'magubal-research-secret')
    DATABASE_PATH = os.path.join(BASE_DIR, 'research_data.db')
    
    # External API Settings
    YAHOO_TIMEOUT = 10
    NEWS_MAX_DAYS = 3
    NEWS_MAX_COUNT = 8
    
    # Flywheel Stages (from investment-philosophy.md)
    FLYWHEEL_STAGES = [
        {"id": 1, "name": "데이터 수집", "icon": "📊", "workflow": "/01-data-collection", "skill": "data-collection"},
        {"id": 2, "name": "맥락/영향 분석", "icon": "🔍", "workflow": "/02-context-analysis", "skill": "analysis"},
        {"id": 3, "name": "중요도 파악", "icon": "⚖️", "workflow": "/03-importance-evaluation", "skill": "analysis"},
        {"id": 4, "name": "의사결정 시나리오", "icon": "🎯", "workflow": "/04-decision-scenario", "skill": "decision"},
        {"id": 5, "name": "실질확인", "icon": "✅", "workflow": "/05-execution-check", "skill": "decision"},
        {"id": 6, "name": "복기/개선", "icon": "📝", "workflow": "/06-review-improvement", "skill": "research"},
        {"id": 7, "name": "트렌드 정리", "icon": "📈", "workflow": "/07-trend-research", "skill": "research"},
    ]
    
    # Philosophy Core
    INVESTMENT_PHILOSOPHY = {
        "core": "시장방향성 및 주고객 심리이해 & 행동 가능성 및 영향력 예측",
        "customer": "중장기 투자자들",
        "strategy": "선별 매수 → 보유 → 고객(중장기 투자자)에게 매도"
    }


class DevelopmentConfig(Config):
    """Development Configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production Configuration"""
    DEBUG = False
