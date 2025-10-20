import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# app 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from core.logic import MarketingLogic

# 페이지 설정
st.set_page_config(
    page_title="트렌드 아카이브 - 마케팅 문구 생성 AI",
    page_icon="📈",
    layout="wide"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #6d67a8 0%, #5a5480 100%);
        color: white;
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .trend-item {
        background: white;
        padding: 1.5rem;
        margin: 0.75rem 0;
        border-radius: 12px;
        border-left: 4px solid #6d67a8;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        word-wrap: break-word;
    }
    
    .trend-keyword {
        font-weight: bold;
        color: #2c3e50;
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
    }
    
    .trend-info {
        display: flex;
        gap: 1.5rem;
        font-size: 1.1rem;
        color: #666;
        flex-wrap: wrap;
        margin-top: 0.5rem;
        align-items: center;
    }
    
    .trend-category {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        font-weight: 500;
        font-size: 1rem;
    }
    
    .trend-date {
        background: #e8f5e8;
        color: #2e7d32;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        font-weight: 500;
        font-size: 1rem;
    }
    
    .filter-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>트렌드 아카이브</h1>
    <p>최신 마케팅 트렌드 키워드를 확인하고 문구에 활용하세요</p>
</div>
""", unsafe_allow_html=True)

# 필터 섹션
st.markdown('<div class="filter-container">', unsafe_allow_html=True)
st.subheader("트렌드 검색")

col1, col2, col3 = st.columns(3)

with col1:
    limit = st.number_input(
        "표시 개수",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
        help="한 번에 표시할 트렌드 개수를 설정하세요"
    )

with col2:
    category_filter = st.selectbox(
        "카테고리 필터",
        ["전체", "fashion", "lifestyle", "beauty", "food", "travel", "general"],
        help="특정 카테고리의 트렌드만 보려면 카테고리를 선택하세요"
    )

with col3:
    sort_by = st.selectbox(
        "정렬 기준",
        [
            ("최신순", "latest"),
            ("키워드순", "keyword"),
            ("카테고리순", "category")
        ],
        format_func=lambda x: x[0],
        help="트렌드를 어떤 기준으로 정렬할지 선택하세요"
    )

st.markdown('</div>', unsafe_allow_html=True)

# 트렌드 조회 버튼
if st.button("트렌드 조회", use_container_width=True):
    with st.spinner("트렌드를 불러오는 중..."):
        try:
            logic = MarketingLogic()
            
            # 트렌드 조회
            trends = logic.get_recent_trends(limit)
            
            if trends:
                st.success(f"✅ {len(trends)}개의 트렌드를 찾았습니다.")
                
                
                
                # 트렌드 목록 표시
                st.subheader("트렌드 키워드")
                
                for i, trend in enumerate(trends):
                    # 트렌드 정보
                    category = trend.get('category', 'general')
                    date = trend.get('date', '')
                    
                    # 전체 카드를 한 번의 st.markdown 호출로 렌더링
                    st.markdown(f'''
                    <div class="trend-item">
                        <div class="trend-keyword">#{trend["keyword"]}</div>
                        <div class="trend-info">
                            <span class="trend-category">카테고리: {category}</span>
                            <span class="trend-date">날짜: {date}</span>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # 트렌드 데이터를 세션 상태에 저장
                st.session_state.current_trends = trends
                
            else:
                st.info("📭 트렌드 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"❌ 트렌드를 불러오는 중 오류가 발생했습니다: {str(e)}")
            st.exception(e)



