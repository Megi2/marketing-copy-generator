#!/bin/bash

# Streamlit 앱 실행 스크립트
echo "마케팅 문구 생성 AI (Streamlit) 시작 중..."

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
fi

# 의존성 설치 확인
echo "의존성 확인 중..."
pip install -r app/requirements.txt

# Streamlit 앱 실행
echo "streamlit 앱 실행 중..."
echo "브라우저에서 http://localhost:8501 을 열어주세요"
echo "종료하려면 Ctrl+C를 누르세요"
echo ""

cd /Users/lotte/Documents/marketing-copy-generator
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
