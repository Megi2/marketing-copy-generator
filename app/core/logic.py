from db import get_trends_db, get_phrases_db
from core.llm import LLMService
import json

class MarketingLogic:
    def __init__(self):
        self.llm = LLMService()
    
    def get_team_style(self, team_id: str) -> list:
        """팀별 과거 문구 스타일 가져오기"""
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        # 성과가 좋았던 문구 우선 조회
        cursor.execute("""
            SELECT copy_text, tone, target_audience, performance_score
            FROM marketing_phrases
            WHERE team_id = ?
            ORDER BY performance_score DESC
            LIMIT 10
        """, (team_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
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
        """생성된 문구를 DB에 저장"""
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO marketing_phrases 
            (team_id, copy_text, target_audience, tone, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            team_id or 'general',
            copy_text,
            params.get('target_audience'),
            params.get('tone'),
            json.dumps(params)
        ))
        
        conn.commit()
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