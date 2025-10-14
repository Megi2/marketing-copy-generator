from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from blueprints.web import web_bp
from blueprints.api import api_bp
from core.logic import MarketingLogic

def create_app():
    """Flask 애플리케이션 생성"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Blueprint 등록
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    
    # 스케줄러 설정 (주 1회 트렌드 업데이트)
    scheduler = BackgroundScheduler(daemon=True)
    
    def weekly_trend_update():
        """매주 월요일 실행되는 트렌드 업데이트 작업"""
        print("🔄 주간 트렌드 업데이트 시작...")
        logic = MarketingLogic()
        
        # TODO: 실제 Google Search API 호출 및 데이터 수집
        # 현재는 더미 데이터로 테스트
        dummy_trends = [
            {'keyword': '전진하', 'category': 'fashion', 'mention_count': 1500, 'trend_score': 9.5},
            {'keyword': '진하답기', 'category': 'lifestyle', 'mention_count': 1200, 'trend_score': 8.8}
        ]
        
        logic.archive_trends(dummy_trends)
        print("✅ 트렌드 업데이트 완료")
    
    # 스케줄러 작업 등록
    scheduler.add_job(
        weekly_trend_update,
        'cron',
        day_of_week=Config.TREND_UPDATE_DAY,
        hour=Config.TREND_UPDATE_HOUR,
        minute=Config.TREND_UPDATE_MINUTE
    )
    
    scheduler.start()
    print(f"⏰ 스케줄러 시작: 매주 {Config.TREND_UPDATE_DAY}요일 {Config.TREND_UPDATE_HOUR}시에 트렌드 업데이트")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
