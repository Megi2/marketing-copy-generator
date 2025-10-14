from db import get_trends_db, get_phrases_db
from core.llm import LLMService
import json

class MarketingLogic:
    def __init__(self):
        self.llm = LLMService()
    
    def get_team_style(self, team_id: str, sort_by: str = 'conversion_rate', limit: int = 50) -> list:
        """팀별 과거 문구 스타일 가져오기 - 정렬 옵션 지원"""
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        # 정렬 기준 설정
        sort_columns = {
            'latest': 'created_at DESC',
            'conversion_rate': 'conversion_rate DESC, ctr DESC',
            'ctr': 'ctr DESC, conversion_rate DESC',
            'impression_count': 'impression_count DESC',
            'click_count': 'click_count DESC',
            'conversion_count': 'conversion_count DESC'
        }
        
        order_clause = sort_columns.get(sort_by, 'conversion_rate DESC, ctr DESC')
        
        # 성과가 좋았던 문구 우선 조회
        cursor.execute(f"""
            SELECT 
                copy_id,
                content_data, 
                keywords,
                target_audience, 
                tone,
                send_date,
                ctr, 
                conversion_rate,
                impression_count,
                click_count,
                conversion_count
            FROM marketing_copies
            WHERE team_id = ?
            ORDER BY {order_clause}
            LIMIT ?
        """, (team_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        # 결과를 프론트엔드가 기대하는 형태로 변환
        copies = []
        for row in results:
            content_data = json.loads(row['content_data']) if row['content_data'] else {}
            copies.append({
                'copy_id': row['copy_id'],
                'title': content_data.get('title', ''),
                'message': content_data.get('message', ''),
                'keywords': row['keywords'],
                'target_audience': row['target_audience'],
                'tone': row['tone'],
                'send_date': row['send_date'],
                'ctr': row['ctr'],
                'conversion_rate': row['conversion_rate'],
                'impression_count': row['impression_count'],
                'click_count': row['click_count'],
                'conversion_count': row['conversion_count']
            })
        
        return copies
    
    def get_recent_trends(self, limit: int = 10) -> list:
        """최신 트렌드 가져오기"""
        conn = get_trends_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT keyword, category, mention_count, trend_score
            FROM trends
            WHERE is_valid = 1
            ORDER BY collected_at DESC, trend_score DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def generate_marketing_copy(self, params: dict) -> list:
        """
        마케팅 문구 생성 (계획서의 핵심 기능)
        
        params: {
            'topic': '필수',
            'team_id': '선택',
            'target_audience': '선택',
            'reference_text': '선택',
            'tone': '선택',
            'count': 5 (기본값)
        }
        """
        topic = params.get('topic')
        team_id = params.get('team_id')
        target_audience = params.get('target_audience', '일반 대중')
        tone = params.get('tone', '전문적이고 친근한')
        count = params.get('count', 5)
        reference_text = params.get('reference_text', '')
        
        # 1. 팀 스타일 조회 (team_id가 있는 경우)
        team_style_context = ""
        if team_id:
            team_copies = self.get_team_style(team_id)
            if team_copies:
                examples = "\n".join([f"- {c['copy_text']}" for c in team_copies[:3]])
                team_style_context = f"\n\n### 팀 스타일 참고:\n{examples}"
        
        # 2. 최신 트렌드 조회
        trends = self.get_recent_trends(5)
        trend_keywords = ", ".join([t['keyword'] for t in trends])
        trend_context = f"\n\n### 최신 트렌드 키워드:\n{trend_keywords}"
        
        # 3. LLM 프롬프트 구성
        prompt = f"""
당신은 전문 마케팅 카피라이터입니다. 다음 조건에 맞는 마케팅 문구를 {count}개 생성해주세요.

### 주제:
{topic}

### 타겟 고객:
{target_audience}

### 톤앤매너:
{tone}
{team_style_context}
{trend_context}

### 참고 텍스트:
{reference_text if reference_text else '없음'}

### 요구사항:
1. 각 문구는 한 줄로 작성 (최대 50자)
2. 타겟 고객의 감성을 자극하는 표현 사용
3. 최신 트렌드를 자연스럽게 반영
4. 클릭을 유도하는 강력한 CTA 포함

### 출력 형식:
1. [문구1]
2. [문구2]
...
"""
        
        # 4. LLM 호출
        result = self.llm.generate_copy(prompt)
        
        # 5. 결과 파싱
        copies = []
        for line in result.split('\n'):
            line = line.strip()
            if line and line[0].isdigit():
                # "1. " 같은 번호 제거
                copy_text = line.split('.', 1)[1].strip()
                copies.append(copy_text)
        
        return copies[:count]
    
    def save_generated_copy(self, team_id: str, copy_text: str, params: dict):
        """생성된 문구를 DB에 저장 (중복 방지) - add_marketing_copy 함수 사용"""
        # add_marketing_copy 함수와 일관성을 위해 데이터 구조 변환
        copy_data = {
            'team_id': team_id or 1,
            'channel': params.get('channel', 'APP_PUSH'),
            'copy_text': copy_text,
            'title': params.get('title', copy_text),
            'message': params.get('message', copy_text),
            'keywords': params.get('keywords'),
            'target_audience': params.get('target_audience'),
            'tone': params.get('tone'),
            'reference_text': params.get('reference_text'),
            'is_ai_generated': True,
            'created_by': 'ai_generator',
            'metadata': {
                'generated_at': params.get('generated_at'),
                'ai_model': params.get('ai_model', 'gemini-pro')
            }
        }
        
        # add_marketing_copy 함수 사용
        return self.add_marketing_copy(copy_data)
    
    def add_marketing_copy(self, copy_data: dict) -> bool:
        """
        마케팅 문구를 데이터베이스에 추가하는 새로운 함수
        
        copy_data: {
            'team_id': int,
            'channel': str ('APP_PUSH' or 'RCS'),
            'copy_text': str,  # 기본 텍스트 (fallback용)
            
            # RCS 채널 전용 필드:
            'button_name': str (optional, default '자세히 보기'),
            
            # APP_PUSH 채널 전용 필드:
            'title': str (optional, copy_text와 동일시),
            'message': str (optional, copy_text와 동일시),
            
            # 공통 필드:
            'keywords': str (optional),
            'target_audience': str (optional),
            'tone': str (optional),
            'reference_text': str (optional),
            'impression_count': int (optional, default 0),
            'click_count': int (optional, default 0),
            'ctr': float (optional, default 0.0),
            'conversion_count': int (optional, default 0),
            'conversion_rate': float (optional, default 0.0),
            'trend_keywords': str (optional),
            'is_ai_generated': bool (optional, default False),
            'created_by': str (optional, default 'manual'),
            'metadata': dict (optional, default {})
        }
        
        content_data 구조:
        - RCS: {'content': str, 'button_name': str, 'created_by': str, 'metadata': dict}
        - APP_PUSH: {'title': str, 'message': str, 'created_by': str, 'metadata': dict}
        """
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        try:
            # 필수 필드 검증
            if not copy_data.get('team_id') or not copy_data.get('channel'):
                raise ValueError("team_id, channel은 필수 필드입니다.")
            
            # 채널 유효성 검증
            if copy_data.get('channel') not in ['APP_PUSH', 'RCS']:
                raise ValueError("channel은 'APP_PUSH' 또는 'RCS'여야 합니다.")
            # 데이터 삽입
            cursor.execute("""
                INSERT INTO marketing_copies 
                (team_id, channel, content_data, keywords, target_audience, tone, 
                 reference_text, send_date, impression_count, click_count, ctr, conversion_count, 
                 conversion_rate, trend_keywords, is_ai_generated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                copy_data.get('team_id'),
                copy_data.get('channel'),
                copy_data.get('content_data'),
                copy_data.get('keywords'),
                copy_data.get('target_audience'),
                copy_data.get('tone'),
                copy_data.get('reference_text'),
                copy_data.get('send_date'),
                copy_data.get('impression_count', 0),
                copy_data.get('click_count', 0),
                copy_data.get('ctr', 0.0),
                copy_data.get('conversion_count', 0),
                copy_data.get('conversion_rate', 0.0),
                copy_data.get('trend_keywords'),
                copy_data.get('is_ai_generated', False)
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"Error adding marketing copy: {e}")
            return False
        finally:
            conn.close()
    
    def search_trends(self, keyword: str) -> dict:
        """
        Google Search API를 사용한 트렌드 검색
        (2주차 개발 예정 - 현재는 스텁)
        """
        # TODO: Google Search API 연동
        return {
            'keyword': keyword,
            'results': []
        }
    
    def archive_trends(self, trend_data: list):
        """
        트렌드 데이터 저장 (중복 제거 및 정규화)
        """
        conn = get_trends_db()
        cursor = conn.cursor()
        
        for trend in trend_data:
            # 중복 체크
            cursor.execute("""
                SELECT id FROM trends 
                WHERE keyword = ? AND DATE(collected_at) = DATE('now')
            """, (trend['keyword'],))
            
            if cursor.fetchone():
                # 오늘 이미 저장된 트렌드면 업데이트
                cursor.execute("""
                    UPDATE trends 
                    SET mention_count = ?, trend_score = ?
                    WHERE keyword = ? AND DATE(collected_at) = DATE('now')
                """, (trend['mention_count'], trend['trend_score'], trend['keyword']))
            else:
                # 새로운 트렌드 저장
                cursor.execute("""
                    INSERT INTO trends (keyword, category, mention_count, trend_score, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    trend['keyword'],
                    trend.get('category', 'general'),
                    trend.get('mention_count', 0),
                    trend.get('trend_score', 0),
                    trend.get('source', 'google')
                ))
        
        conn.commit()
        conn.close()