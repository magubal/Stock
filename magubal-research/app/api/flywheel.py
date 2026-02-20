"""
Flywheel API Endpoints
"""

from flask import Blueprint, jsonify, request, current_app
from ..services import DecisionService, ResearchService

flywheel_bp = Blueprint('flywheel', __name__)


@flywheel_bp.route('/flywheel/stages', methods=['GET'])
def get_flywheel_stages():
    """플라이휠 7단계 정보"""
    config = current_app.config
    
    return jsonify({
        'success': True,
        'stages': config.get('FLYWHEEL_STAGES', []),
        'philosophy': config.get('INVESTMENT_PHILOSOPHY', {}),
        'currentStage': 1
    })


@flywheel_bp.route('/decision/scenario', methods=['POST'])
def create_scenario():
    """시나리오 생성 (Skill: decision, Workflow: /04-decision-scenario)"""
    data = request.get_json()
    
    if not data or 'symbol' not in data or 'currentPrice' not in data:
        return jsonify({'success': False, 'error': 'symbol and currentPrice are required'}), 400
    
    config = current_app.config
    decision_service = DecisionService(config)
    
    scenarios = decision_service.create_scenario(
        data['symbol'],
        data['currentPrice'],
        data.get('analysis')
    )
    
    return jsonify({
        'success': True,
        'symbol': data['symbol'],
        'scenarios': scenarios
    })


@flywheel_bp.route('/decision/risk/<symbol>', methods=['GET'])
def evaluate_risk(symbol):
    """리스크 평가 (Skill: decision)"""
    is_holder = request.args.get('holder', 'false').lower() == 'true'
    
    config = current_app.config
    decision_service = DecisionService(config)
    
    result = decision_service.evaluate_risk(symbol.upper(), is_holder)
    
    return jsonify({
        'success': True,
        'result': result
    })


@flywheel_bp.route('/decision/execution/<symbol>', methods=['GET'])
def check_execution(symbol):
    """실질확인 (Skill: decision, Workflow: /05-execution-check)"""
    config = current_app.config
    decision_service = DecisionService(config)
    
    result = decision_service.check_execution(symbol.upper())
    
    return jsonify({
        'success': True,
        'result': result
    })


@flywheel_bp.route('/research/company/<symbol>', methods=['GET'])
def evaluate_company(symbol):
    """기업 분석 (Skill: research)"""
    config = current_app.config
    research_service = ResearchService(config)
    
    result = research_service.evaluate_company(symbol.upper())
    
    return jsonify({
        'success': True,
        'result': result
    })


@flywheel_bp.route('/research/trend', methods=['POST'])
def research_trend():
    """트렌드 리서치 (Skill: research, Workflow: /07-trend-research)"""
    data = request.get_json()
    
    if not data or 'topic' not in data:
        return jsonify({'success': False, 'error': 'topic is required'}), 400
    
    config = current_app.config
    research_service = ResearchService(config)
    
    result = research_service.research_trend(data['topic'])
    
    return jsonify({
        'success': True,
        'result': result
    })


@flywheel_bp.route('/research/review/<symbol>', methods=['GET'])
def create_review(symbol):
    """복기 템플릿 (Skill: research, Workflow: /06-review-improvement)"""
    config = current_app.config
    research_service = ResearchService(config)
    
    result = research_service.create_review(symbol.upper())
    
    return jsonify({
        'success': True,
        'result': result
    })
