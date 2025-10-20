#!/usr/bin/env python3
"""
migrate_database.py
기존 DB에서 keywords 컬럼을 제거하는 마이그레이션 스크립트
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from db import get_phrases_db

def backup_database():
    """데이터베이스 백업"""
    db_path = project_root / "data" / "marketing_phrases.db"
    backup_path = project_root / "data" / f"marketing_phrases_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ 데이터베이스 백업 완료: {backup_path}")
    return backup_path

def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    print("🔄 데이터베이스 마이그레이션을 시작합니다...")
    print("⚠️  keywords 컬럼이 제거됩니다.")
    
    # 사용자 확인 (자동 실행)
    print("자동으로 마이그레이션을 진행합니다...")
    
    try:
        # 백업 생성
        backup_path = backup_database()
        
        # 데이터베이스 연결
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        # 1. 새 테이블 생성 (keywords 컬럼 없이)
        print("🆕 새 테이블 생성 중...")
        cursor.execute("""
            CREATE TABLE marketing_copies_new (
                copy_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                channel TEXT NOT NULL CHECK(channel IN ('APP_PUSH', 'RCS')),
                content_data TEXT NOT NULL,
                target_audience TEXT,
                tone TEXT,
                reference_text TEXT,
                send_date DATE,
                send_time TEXT,
                impression_count INTEGER DEFAULT 0,
                click_count INTEGER DEFAULT 0,
                ctr REAL DEFAULT 0.0,
                conversion_count INTEGER DEFAULT 0,
                conversion_rate REAL DEFAULT 0.0,
                trend_keywords TEXT,
                is_ai_generated BOOLEAN DEFAULT 0,
                FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
            )
        """)
        
        # 2. 기존 데이터 복사 (keywords 제외)
        print("📊 기존 데이터 복사 중...")
        cursor.execute("""
            INSERT INTO marketing_copies_new 
            (copy_id, team_id, channel, content_data, target_audience, tone, 
             reference_text, send_date, send_time, impression_count, click_count, ctr, 
             conversion_count, conversion_rate, trend_keywords, is_ai_generated)
            SELECT 
                copy_id, team_id, channel, content_data, target_audience, tone,
                reference_text, send_date, send_time, impression_count, click_count, ctr,
                conversion_count, conversion_rate, trend_keywords, is_ai_generated
            FROM marketing_copies
        """)
        
        # 3. 기존 테이블 삭제
        print("🗑️  기존 테이블 삭제 중...")
        cursor.execute("DROP TABLE marketing_copies")
        
        # 4. 새 테이블 이름 변경
        print("🔄 테이블 이름 변경 중...")
        cursor.execute("ALTER TABLE marketing_copies_new RENAME TO marketing_copies")
        
        # 5. 인덱스 재생성
        print("📊 인덱스 재생성 중...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_marketing_copies_team_id ON marketing_copies(team_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_marketing_copies_channel ON marketing_copies(channel)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_marketing_copies_ctr ON marketing_copies(ctr)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_marketing_copies_conversion_rate ON marketing_copies(conversion_rate)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_marketing_copies_send_date ON marketing_copies(send_date)")
        
        # 변경사항 저장
        conn.commit()
        
        # 결과 확인
        cursor.execute("SELECT COUNT(*) FROM marketing_copies")
        count = cursor.fetchone()[0]
        
        print(f"\n✅ 데이터베이스 마이그레이션 완료!")
        print(f"📊 총 문구 수: {count}개")
        print(f"💾 백업 파일: {backup_path}")
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"❌ 마이그레이션 실패: {e}")
        print(f"💾 백업 파일에서 복원할 수 있습니다: {backup_path}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return 1

def main():
    """메인 함수"""
    return migrate_database()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
