import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask 설정
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # 데이터베이스 경로
    DB_TRENDS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'trends.db')
    DB_PHRASES_PATH = os.path.join(os.path.dirname(__file__), 'data', 'marketing_phrases.db')
    
    # API 키
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GOOGLE_SEARCH_API_KEY = os.getenv('GOOGLE_SEARCH_API_KEY')
    GOOGLE_SEARCH_ENGINE_ID = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    # 스케줄러 설정 (주 1회 트렌드 업데이트)
    TREND_UPDATE_DAY = 'mon'  # 월요일
    TREND_UPDATE_HOUR = 9     # 오전 9시