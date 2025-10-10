CREATE TABLE IF NOT EXISTS trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    mention_count INTEGER DEFAULT 0,
    trend_score REAL DEFAULT 0.0,
    source TEXT DEFAULT 'google',
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_valid BOOLEAN DEFAULT 1,
    metadata TEXT  -- JSON 형식으로 추가 정보 저장
);

-- 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_keyword ON trends(keyword);
CREATE INDEX IF NOT EXISTS idx_collected_at ON trends(collected_at);
CREATE INDEX IF NOT EXISTS idx_trend_score ON trends(trend_score);

-- 샘플 데이터 (개발용)
INSERT INTO trends (keyword, category, mention_count, trend_score, source) VALUES
('봄신상', 'fashion', 1500, 8.5, 'google'),
('에코백', 'lifestyle', 1200, 7.8, 'instagram'),
('비건뷰티', 'beauty', 980, 8.2, 'naver'),
('홈카페', 'food', 850, 7.5, 'google'),
('제로웨이스트', 'lifestyle', 720, 7.9, 'twitter');