from db import get_trends_db, get_phrases_db
from core.llm import LLMService
from core.vector_store import VectorStore
import json

class MarketingLogic:
    def __init__(self):
        self.llm = LLMService()
        self.vector_store = VectorStore()
    
    def get_team_style(self, team_id: str, sort_by: str = 'conversion_rate', limit: int = 50, channel: str = None) -> list:
        """팀별 과거 문구 스타일 가져오기 - 정렬 옵션 및 채널 필터링 지원"""
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        # 정렬 기준 설정
        sort_columns = {
            'latest': 'send_date DESC',
            'conversion_rate': 'conversion_rate DESC, ctr DESC',
            'ctr': 'ctr DESC, conversion_rate DESC',
            'impression_count': 'impression_count DESC',
            'click_count': 'click_count DESC',
            'conversion_count': 'conversion_count DESC'
        }
        
        order_clause = sort_columns.get(sort_by, 'conversion_rate DESC, ctr DESC')
        
        # 채널 필터링 조건 추가
        channel_condition = ""
        if channel:
            channel_condition = f"AND channel = '{channel}'"
        
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
                conversion_count,
                channel
            FROM marketing_copies
            WHERE team_id = ? {channel_condition}
            ORDER BY {order_clause}
            LIMIT ?
        """, (team_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        # 결과를 프론트엔드가 기대하는 형태로 변환
        copies = []
        for row in results:
            content_data = json.loads(row['content_data']) if row['content_data'] else {}
            
            # 채널별로 content_data 구조 다르게 처리
            if row['channel'] == 'RCS':
                # RCS의 경우 button과 message 사용
                title = content_data.get('button', '')
                message = content_data.get('message', '')
                
                # content_data가 비어있으면 keywords나 target_audience 사용
                if not title and not message:
                    title = row['keywords'] or '버튼 텍스트 없음'
                    message = row['target_audience'] or '메시지 내용 없음'
            else:
                # APP_PUSH의 경우 title과 message 사용
                title = content_data.get('title', '')
                message = content_data.get('message', '')
            
            copies.append({
                'copy_id': row['copy_id'],
                'title': title,
                'message': message,
                'keywords': row['keywords'],
                'target_audience': row['target_audience'],
                'tone': row['tone'],
                'send_date': row['send_date'],
                'ctr': row['ctr'],
                'conversion_rate': row['conversion_rate'],
                'impression_count': row['impression_count'],
                'click_count': row['click_count'],
                'conversion_count': row['conversion_count'],
                'channel': row['channel']
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
        discount_type = params.get('discount_type', '')
        appeal_point = params.get('appeal_point', '')
        brand = params.get('brand', '')
        event_name = params.get('event_name', '')
        channel = params.get('channel', 'RCS')
        use_emoji = params.get('use_emoji', 'true').lower() == 'true'
        
        # 1. RAG를 통한 관련 문구 검색
        rag_context = ""
        
        # 검색 쿼리 구성 (키워드와 타겟으로 유사도 계산)
        search_query_parts = []
        
        # 키워드 관련 요소들
        if topic:
            search_query_parts.append(topic)
        if discount_type:
            search_query_parts.append(discount_type)
        if appeal_point:
            search_query_parts.append(appeal_point)
        if brand:
            search_query_parts.append(brand)
        if event_name:
            search_query_parts.append(event_name)
        
        # 타겟 관련 요소들
        if target_audience:
            search_query_parts.append(target_audience)
        
        search_query = " ".join(search_query_parts)
        
        # 벡터 저장소 상태 확인
        try:
            stats = self.vector_store.get_collection_stats()
            print(f"\n📊 벡터 저장소 상태: {stats}")
        except Exception as e:
            print(f"\n❌ 벡터 저장소 상태 확인 실패: {e}")
        
        # 벡터 검색으로 관련 문구 찾기 (채널/팀 필터링 + 키워드/타겟 유사도)
        print(f"\n🔍 벡터 검색 시작 (쿼리: '{search_query}')")
        print(f"📋 필터링 조건: team_id={team_id}, channel={channel}")
        print(f"📋 성과 기준: min_ctr=0.01, min_conversion_rate=0.005, min_similarity=0.6")
        
        try:
            similar_phrases = self.vector_store.search_similar_phrases(
                query=search_query,
                n_results=20,  # 충분한 후보 확보
                team_id=team_id,
                channel=channel,  # 동일한 채널만 검색
                min_ctr=0.01,  # CTR 1% 이상
                min_conversion_rate=0.005,  # 전환율 0.5% 이상
                min_similarity=0.6  # 유사도 60% 이상으로 강화
            )
            print(f"📊 벡터 검색 결과: {len(similar_phrases)}개 문구 발견 (채널: {channel})")
        except Exception as e:
            print(f"❌ 벡터 검색 실패: {e}")
            similar_phrases = []
        
        # unique_phrases 초기화 (프롬프트에서 사용하기 위해)
        unique_phrases = []
        
        if similar_phrases:
            # 중복 제거: 동일한 제목+내용 조합 제거
            unique_phrases = []
            seen_combinations = set()
            
            for phrase in similar_phrases:
                combination = f"{phrase['title']}|{phrase['message']}"
                if combination not in seen_combinations:
                    seen_combinations.add(combination)
                    unique_phrases.append(phrase)
            
            # CTR 순서로 정렬 (높은 CTR 우선)
            unique_phrases.sort(key=lambda x: x['ctr'], reverse=True)
            
            # 상위 3개만 선택
            unique_phrases = unique_phrases[:3]
            
            # 디버깅: 참고 문구 콘솔 출력
            print(f"\n🔍 RAG 검색 결과 (쿼리: '{search_query}')")
            print(f"📊 전체 검색: {len(similar_phrases)}개 → 중복 제거 후: {len(unique_phrases)}개")
            print("=" * 80)
            
            examples = []
            for i, phrase in enumerate(unique_phrases):
                print(f"📝 참고 문구 {i+1}:")
                print(f"   유사도: {phrase['similarity_score']:.3f}")
                print(f"   성과: CTR {phrase['ctr']:.2%}, 전환율 {phrase['conversion_rate']:.2%}")
                print(f"   제목: {phrase['title']}")
                print(f"   내용: {phrase['message']}")
                print(f"   팀: {phrase['team_id']}")
                print("-" * 60)
                
                examples.append(f"- {phrase['title']}: {phrase['message']} (CTR: {phrase['ctr']:.2%}, 전환율: {phrase['conversion_rate']:.2%})")
            
            rag_context = f"\n\n### 성과 좋은 유사 문구 참고:\n" + "\n".join(examples)
            print("=" * 80)
        else:
            print(f"\n⚠️ 벡터 검색 결과가 없습니다. 검색 조건을 완화하거나 데이터를 확인해주세요.")
            print(f"   검색 쿼리: '{search_query}'")
            print(f"   팀 ID: {team_id}")
            print("=" * 80)
        
        # 2. 최신 트렌드 조회
        trends = self.get_recent_trends(5)
        trend_keywords = ", ".join([t['keyword'] for t in trends])
        trend_context = f"\n\n### 최신 트렌드 키워드:\n{trend_keywords}"
        
        # 3. LLM 프롬프트 구성
        discount_context = ""
        if discount_type:
            discount_context = f"\n\n### 할인 유형:\n{discount_type}\n(반드시 이 할인 정보를 문구에 포함해주세요)"
        
        appeal_context = ""
        if appeal_point:
            appeal_context = f"\n\n### 소구 포인트:\n{appeal_point}\n(고객에게 어필할 핵심 포인트를 강조해주세요)"
        
        brand_context = ""
        if brand:
            brand_context = f"\n\n### 브랜드:\n{brand}"
            
        event_context = ""
        if event_name:
            event_context = f"\n\n### 행사명:\n{event_name}"
        
        emoji_instruction = ""
        if use_emoji:
            emoji_instruction = "\n- 이모지를 적절히 사용하여 시각적 효과를 높이세요"
        else:
            emoji_instruction = "\n- 이모지는 사용하지 마세요"
        
        if channel == 'RCS':
            # 실제 참고 문구를 사용한 예시 생성
            example_format = ""
            if unique_phrases and len(unique_phrases) > 0:
                for i, phrase in enumerate(unique_phrases[:3]):  # 상위 3개 사용
                    # 안전한 딕셔너리 접근
                    title = phrase.get('title', '버튼 텍스트')
                    message = phrase.get('message', '메시지 내용')
                    example_format += f"""
{i+1}. 버튼: {title}
메시지: {message}

"""
            else:
                example_format = """
1. 버튼: 지금 바로 구매하기
메시지: 롯데ON 뷰티 세일! ✨

신규고객 30% 할인 혜택

봄신상 뷰티템을 특가로 만나보세요! 💖

2. 버튼: 뷰티 혜택 확인하기
메시지: 롯데ON에서 뷰티 세일 진행중! 🎉

최대 30% 할인에 신규고객 추가 혜택까지!

지금 바로 확인해보세요 ✨

"""

            prompt = f"""
당신은 전문 마케팅 카피라이터입니다. RCS 메시지용 마케팅 문구를 {count}개 생성해주세요.

### 주제:
{topic}{brand_context}{event_context}

### 타겟 고객:
{target_audience}

### 톤앤매너:
{tone}{discount_context}{appeal_context}
{rag_context}

### 참고 텍스트:
{reference_text if reference_text else '없음'}

### RCS 요구사항:
1. 버튼 텍스트는 15자 이내로 간결하고 매력적인 문구 작성
2. 메시지는 100자 이내로 작성하며 문단 단위로 줄바꿈을 두 번씩 하여 가독성 향상
3. 할인 혜택은 숫자와 함께 강조하여 표시 (예: 30% 할인, 최대 50% OFF)
4. 센스있는 후킹 문구로 고객의 관심을 끌어야 함
5. 이모지를 적절히 사용하여 시각적 효과를 높이세요(이모지를 사용하는 경우 브랜드 양옆에 동일한 이모지를 넣어 강조)
6. 타겟 고객의 감성을 자극하는 표현 사용
7. 최신 트렌드를 자연스럽게 반영

### 출력 형식 (정확히 이 형식을 따라주세요):
{example_format}
위와 같은 형식으로 반드시 버튼과 메시지를 모두 포함하여 출력하세요.
메시지는 문단 단위로 줄바꿈을 두 번씩 하여 가독성을 높이고, 할인 혜택을 강조하세요.

"""
        else:  # APP_PUSH
            prompt = f"""
앱푸시 마케팅 문구를 {count}개 생성해주세요.

주제: {topic}{brand_context}{event_context}
타겟: {target_audience}
톤: {tone}{discount_context}{appeal_context}
{rag_context}

각 문구는 반드시 다음 형식으로 출력하세요:
1. 타이틀: [15-20자 제목]
본문: (광고) [40자 이내 내용]{emoji_instruction}
2. 타이틀: [15-20자 제목]
본문: (광고) [40자 이내 내용]{emoji_instruction}

타이틀과 본문을 모두 포함해야 합니다.
"""
        
        # 4. LLM 호출 (Temperature 설정 가능)
        temperature = params.get('temperature', 2.0)  # 기본값 0.6
        result = self.llm.generate_copy(prompt, temperature=temperature)
        
        # 참고 문구 정보 저장 (API 응답용)
        referenced_phrases = []
        if similar_phrases and unique_phrases and len(unique_phrases) > 0:
            for phrase in unique_phrases[:3]:  # 상위 3개만
                referenced_phrases.append({
                    'title': phrase.get('title', ''),
                    'message': phrase.get('message', ''),
                    'similarity_score': phrase.get('similarity_score', 0),
                    'ctr': phrase.get('ctr', 0),
                    'conversion_rate': phrase.get('conversion_rate', 0),
                    'team_id': phrase.get('team_id', ''),
                    'channel': phrase.get('channel', '')
                })
        
        # 5. 결과 파싱
        copies = []
        if channel == 'APP_PUSH':
            # 앱푸시 파싱: "타이틀: [내용]\n본문: [내용]" 형식
            lines = result.split('\n')
            current_copy = {}
            
            for line in lines:
                line = line.strip()

                # "타이틀:" 또는 "5. 타이틀:" 형태 모두 처리
                if '타이틀:' in line:
                    if current_copy and current_copy.get('title'):
                        # 본문이 없어도 타이틀만으로 문구 생성
                        if not current_copy.get('message'):
                            current_copy['message'] = '(광고) ' + current_copy.get('title', '')
                        copies.append(current_copy)

                    # "타이틀:" 이후의 텍스트만 추출
                    title_text = line.split('타이틀:', 1)[1].strip()
                    # 마크다운 형식 제거
                    title_text = title_text.replace('**', '')
                    current_copy = {'title': title_text, 'message': ''}

                elif '본문:' in line:
                    if current_copy:
                        # "본문:" 이후의 텍스트만 추출
                        message_text = line.split('본문:', 1)[1].strip()
                        # 마크다운 형식 제거
                        message_text = message_text.replace('**', '')
                        current_copy['message'] = message_text
            
            # 마지막 문구 추가
            if current_copy and current_copy.get('title'):
                if not current_copy.get('message'):
                    current_copy['message'] = '(광고) ' + current_copy.get('title', '')
                copies.append(current_copy)
                
            # 파싱 실패 시 전체 텍스트를 메시지로 처리
            if not copies:
                for line in result.split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        copy_text = line.split('.', 1)[1].strip()
                        copies.append({'message': copy_text})
        else:
            # RCS 파싱: 줄바꿈 보존 개선
            lines = result.split('\n')
            current_copy = {}
            
            for i, line in enumerate(lines):
                original_line = line  # 원본 줄바꿈 보존
                line = line.strip()
                
                # 번호가 있는 줄인지 확인
                if line and line[0].isdigit():
                    # 기존 문구가 있으면 저장
                    if current_copy and (current_copy.get('button') or current_copy.get('message')):
                        copies.append(current_copy)
                    
                    # 새로운 문구 시작
                    current_copy = {}
                    
                    # "1. " 같은 번호 제거
                    content = line.split('.', 1)[1].strip()
                    
                    # 버튼과 메시지 구분
                    if '버튼:' in content:
                        button_text = content.split('버튼:', 1)[1].strip()
                        button_text = button_text.replace('**', '')
                        current_copy['button'] = button_text
                    elif '메시지:' in content:
                        message_text = content.split('메시지:', 1)[1].strip()
                        message_text = message_text.replace('**', '')
                        current_copy['message'] = message_text
                    else:
                        # 구분자가 없으면 메시지로 처리 (기존 방식)
                        content = content.replace('**', '')
                        current_copy['message'] = content
                
                elif line and current_copy and '메시지:' in line:
                    # 메시지: 로 시작하는 줄 처리
                    message_text = line.split('메시지:', 1)[1].strip()
                    message_text = message_text.replace('**', '')
                    current_copy['message'] = message_text
                
                elif current_copy and 'message' in current_copy:
                    # 메시지 내용의 연속으로 처리 (줄바꿈 보존)
                    if line == '':
                        # 빈 줄이면 원본 줄바꿈 그대로 추가
                        current_copy['message'] += original_line
                    else:
                        # 내용이 있는 줄이면 줄바꿈과 함께 추가
                        current_copy['message'] += '\n' + line.replace('**', '')
            
            # 마지막 문구 저장
            if current_copy and (current_copy.get('button') or current_copy.get('message')):
                copies.append(current_copy)
            
            # 파싱이 실패한 경우 기존 방식으로 fallback
            if not copies:
                for line in result.split('\n'):
                    line = line.strip()
                    if line and line[0].isdigit():
                        copy_text = line.split('.', 1)[1].strip()
                        copy_text = copy_text.replace('**', '')
                        copies.append({'message': copy_text})
        
        # RCS 메시지에 [롯데ON] 자동 추가 (안전한 버전)
        try:
            for copy in copies:
                if isinstance(copy, dict) and 'message' in copy and channel == 'RCS':
                    message = copy['message']
                    if isinstance(message, str):
                        # 이미 [롯데ON]으로 시작하지 않는 경우에만 추가
                        if not message.strip().startswith('[롯데ON]'):
                            copy['message'] = f"[롯데ON]\n{message}"
        except Exception as e:
            print(f"❌ [롯데ON] 추가 오류: {e}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
        
        return {
            'copies': copies[:count],
            'referenced_phrases': referenced_phrases
        }
    
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