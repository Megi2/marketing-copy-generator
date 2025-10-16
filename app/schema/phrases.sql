-- 마케팅 문구 데이터베이스 스키마
CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS marketing_copies (
    copy_id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER,
    channel TEXT NOT NULL CHECK(channel IN ('APP_PUSH', 'RCS')),
    content_data TEXT NOT NULL, -- JSON 형태로 저장
    keywords TEXT,
    target_audience TEXT,
    tone TEXT,
    reference_text TEXT,
    send_date TEXT, -- 발송 날짜 (YYYYMMDD 형식)
    impression_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    ctr REAL DEFAULT 0.0,
    conversion_count INTEGER DEFAULT 0,
    conversion_rate REAL DEFAULT 0.0,
    trend_keywords TEXT,
    is_ai_generated BOOLEAN DEFAULT 0,
    FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_marketing_copies_team_id ON marketing_copies(team_id);
CREATE INDEX IF NOT EXISTS idx_marketing_copies_channel ON marketing_copies(channel);
CREATE INDEX IF NOT EXISTS idx_marketing_copies_ctr ON marketing_copies(ctr);
CREATE INDEX IF NOT EXISTS idx_marketing_copies_conversion_rate ON marketing_copies(conversion_rate);
CREATE INDEX IF NOT EXISTS idx_marketing_copies_created_at ON marketing_copies(created_at);