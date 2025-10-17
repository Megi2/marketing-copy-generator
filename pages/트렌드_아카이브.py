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
        margin: 1rem 0;
        border-radius: 12px;
        border-left: 4px solid #6d67a8;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .trend-keyword {
        font-weight: bold;
        color: #2c3e50;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    
    .trend-info {
        display: flex;
        gap: 1rem;
        font-size: 0.9rem;
        color: #666;
        flex-wrap: wrap;
    }
    
    .trend-category {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .trend-score {
        background: #f3e5f5;
        color: #7b1fa2;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .trend-mentions {
        background: #e8f5e8;
        color: #2e7d32;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }
    
    .score-high {
        color: #d32f2f;
        font-weight: bold;
    }
    
    .score-medium {
        color: #f57c00;
        font-weight: bold;
    }
    
    .score-low {
        color: #388e3c;
        font-weight: bold;
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
    <h1>📈 트렌드 아카이브</h1>
    <p>최신 마케팅 트렌드 키워드를 확인하고 문구에 활용하세요</p>
</div>
""", unsafe_allow_html=True)

# 필터 섹션
st.markdown('<div class="filter-container">', unsafe_allow_html=True)
st.subheader("🔍 트렌드 검색")

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
            ("트렌드 점수 높은순", "trend_score"),
            ("언급 수 많은순", "mention_count")
        ],
        format_func=lambda x: x[0],
        help="트렌드를 어떤 기준으로 정렬할지 선택하세요"
    )

st.markdown('</div>', unsafe_allow_html=True)

# 트렌드 조회 버튼
if st.button("📊 트렌드 조회", use_container_width=True):
    with st.spinner("📈 트렌드를 불러오는 중..."):
        try:
            logic = MarketingLogic()
            
            # 트렌드 조회
            trends = logic.get_recent_trends(limit)
            
            if trends:
                st.success(f"✅ {len(trends)}개의 트렌드를 찾았습니다.")
                
                # 통계 정보 표시
                if trends:
                    total_mentions = sum(trend.get('mention_count', 0) for trend in trends)
                    avg_score = sum(trend.get('trend_score', 0) for trend in trends) / len(trends) if trends else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("평균 트렌드 점수", f"{avg_score:.1f}")
                    with col2:
                        st.metric("총 언급 수", f"{total_mentions:,}")
                    with col3:
                        st.metric("트렌드 수", len(trends))
                
                # 트렌드 차트 (간단한 막대 차트)
                if len(trends) > 1:
                    st.subheader("📊 트렌드 점수 비교")
                    
                    # 데이터프레임 생성
                    df = pd.DataFrame(trends)
                    df = df.head(10)  # 상위 10개만 표시
                    
                    # 막대 차트
                    st.bar_chart(
                        df.set_index('keyword')['trend_score'],
                        height=400
                    )
                
                # 트렌드 목록 표시
                st.subheader("🔥 트렌드 키워드")
                
                for i, trend in enumerate(trends):
                    st.markdown('<div class="trend-item">', unsafe_allow_html=True)
                    
                    # 트렌드 점수에 따른 색상 분류
                    score = trend.get('trend_score', 0)
                    if score >= 8:
                        score_class = "score-high"
                    elif score >= 5:
                        score_class = "score-medium"
                    else:
                        score_class = "score-low"
                    
                    # 키워드 표시
                    st.markdown(f'<div class="trend-keyword">#{trend["keyword"]}</div>', unsafe_allow_html=True)
                    
                    # 트렌드 정보 표시
                    st.markdown('<div class="trend-info">', unsafe_allow_html=True)
                    
                    # 카테고리
                    category = trend.get('category', 'general')
                    st.markdown(f'<span class="trend-category">카테고리: {category}</span>', unsafe_allow_html=True)
                    
                    # 트렌드 점수
                    st.markdown(f'<span class="trend-score {score_class}">점수: {score:.1f}</span>', unsafe_allow_html=True)
                    
                    # 언급 수
                    mentions = trend.get('mention_count', 0)
                    st.markdown(f'<span class="trend-mentions">언급: {mentions:,}회</span>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 트렌드 활용 팁
                    with st.expander(f"💡 '{trend['keyword']}' 활용 팁", expanded=False):
                        if category == 'fashion':
                            st.write("👗 패션 관련 문구에 활용하세요:")
                            st.write(f"- '{trend['keyword']}'를 활용한 스타일링 문구")
                            st.write(f"- 트렌디한 '{trend['keyword']}' 컬렉션")
                        elif category == 'beauty':
                            st.write("💄 뷰티 관련 문구에 활용하세요:")
                            st.write(f"- '{trend['keyword']}' 뷰티 트렌드")
                            st.write(f"- '{trend['keyword']}' 메이크업 팁")
                        elif category == 'food':
                            st.write("🍽️ 푸드 관련 문구에 활용하세요:")
                            st.write(f"- '{trend['keyword']}' 맛집 추천")
                            st.write(f"- '{trend['keyword']}' 레시피")
                        else:
                            st.write(f"🌟 '{trend['keyword']}'를 활용한 마케팅 문구:")
                            st.write(f"- 최신 '{trend['keyword']}' 트렌드 반영")
                            st.write(f"- '{trend['keyword']}'와 함께하는 특별한 혜택")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # 트렌드 데이터를 세션 상태에 저장
                st.session_state.current_trends = trends
                
            else:
                st.info("📭 트렌드 데이터가 없습니다.")
                
        except Exception as e:
            st.error(f"❌ 트렌드를 불러오는 중 오류가 발생했습니다: {str(e)}")
            st.exception(e)

# 트렌드 업데이트 섹션 (관리자용)
with st.expander("🔧 트렌드 관리", expanded=False):
    st.subheader("📊 벡터 저장소 상태")
    
    if st.button("📈 벡터 저장소 통계 조회"):
        with st.spinner("통계를 불러오는 중..."):
            try:
                logic = MarketingLogic()
                stats = logic.vector_store.get_collection_stats()
                
                st.success("✅ 벡터 저장소 통계를 불러왔습니다.")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("총 문서 수", stats.get('total_documents', 0))
                with col2:
                    st.metric("컬렉션 수", stats.get('total_collections', 0))
                with col3:
                    st.metric("마지막 업데이트", stats.get('last_updated', 'N/A'))
                
            except Exception as e:
                st.error(f"❌ 통계 조회 중 오류가 발생했습니다: {str(e)}")
    
    st.subheader("🔄 벡터 저장소 동기화")
    st.write("데이터베이스의 최신 문구를 벡터 저장소에 반영합니다.")
    
    if st.button("🔄 동기화 실행", type="primary"):
        with st.spinner("벡터 저장소를 동기화하는 중..."):
            try:
                logic = MarketingLogic()
                logic.vector_store.sync_from_database()
                
                st.success("✅ 벡터 저장소 동기화가 완료되었습니다.")
                
            except Exception as e:
                st.error(f"❌ 동기화 중 오류가 발생했습니다: {str(e)}")

# 사이드바에 추가 정보
with st.sidebar:
    st.header("트렌드 가이드")
    st.markdown("""
    ### 트렌드 아카이브
    - 최신 마케팅 트렌드 키워드를 확인할 수 있습니다
    - 트렌드 점수와 언급 수를 통해 인기도를 파악하세요
    - 카테고리별로 트렌드를 필터링할 수 있습니다
    
    ### 트렌드 지표
    - **트렌드 점수**: 키워드의 인기도 (0-10점)
    - **언급 수**: 해당 키워드가 언급된 횟수
    - **카테고리**: 키워드의 분야 (패션, 뷰티, 푸드 등)
    
    ### 활용 팁
    - 높은 트렌드 점수의 키워드를 문구에 활용하세요
    - 카테고리별로 적절한 문구 스타일을 적용하세요
    - 최신 트렌드를 반영한 문구가 더 높은 관심을 받습니다
    """)
    
    # 인기 트렌드 (예시)
    st.markdown("---")
    st.header("인기 트렌드")
    st.markdown("""
    **이번 주 TOP 3:**
    1. 전진하 (패션)
    2. 진하답기 (라이프스타일)
    3. 봄신상 (패션)
    
    **트렌드 활용법:**
    - 문구에 해시태그로 포함
    - 제품 설명에 자연스럽게 삽입
    - 마케팅 캠페인 테마로 활용
    """)
    
    # 최근 조회한 트렌드가 있으면 표시
    if 'current_trends' in st.session_state:
        st.markdown("---")
        st.header("최근 조회한 트렌드")
        for trend in st.session_state.current_trends[:5]:  # 최근 5개만
            st.write(f"• {trend['keyword']} ({trend.get('category', 'general')})")
