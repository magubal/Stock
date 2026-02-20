"""
News API Endpoints
"""

from flask import Blueprint, jsonify, request, current_app
from ..services import DataCollectionService, AnalysisService

news_bp = Blueprint('news', __name__)

# 종목명 매핑
STOCK_CODE_TO_NAME = {
    '005930': '삼성전자',
    '000660': 'SK하이닉스',
    '373220': 'LG에너지솔루션',
    '207940': '삼성바이오로직스',
    '005380': '현대차',
    '000270': '기아',
    '068270': '셀트리온',
    '006400': '삼성SDI',
    '105560': 'KB금융',
    '055550': '신한지주',
    '035420': '네이버',
    '035720': '카카오',
    '005490': '포스코홀딩스',
    '012330': '현대모비스',
    '051910': 'LG화학',
}


@news_bp.route('/data/news/<symbol>', methods=['GET'])
def get_stock_news(symbol):
    """종목 관련 뉴스 수집 (Skill: data-collection)"""
    symbol = symbol.upper()
    stock_name = STOCK_CODE_TO_NAME.get(symbol, symbol)
    
    config = current_app.config
    data_service = DataCollectionService(config)
    analysis_service = AnalysisService(config)
    
    # 뉴스 수집
    news_items = data_service.fetch_google_news(
        stock_name + " 주식",
        max_count=config.get('NEWS_MAX_COUNT', 8)
    )
    
    # 중요도 평가 추가
    for item in news_items:
        importance = analysis_service.evaluate_importance(
            item['title'],
            item.get('description', ''),
            item.get('source', '')
        )
        item['importance'] = importance
    
    # 중요도 순 정렬
    news_items.sort(key=lambda x: x.get('importance', {}).get('score', 0), reverse=True)
    
    return jsonify({
        'success': True,
        'symbol': symbol,
        'stockName': stock_name,
        'news': news_items,
        'count': len(news_items)
    })


@news_bp.route('/data/market-issues', methods=['GET'])
def get_market_issues():
    """시장 핵심 이슈 수집 (Skill: data-collection)"""
    config = current_app.config
    data_service = DataCollectionService(config)
    
    # KITA 무역뉴스
    kita_news = data_service.fetch_kita_news(max_count=10)
    
    # 증시 이슈
    stock_issues = data_service.fetch_google_news("코스피 증시", max_count=4, max_days=3)
    
    return jsonify({
        'success': True,
        'issues': kita_news,
        'risks': stock_issues,
        'timestamp': current_app.config.get('timestamp', None)
    })


@news_bp.route('/analysis/importance', methods=['POST'])
def analyze_importance():
    """중요도 평가 (Skill: analysis)"""
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({'success': False, 'error': 'title is required'}), 400
    
    config = current_app.config
    analysis_service = AnalysisService(config)
    
    result = analysis_service.evaluate_importance(
        data['title'],
        data.get('description', ''),
        data.get('source', '')
    )
    
    return jsonify({
        'success': True,
        'result': result
    })


@news_bp.route('/analysis/context', methods=['POST'])
def analyze_context():
    """맥락 분석 (Skill: analysis, Workflow: /02-context-analysis)"""
    data = request.get_json()
    
    if not data or 'issue' not in data:
        return jsonify({'success': False, 'error': 'issue is required'}), 400
    
    config = current_app.config
    analysis_service = AnalysisService(config)
    
    result = analysis_service.analyze_context(
        data['issue'],
        data.get('investor_type', 'medium_term')
    )
    
    return jsonify({
        'success': True,
        'result': result
    })
