## 프로젝트 구조

```
app/
├─ app.py                  # Flask 앱 팩토리
├─ config.py               # 설정 파일
├─ db.py                   # DB 연결 관리
├─ services/
│  ├─ llm.py               # Gemini API 호출
│  └─ logic.py             # 비즈니스 로직
├─ blueprints/
│  ├─ web.py               # 웹 페이지 라우트
│  └─ api.py               # REST API
├─ templates/              # HTML 템플릿
├─ static/                 # CSS/JS
├─ schema/                 # DB 스키마
└─ wsgi.py                 # 배포 엔트리
```

## 설치 및 실행

### 1. 가상환경 생성
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
`.env` 파일 생성:
```
GEMINI_API_KEY=your-api-key
GOOGLE_SEARCH_API_KEY=your-search-key
GOOGLE_SEARCH_ENGINE_ID=your-engine-id
```

### 4. 데이터베이스 초기화
```bash
python -c "from db import init_databases; init_databases()"
```

### 5. 서버 실행
```bash
python app.py
```

서버 실행 후 브라우저에서 `http://localhost:5000` 접속

