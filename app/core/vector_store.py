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
    
    def add_phrases(self, phrases: List[Dict[str, Any]]) -> None:
        """문구들을 벡터 저장소에 추가"""
        if not phrases:
            return
        
        # 문서와 메타데이터 준비
        documents = []
        metadatas = []
        ids = []
        
        for phrase in phrases:
            # 키워드와 타겟으로 유사도 계산용 텍스트 생성
            keywords = phrase.get('keywords', '')
            target_audience = phrase.get('target_audience', '')
            text = f"{keywords} {target_audience}".strip()
            
            if not text:
                continue
            
            # 메타데이터 준비 (None 값 제거)
            metadata = {
                'copy_id': phrase.get('copy_id') or '',
                'team_id': phrase.get('team_id') or '',
                'channel': phrase.get('channel') or '',
                'keywords': phrase.get('keywords') or '',
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
            conditions.append({'team_id': int(team_id)})
        
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
                        'keywords': metadata.get('keywords', ''),
                        'target_audience': metadata.get('target_audience', ''),
                        'tone': metadata.get('tone', ''),
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
        
        # 벡터 저장소에 추가
        self.add_phrases(phrases)
        print(f"✅ 총 {len(phrases)}개 문구 동기화 완료!")
    
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
