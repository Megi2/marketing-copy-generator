from flask import Blueprint, request, jsonify
from core.logic import MarketingLogic

api_bp = Blueprint('api', __name__, url_prefix='/api')
logic = MarketingLogic()

@api_bp.route('/generate', methods=['POST'])
def generate_copy():
    """마케팅 문구 생성 API"""
    try:
        data = request.get_json()
        
        # 필수 파라미터 검증
        if not data.get('topic'):
            return jsonify({'error': '주제(topic)는 필수입니다'}), 400
        
        # 문구 생성
        copies = logic.generate_marketing_copy(data)
        
        # 생성된 문구 DB 저장 (선택사항)
        team_id = data.get('team_id')
        if team_id:
            for copy in copies:
                logic.save_generated_copy(team_id, copy, data)
        
        return jsonify({
            'success': True,
            'copies': copies,
            'count': len(copies)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/trends', methods=['GET'])
def get_trends():
    """최신 트렌드 조회 API"""
    try:
        limit = request.args.get('limit', 10, type=int)
        trends = logic.get_recent_trends(limit)
        
        return jsonify({
            'success': True,
            'trends': trends
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/archive', methods=['GET'])
def get_archive():
    """문구 아카이브 조회 API"""
    try:
        team_id = request.args.get('team_id')
        
        if not team_id:
            return jsonify({'error': 'team_id는 필수입니다'}), 400
        
        copies = logic.get_team_style(team_id)
        
        return jsonify({
            'success': True,
            'copies': copies
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500