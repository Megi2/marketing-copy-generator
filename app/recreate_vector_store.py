#!/usr/bin/env python3
"""
recreate_vector_store.py
키워드 기반에서 문구 기반으로 변경된 벡터 저장소를 재구성하는 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.vector_store import VectorStore

def main():
    """벡터 저장소 재구성"""
    print("🔄 벡터 저장소를 문구 기반으로 재구성합니다...")
    print("⚠️  기존 벡터 저장소는 삭제되고 새로 생성됩니다.")
    
    # 사용자 확인 (자동 실행)
    print("자동으로 벡터 저장소 재구성을 진행합니다...")
    
    try:
        # VectorStore 인스턴스 생성
        vector_store = VectorStore()
        
        # 기존 컬렉션 삭제 및 재생성
        print("🗑️  기존 벡터 저장소 삭제 중...")
        try:
            vector_store.client.delete_collection("marketing_phrases")
            print("✅ 기존 벡터 저장소 삭제 완료")
        except Exception as e:
            print(f"⚠️  기존 벡터 저장소 삭제 중 오류 (무시 가능): {e}")
        
        # 새 컬렉션 생성
        print("🆕 새 벡터 저장소 생성 중...")
        vector_store.collection = vector_store.client.create_collection(
            name="marketing_phrases",
            metadata={"hnsw:space": "cosine"}
        )
        
        # DB에서 데이터 동기화
        print("📊 데이터베이스에서 벡터 저장소로 동기화 중...")
        vector_store.sync_from_database()
        
        # 통계 확인
        stats = vector_store.get_collection_stats()
        print(f"\n✅ 벡터 저장소 재구성 완료!")
        print(f"📊 총 문구 수: {stats['total_phrases']}개")
        print(f"📊 상태: {stats['status']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ 벡터 저장소 재구성 실패: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
