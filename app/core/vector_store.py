import chromadb
from chromadb.config import Settings
import json
import os
from typing import List, Dict, Any
from db import get_phrases_db

class VectorStore:
    def __init__(self):
        """벡터 저장소 초기화"""
        # ChromaDB 클라이언트 초기화 (절대 경로 사용)
        chroma_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 컬렉션 초기화 (ChromaDB 기본 임베딩 사용)
        self.collection = self.client.get_or_create_collection(
            name="marketing_phrases",
            metadata={"hnsw:space": "cosine"}
        )
    
    def _replace_placeholders(self, text: str) -> str:
        """플레이스홀더를 실제 키워드로 치환"""
        if not text:
            return text
        
        # 플레이스홀더 치환 규칙
        replacements = {
            '${키워드}': '상품',
            '{키워드}': '상품',
            '{브랜드명}': '브랜드',
            '${브랜드명}': '브랜드',
            '{상품명}': '상품',
            '${상품명}': '상품',
            '{할인율}': '30%',
            '${할인율}': '30%',
            '{금액}': '10만원',
            '${금액}': '10만원',
            '{쿠폰명}': '특가쿠폰',
            '${쿠폰명}': '특가쿠폰',
            '{이벤트명}': '특가이벤트',
            '${이벤트명}': '특가이벤트'
        }
        
        result = text
        for placeholder, replacement in replacements.items():
            result = result.replace(placeholder, replacement)
        
        return result
    
    def add_phrases(self, phrases: List[Dict[str, Any]]) -> None:
        """문구들을 벡터 저장소에 추가"""
        if not phrases:
            return
        
        # 문서와 메타데이터 준비
        documents = []
        metadatas = []
        ids = []
        
        for phrase in phrases:
            # 문구 내용으로 유사도 계산용 텍스트 생성
            title = phrase.get('title', '')
            message = phrase.get('message', '')
            
            # 플레이스홀더 치환
            title = self._replace_placeholders(title)
            message = self._replace_placeholders(message)
            
            text = f"{title} {message}".strip()
            
            if not text:
                continue
            
            # 메타데이터 준비 (None 값 제거)
            metadata = {
                'copy_id': phrase.get('copy_id') or '',
                'team_id': phrase.get('team_id') or '',
                'channel': phrase.get('channel') or '',
                'target_audience': phrase.get('target_audience') or '',
                'tone': phrase.get('tone') or '',
                'ctr': float(phrase.get('ctr', 0)) if phrase.get('ctr') is not None else 0.0,
                'conversion_rate': float(phrase.get('conversion_rate', 0)) if phrase.get('conversion_rate') is not None else 0.0,
                'impression_count': int(phrase.get('impression_count', 0)) if phrase.get('impression_count') is not None else 0,
                'click_count': int(phrase.get('click_count', 0)) if phrase.get('click_count') is not None else 0,
                'conversion_count': int(phrase.get('conversion_count', 0)) if phrase.get('conversion_count') is not None else 0,
                'send_date': phrase.get('send_date') or '',
                'title': phrase.get('title', ''),
                'message': phrase.get('message', '')
            }
            
            documents.append(text)
            metadatas.append(metadata)
            ids.append(f"phrase_{phrase.get('copy_id', len(documents))}")
        
        # 벡터 저장소에 추가
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"✅ {len(documents)}개 문구를 벡터 저장소에 추가했습니다.")
    
    def search_similar_phrases(self, query: str, n_results: int = 5, 
                              team_id: str = None, channel: str = None,
                              min_ctr: float = 0.0,
                              min_conversion_rate: float = 0.0, 
                              min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """유사한 문구 검색 (채널/팀 필터링 + 키워드/타겟 유사도 계산)"""
        # 채널과 팀으로 필터링 (둘 다 동시에 적용 가능)
        where_conditions = None
        conditions = []
        
        if team_id:
            # team_id가 tuple인 경우 첫 번째 요소 사용, 그 외에는 직접 변환
            if isinstance(team_id, tuple):
                team_id_value = team_id[0] if team_id else None
            else:
                team_id_value = team_id
            
            if team_id_value:
                try:
                    conditions.append({'team_id': int(team_id_value)})
                except (ValueError, TypeError) as e:
                    print(f"⚠️ team_id 변환 실패: {team_id_value} -> {e}")
                    # 변환 실패 시 해당 필터 무시
                    pass
        
        if channel:
            conditions.append({'channel': channel})
        
        # 성과 기준 추가 필터링 (팀/채널 필터가 없을 때만)
        if not conditions:
            if min_ctr > 0:
                conditions.append({'ctr': {"$gte": min_ctr}})
            elif min_conversion_rate > 0:
                conditions.append({'conversion_rate': {"$gte": min_conversion_rate}})
        
        # 조건이 있으면 $and로 결합
        if conditions:
            if len(conditions) == 1:
                where_conditions = conditions[0]
            else:
                where_conditions = {"$and": conditions}
        
        # 벡터 검색 실행
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_conditions if where_conditions else None
        )
        
        # 결과 포맷팅 및 유사도 필터링
        similar_phrases = []
        if (results['documents'] and 
            len(results['documents']) > 0 and 
            results['documents'][0] and 
            len(results['documents'][0]) > 0):
            
            for i, doc in enumerate(results['documents'][0]):
                # 안전한 인덱스 접근
                if (i < len(results['metadatas'][0]) and 
                    i < len(results['distances'][0])):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    similarity_score = 1 - distance
                
                    # 유사도 임계값 확인
                    if similarity_score < min_similarity:
                        continue
                    
                    similar_phrases.append({
                        'text': doc,
                        'title': metadata.get('title', ''),
                        'message': metadata.get('message', ''),
                        'team_id': metadata.get('team_id', ''),
                        'channel': metadata.get('channel', ''),
                        'target_audience': metadata.get('target_audience', ''),
                        'tone': metadata.get('tone', ''),
                        'send_date': metadata.get('send_date', ''),
                        'ctr': metadata.get('ctr', 0),
                        'conversion_rate': metadata.get('conversion_rate', 0),
                        'impression_count': metadata.get('impression_count', 0),
                        'click_count': metadata.get('click_count', 0),
                        'conversion_count': metadata.get('conversion_count', 0),
                        'similarity_score': similarity_score
                    })
        
        return similar_phrases
    
    def sync_from_database(self) -> None:
        """DB의 모든 문구를 벡터 저장소에 동기화"""
        print("🔄 DB에서 벡터 저장소로 문구 동기화 중...")
        
        # 기존 컬렉션 삭제 후 재생성
        try:
            self.client.delete_collection("marketing_phrases")
        except:
            pass
        
        self.collection = self.client.create_collection(
            name="marketing_phrases",
            metadata={"hnsw:space": "cosine"}
        )
        
        # DB에서 모든 문구 조회
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                copy_id,
                team_id,
                channel,
                content_data,
                target_audience,
                tone,
                send_date,
                send_time,
                ctr,
                conversion_rate,
                impression_count,
                click_count,
                conversion_count
            FROM marketing_copies
            WHERE content_data IS NOT NULL
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        # 문구 데이터 변환
        phrases = []
        for row in results:
            content_data = json.loads(row['content_data']) if row['content_data'] else {}
            
            # 채널별로 title/message 추출 방식 다르게 처리
            if row['channel'] == 'RCS':
                # RCS의 경우 button과 message 사용
                title = content_data.get('button', '')
                message = content_data.get('message', '')
            else:
                # APP_PUSH의 경우 title과 message 사용
                title = content_data.get('title', '')
                message = content_data.get('message', '')
            
            phrases.append({
                'copy_id': row['copy_id'],
                'team_id': row['team_id'],
                'channel': row['channel'],
                'title': title,
                'message': message,
                'target_audience': row['target_audience'],
                'tone': row['tone'],
                'send_date': row['send_date'],
                'ctr': row['ctr'],
                'conversion_rate': row['conversion_rate'],
                'impression_count': row['impression_count'],
                'click_count': row['click_count'],
                'conversion_count': row['conversion_count']
            })
        
        # 벡터 저장소에 추가
        self.add_phrases(phrases)
        print(f"✅ 총 {len(phrases)}개 문구 동기화 완료!")
    
    def get_phrases_by_date_range(self, start_date: str = None, end_date: str = None, 
                                 channel: str = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """날짜 범위별로 문구 검색"""
        try:
            where_conditions = {}
            
            if channel:
                where_conditions['channel'] = channel
            
            if start_date or end_date:
                date_conditions = {}
                if start_date:
                    date_conditions['$gte'] = start_date
                if end_date:
                    date_conditions['$lt'] = end_date
                where_conditions['send_date'] = date_conditions
            
            # ChromaDB의 where 조건이 복합 조건을 지원하지 않으므로 단계별로 검색
            if len(where_conditions) > 1:
                # 먼저 채널로 필터링
                if 'channel' in where_conditions:
                    results = self.collection.get(
                        where={'channel': channel},
                        limit=limit
                    )
                else:
                    results = self.collection.get(limit=limit)
                
                # 날짜 조건으로 추가 필터링
                filtered_phrases = []
                for i, metadata in enumerate(results['metadatas']):
                    send_date = metadata.get('send_date', '')
                    
                    # 날짜 조건 확인
                    date_match = True
                    if start_date and send_date < start_date:
                        date_match = False
                    if end_date and send_date >= end_date:
                        date_match = False
                    
                    if date_match:
                        filtered_phrases.append({
                            'copy_id': metadata.get('copy_id', ''),
                            'team_id': metadata.get('team_id', ''),
                            'channel': metadata.get('channel', ''),
                            'title': metadata.get('title', ''),
                            'message': metadata.get('message', ''),
                            'target_audience': metadata.get('target_audience', ''),
                            'tone': metadata.get('tone', ''),
                            'send_date': metadata.get('send_date', ''),
                            'ctr': metadata.get('ctr', 0),
                            'conversion_rate': metadata.get('conversion_rate', 0),
                            'impression_count': metadata.get('impression_count', 0),
                            'click_count': metadata.get('click_count', 0),
                            'conversion_count': metadata.get('conversion_count', 0)
                        })
                
                return filtered_phrases
            else:
                # 단일 조건인 경우
                results = self.collection.get(
                    where=where_conditions if where_conditions else None,
                    limit=limit
                )
                
                phrases = []
                for i, metadata in enumerate(results['metadatas']):
                    phrases.append({
                        'copy_id': metadata.get('copy_id', ''),
                        'team_id': metadata.get('team_id', ''),
                        'channel': metadata.get('channel', ''),
                        'title': metadata.get('title', ''),
                        'message': metadata.get('message', ''),
                        'target_audience': metadata.get('target_audience', ''),
                        'tone': metadata.get('tone', ''),
                        'send_date': metadata.get('send_date', ''),
                        'ctr': metadata.get('ctr', 0),
                        'conversion_rate': metadata.get('conversion_rate', 0),
                        'impression_count': metadata.get('impression_count', 0),
                        'click_count': metadata.get('click_count', 0),
                        'conversion_count': metadata.get('conversion_count', 0)
                    })
                
                return phrases
            
        except Exception as e:
            print(f"날짜 범위 검색 중 오류: {e}")
            return []
    
    def recreate_vector_store(self) -> None:
        """벡터 스토어를 완전히 재생성"""
        print("🔄 벡터 스토어 재생성 중...")
        self.sync_from_database()
        print("✅ 벡터 스토어 재생성 완료!")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보 반환"""
        try:
            count = self.collection.count()
            return {
                'total_phrases': count,
                'status': 'active'
            }
        except:
            return {
                'total_phrases': 0,
                'status': 'inactive'
            }
