from flask import Blueprint, request, jsonify
from core.logic import MarketingLogic
from db import get_phrases_db
import json
import pandas as pd
import io

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
        sort_by = request.args.get('sort_by', 'conversion_rate')
        limit = request.args.get('limit', 50, type=int)
        
        if not team_id:
            return jsonify({'error': 'team_id는 필수입니다'}), 400
        
        copies = logic.get_team_style(team_id, sort_by, limit)
        
        return jsonify({
            'success': True,
            'copies': copies
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/upload-csv', methods=['POST'])
def upload_csv():
    """CSV 파일 업로드 및 데이터베이스 저장"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not file.filename.lower().endswith(('.csv', '.json')):
            return jsonify({'error': 'CSV 또는 JSON 파일만 업로드 가능합니다.'}), 400
        
        # 파일 타입에 따라 처리
        file_content = file.read().decode('utf-8')
        
        if file.filename.lower().endswith('.json'):
            # JSON 파일 처리
            try:
                data = json.loads(file_content)
                if not isinstance(data, list):
                    return jsonify({'error': 'JSON 파일은 배열 형태여야 합니다.'}), 400
                
                # JSON 데이터를 DataFrame으로 변환
                df = pd.DataFrame(data)
                
                # JSON 구조에 맞게 컬럼 매핑
                if 'contents' in df.columns:
                    # contents 구조에서 title, message 추출
                    df['title'] = df['contents'].apply(lambda x: x.get('title', '') if isinstance(x, dict) else '')
                    df['message'] = df['contents'].apply(lambda x: x.get('message', '') if isinstance(x, dict) else '')
                
                # 팀명을 팀 ID로 매핑
                team_mapping = {
                    '그로스마케팅': 1, '여행서비스TFT': 2, '버티컬마케팅팀': 3, '마케팅운영팀': 4,
                    '스포츠레저팀': 5, '패션팀': 6, '브랜드뷰티팀': 7, '리빙팀': 8, '식품팀': 9,
                    '유아동패션팀': 10, 'L.TOWN팀': 11, '제휴서비스상품팀': 12, 'b tft': 13,
                    '명품잡화팀': 14, '브랜드패션팀': 15, 'B2B팀': 16, '디지털가전팀': 17
                }
                
                # 데이터 변환 및 저장
                success_count = 0
                error_count = 0
                
                for _, row in df.iterrows():
                    try:
                        copy_data = {
                            'team_id': int(row.get('team_id', 1)),
                            'channel': str(row.get('channel', 'APP_PUSH')).upper(),
                            'content_data': json.dumps({
                                'title': str(row.get('title', '')),
                                'message': str(row.get('message', '')),
                            }, ensure_ascii=False),
                            'keywords': None,
                            'target_audience': str(row.get('target_audience', '')),
                            'tone': str(row.get('tone', '')),
                            'reference_text': None,
                            'send_date': str(row.get('send_date', '')),
                            'impression_count': int(row.get('impression_count', 0)),
                            'click_count': int(row.get('click_count', 0)),
                            'ctr': float(row.get('ctr', 0.0)),
                            'conversion_count': int(row.get('conversion_count', 0)),
                            'conversion_rate': float(row.get('conversion_rate', 0.0)),
                            'trend_keywords': None,
                            'is_ai_generated': bool(row.get('is_ai_generated', False)),
                        }
                        
                        if logic.add_marketing_copy(copy_data):
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        continue
                
                return jsonify({
                    'success': True,
                    'count': success_count,
                    'errors': error_count,
                    'message': f'{success_count}개 문구가 성공적으로 추가되었습니다.'
                })
                
            except json.JSONDecodeError:
                return jsonify({'error': 'JSON 파일 형식이 올바르지 않습니다.'}), 400
        
        # CSV 파일 처리 (기존 로직)
        try:
            df = pd.read_csv(io.StringIO(file_content), header=None)
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(io.StringIO(file.read().decode('cp949')), header=None)
            except:
                return jsonify({'error': 'CSV 파일 인코딩을 읽을 수 없습니다.'}), 400
        
        # 팀명을 팀 ID로 매핑하는 딕셔너리
        team_mapping = {
            '그로스마케팅': 1,
            '여행서비스TFT': 2,
            '버티컬마케팅팀': 3,
            '마케팅운영팀': 4,
            '스포츠레저팀': 5,
            '패션팀': 6,
            '브랜드뷰티팀': 7,
            '리빙팀': 8,
            '식품팀': 9,
            '유아동패션팀': 10,
            'L.TOWN팀': 11,
            '제휴서비스상품팀': 12,
            'b tft': 13,
            '명품잡화팀': 14,
            '브랜드패션팀': 15,
            'B2B팀': 16,
            '디지털가전팀': 17
        }
        
        # 데이터 변환 및 저장
        success_count = 0
        error_count = 0
        
        for _, row in df.iterrows():
            try:
                # 컬럼 위치 기반으로 데이터 추출 (4열부터 시작, E열=4)
                # E(4): 발송일자, F(5): 발송시간, G(6): 팀, H(7): 카테고리/오퍼, I(8): 행사명
                # J(9): 메세지(제목), K(10): 메세지(내용), L(11): 발송통수, M(12): 발송통수(성공)
                # N(13): 발송성공률, O(14): 오픈수, P(15): 오픈율(%), Q(16): 구매자수
                # R(17): 구매전환율(%), S(18): 판매매출, T(19): UV, U(20): 타겟, V(21): 비고
                
                # 날짜 변환 함수
                def convert_date(date_str):
                    try:
                        if pd.isna(date_str) or date_str == '':
                            return None
                        date_str = str(date_str).strip()
                        # 8/25(일) -> 20250825 형식으로 변환
                        if '(' in date_str and ')' in date_str:
                            date_part = date_str.split('(')[0]  # 8/25
                            month, day = date_part.split('/')
                            # 2025년으로 가정 (실제로는 현재 연도 사용 가능)
                            return f"2025{month.zfill(2)}{day.zfill(2)}"
                        return None
                    except:
                        return None
                
                team_name = str(row.iloc[6]).strip() if len(row) > 6 else ''
                team_id = team_mapping.get(team_name, 1)  # 기본값은 그로스마케팅팀
                
                title = str(row.iloc[9]).strip() if len(row) > 9 else ''
                message = str(row.iloc[10]).strip() if len(row) > 10 else ''
                target_audience = str(row.iloc[20]).strip() if len(row) > 20 else ''
                send_date = convert_date(row.iloc[3]) if len(row) > 3 else None
                
                # 숫자 데이터 처리 (안전하게 변환)
                def safe_int(value, default=0):
                    try:
                        if pd.isna(value) or value == '':
                            return default
                        return int(float(str(value).replace(',', '')))
                    except:
                        return default
                
                def safe_float(value, default=0.0):
                    try:
                        if pd.isna(value) or value == '':
                            return default
                        return float(str(value).replace(',', '').replace('%', ''))
                    except:
                        return default
                
                impression_count = safe_int(row.iloc[12]) if len(row) > 12 else 0
                click_count = safe_int(row.iloc[14]) if len(row) > 14 else 0
                ctr = safe_float(row.iloc[15]) / 100 if len(row) > 15 else 0.0  # 퍼센트를 소수로 변환
                conversion_count = safe_int(row.iloc[16]) if len(row) > 16 else 0
                conversion_rate = safe_float(row.iloc[17]) / 100 if len(row) > 17 else 0.0  # 퍼센트를 소수로 변환
                
                # 데이터 구성
                copy_data = {
                    'team_id': team_id,
                    'channel': 'APP_PUSH',  # 기본값으로 APP_PUSH 설정
                    'content_data': json.dumps({
                        'title': title,
                        'message': message,
                    }, ensure_ascii=False),
                    'keywords': None,  # 키워드는 None으로 설정
                    'target_audience': target_audience,
                    'tone': '',
                    'reference_text': None,
                    'send_date': send_date,  # 발송 날짜 추가
                    'impression_count': impression_count,
                    'click_count': click_count,
                    'ctr': ctr,
                    'conversion_count': conversion_count,
                    'conversion_rate': conversion_rate,
                    'trend_keywords': None,
                    'is_ai_generated': False,
                }
                
                # 데이터베이스에 저장
                if logic.add_marketing_copy(copy_data):
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                continue
        
        return jsonify({
            'success': True,
            'count': success_count,
            'errors': error_count,
            'message': f'{success_count}개 문구가 성공적으로 추가되었습니다.'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500