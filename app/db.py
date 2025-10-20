import sqlite3
import os
import sys

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config import Config

def get_trends_db():
    """트렌드 DB 연결"""
    conn = sqlite3.connect(Config.DB_TRENDS_PATH)
    conn.row_factory = sqlite3.Row  # dict처럼 접근 가능
    return conn

def get_phrases_db():
    """마케팅 문구 DB 연결"""
    conn = sqlite3.connect(Config.DB_PHRASES_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_databases():
    """데이터베이스 초기화 (테이블 생성)"""
    # data 디렉토리 생성
    os.makedirs('data', exist_ok=True)
    
    # trends.db 초기화
    conn_trends = get_trends_db()
    with open('app/schema/trends.sql', 'r', encoding='utf-8') as f:
        conn_trends.executescript(f.read())
    conn_trends.commit()
    conn_trends.close()
    
    # marketing_phrases.db 초기화
    conn_phrases = get_phrases_db()
    with open('app/schema/phrases.sql', 'r', encoding='utf-8') as f:
        conn_phrases.executescript(f.read())
    conn_phrases.commit()
    conn_phrases.close()
    
    print("✅ 데이터베이스 초기화 완료")