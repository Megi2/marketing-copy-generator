# 📝 마케팅 문구 생성 AI

성과가 좋았던 문구를 반영하는 스마트한 카피라이팅 도구입니다. Streamlit 기반의 웹 애플리케이션으로 마케팅 문구를 생성하고 관리할 수 있습니다.

## ✨ 주요 기능

- 🤖 **AI 문구 생성**: Gemini AI를 활용한 마케팅 문구 자동 생성
- 📚 **문구 아카이브**: 팀별 성과 좋은 문구 조회 및 분석
- 📈 **트렌드 아카이브**: 최신 마케팅 트렌드 키워드 확인
- 📤 **CSV 업로드**: 기존 마케팅 데이터 업로드 및 관리
- 🔍 **RAG 검색**: 벡터 검색을 통한 유사 문구 참조

## 📁 프로젝트 구조

```
marketing-copy-generator/
├─ streamlit_app.py           # Streamlit 메인 앱
├─ pages/                     # 멀티페이지 구조
│  ├─ phrases_archive.py      # 문구 아카이브 페이지
│  ├─ trends_archive.py       # 트렌드 아카이브 페이지
│  └─ upload.py               # CSV 업로드 페이지
├─ app/
│  ├─ core/                   # 핵심 로직
│  │  ├─ llm.py              # Gemini API 호출
│  │  ├─ logic.py            # 비즈니스 로직
│  │  └─ vector_store.py     # 벡터 저장소 관리
│  ├─ data/                   # 데이터베이스 파일
│  ├─ schema/                 # DB 스키마
│  └─ requirements.txt        # 의존성 목록
├─ flask_backup/              # Flask 버전 백업
└─ run_streamlit.sh          # 실행 스크립트
```

## 🚀 설치 및 실행

### 1. 가상환경 생성
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 패키지 설치
```bash
pip install -r app/requirements.txt
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
python -c "from app.db import init_databases; init_databases()"
```

### 5. Streamlit 앱 실행

#### 방법 1: 실행 스크립트 사용
```bash
./run_streamlit.sh
```

#### 방법 2: 직접 실행
```bash
streamlit run streamlit_app.py
```

서버 실행 후 브라우저에서 `http://localhost:8501` 접속

## 📱 사용법

### 1. 문구 생성
- 메인 페이지에서 주제와 채널을 선택
- 팀 ID를 선택하면 해당 팀의 성과 좋은 문구를 참고
- 추가 정보 입력 후 "문구 생성하기" 버튼 클릭

### 2. 문구 아카이브
- 팀별로 성과가 좋았던 문구 조회
- 다양한 정렬 기준으로 문구 검색
- 성과 지표를 통한 효과적인 문구 패턴 분석

### 3. 트렌드 아카이브
- 최신 마케팅 트렌드 키워드 확인
- 트렌드 점수와 언급 수를 통한 인기도 파악
- 카테고리별 트렌드 필터링

### 4. CSV 업로드
- 기존 마케팅 데이터를 CSV 또는 JSON 파일로 업로드
- 팀별 문구 데이터베이스 구축
- 벡터 저장소 동기화로 RAG 검색 정확도 향상

## 🔧 기술 스택

- **Frontend**: Streamlit
- **Backend**: Python
- **AI**: Google Gemini API
- **Database**: SQLite
- **Vector Store**: ChromaDB
- **Search**: Sentence Transformers

## 📊 마이그레이션 정보

이 프로젝트는 Flask에서 Streamlit으로 마이그레이션되었습니다.

### 변경사항
- **프론트엔드**: HTML/CSS/JS → Streamlit 위젯
- **라우팅**: Flask Blueprint → Streamlit 멀티페이지
- **API**: REST API → 직접 함수 호출
- **스타일링**: CSS → Streamlit CSS-in-Python

### 백업 파일
기존 Flask 버전은 `flask_backup/` 디렉토리에 백업되어 있습니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

