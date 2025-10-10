CREATE TABLE IF NOT EXISTS marketing_phrases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT NOT NULL,
    copy_text TEXT NOT NULL,
    target_audience TEXT,
    tone TEXT,
    performance_score REAL DEFAULT 0.0,  -- CTR, 전환율 등 성과 지표
    metadata TEXT,  -- JSON 형식으로 추가 정보 저장
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_team_id ON marketing_phrases(team_id);
CREATE INDEX IF NOT EXISTS idx_performance_score ON marketing_phrases(performance_score);
CREATE INDEX IF NOT EXISTS idx_created_at ON marketing_phrases(created_at);

-- 샘플 데이터 (팀별 과거 문구 예시)
INSERT INTO marketing_phrases (team_id, copy_text, target_audience, tone, performance_score) VALUES
('team_growth', '지금 바로 시작하세요! 첫 구매 20% 할인', '20-30대', '친근한', 8.5),
('team_growth', '놓치면 후회할 특가! 오늘만 이 가격', '전연령', '긴박한', 9.2),
('team_growth', '당신만을 위한 특별한 혜택', '20-40대', '프리미엄', 7.8),
('team_brand', '새로운 라이프스타일의 시작', '30-40대', '전문적인', 8.0),
('team_brand', '일상에 특별함을 더하다', '20-30대 여성', '감성적인', 8.7);