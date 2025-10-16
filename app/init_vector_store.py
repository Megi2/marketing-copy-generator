#!/usr/bin/env python3
"""
벡터 저장소 초기화 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.vector_store import VectorStore

def main():
    print("🔄 벡터 저장소 초기화 시작...")
    
    try:
        # 벡터 저장소 인스턴스 생성
        vector_store = VectorStore()
        
        # DB에서 벡터 저장소로 동기화
        vector_store.sync_from_database()
        
        # 통계 정보 출력
        stats = vector_store.get_collection_stats()
        print(f"✅ 벡터 저장소 초기화 완료!")
        print(f"📊 총 문구 수: {stats['total_phrases']}")
        print(f"📊 상태: {stats['status']}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
