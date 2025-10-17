import streamlit as st
import json
import sys
import os

# app 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from core.logic import MarketingLogic

# 페이지 설정
st.set_page_config(
    page_title="문구 아카이브 - 마케팅 문구 생성 AI",
    page_icon="📚",
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
    
    .archive-item {
        background: #f8f9fa;
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 8px;
        border-left: 4px solid #764ba2;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        word-wrap: break-word;
        word-break: break-word;
        white-space: pre-wrap;
        max-width: 100%;
        overflow-wrap: break-word;
        box-sizing: border-box;
    }
    
    .archive-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        flex-wrap: wrap;
        gap: 10px;
    }
    
    .archive-title {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        flex: 1;
        min-width: 200px;
        word-wrap: break-word;
        word-break: break-word;
    }
    
    .archive-date {
        font-size: 14px;
        color: #666;
        background: #f0f0f0;
        padding: 4px 8px;
        border-radius: 4px;
        white-space: nowrap;
        flex-shrink: 0;
    }
    
    .archive-message {
        font-size: 16px;
        color: #555;
        margin-bottom: 12px;
        line-height: 1.6;
        word-wrap: break-word;
        word-break: break-word;
        white-space: pre-wrap;
        max-width: 100%;
        overflow-wrap: break-word;
    }
    
    .archive-meta {
        display: grid;
        grid-template-columns: 1fr auto auto auto auto auto;
        gap: 10px;
        font-size: 13px;
        align-items: start;
        width: 100%;
        box-sizing: border-box;
    }
    
    .meta-item-target {
        grid-column: 1;
        background: white;
        padding: 8px 12px;
        border-radius: 5px;
        border: 1px solid #e9ecef;
        word-break: break-word;
        min-width: 0;
    }
    
    .meta-item {
        background: white;
        padding: 8px 12px;
        border-radius: 5px;
        border: 1px solid #e9ecef;
        min-width: 80px;
        text-align: center;
        flex-shrink: 0;
    }
    
    .meta-label {
        font-weight: bold;
        color: #495057;
        display: block;
        margin-bottom: 2px;
    }
    
    .meta-value {
        color: #007bff;
        font-weight: bold;
    }
    
    .performance-high {
        border-left-color: #28a745;
    }
    
    .performance-medium {
        border-left-color: #ffc107;
    }
    
    .performance-low {
        border-left-color: #dc3545;
    }
    
    .filter-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 2rem;
    }
    
    .sort-title {
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #f0f0f0;
    }
    
    .sort-title h3 {
        color: #6d67a8;
        margin: 0;
        font-size: 20px;
    }
    
    /* 전체 컨테이너 텍스트 오버플로우 방지 */
    .main .block-container {
        max-width: 100%;
        padding-left: 1rem;
        padding-right: 1rem;
        box-sizing: border-box;
    }
    
    /* Streamlit 기본 스타일 오버라이드 */
    .stMarkdown {
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        box-sizing: border-box;
    }
    
    /* 텍스트 박스 오버플로우 방지 */
    .stText {
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        box-sizing: border-box;
    }
    
    /* 반응형 그리드 */
    @media (max-width: 768px) {
        .archive-meta {
            grid-template-columns: 1fr;
            gap: 8px;
        }
        
        .meta-item-target {
            grid-column: 1;
        }
        
        .meta-item {
            min-width: auto;
        }
        
        .archive-header {
            flex-direction: column;
            align-items: flex-start;
        }
        
        .archive-title {
            min-width: auto;
        }
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>📚 문구 아카이브</h1>
    <p>팀별 성과 좋은 마케팅 문구를 확인하고 참고하세요</p>
</div>
""", unsafe_allow_html=True)

# 필터 섹션
st.markdown('<div class="filter-container">', unsafe_allow_html=True)
st.subheader("🔍 검색 필터")

col1, col2, col3, col4 = st.columns(4)

with col1:
    team_options = [
        ("그로스마케팅팀", "1"),
        ("버티컬마케팅팀", "3"),
        ("마케팅운영팀", "4"),
        ("식품팀", "9"),
        ("여행서비스TFT", "2"),
        ("리빙팀", "8"),
        ("스포츠레저팀", "5"),
        ("b tft", "13"),
        ("유아동패션팀", "10"),
        ("명품잡화팀", "14"),
        ("L.TOWN팀", "11"),
        ("B2B팀", "16"),
        ("패션팀", "6"),
        ("브랜드뷰티팀", "7"),
        ("제휴서비스상품팀", "12"),
        ("브랜드패션팀", "15"),
        ("디지털가전팀", "17")
    ]
    
    selected_team = st.selectbox(
        "팀 선택",
        options=[("전체", "")] + team_options,
        format_func=lambda x: x[0],
        help="특정 팀의 문구만 보려면 팀을 선택하세요"
    )
    team_id = selected_team[1] if selected_team else ""

with col2:
    channel_filter = st.selectbox(
        "채널 필터",
        ["전체", "RCS", "APP_PUSH"],
        help="특정 채널의 문구만 보려면 채널을 선택하세요"
    )

with col3:
    sort_by = st.selectbox(
        "정렬 기준",
        [
            ("최신순", "latest"),
            ("전환율 높은순", "conversion_rate"),
            ("CTR 높은순", "ctr"),
            ("노출수 높은순", "impression_count"),
            ("클릭수 높은순", "click_count"),
            ("구매수 높은순", "conversion_count")
        ],
        format_func=lambda x: x[0],
        help="문구를 어떤 기준으로 정렬할지 선택하세요"
    )

with col4:
    limit = st.number_input(
        "표시 개수",
        min_value=10,
        max_value=200,
        value=10,
        step=10,
        help="한 번에 표시할 문구 개수를 설정하세요"
    )

st.markdown('</div>', unsafe_allow_html=True)

# 검색 버튼
if st.button("🔍 문구 검색", use_container_width=True):
    if not team_id:
        st.warning("⚠️ 팀을 선택해주세요.")
    else:
        with st.spinner("📊 문구를 불러오는 중..."):
            try:
                logic = MarketingLogic()
                
                # 채널 필터 적용
                channel = None if channel_filter == "전체" else channel_filter
                
                # 문구 조회
                copies = logic.get_team_style(
                    team_id=team_id,
                    sort_by=sort_by[1],
                    limit=limit,
                    channel=channel
                )
                
                if copies:
                    st.success(f"✅ {len(copies)}개의 문구를 찾았습니다.")
                    
                    # 정렬 기준에 따른 제목 설정
                    sort_titles = {
                        'latest': f'최신순 {len(copies)}개',
                        'conversion_rate': f'전환율 높은 순 {len(copies)}개',
                        'ctr': f'CTR 높은 순 {len(copies)}개',
                        'impression_count': f'노출수 높은 순 {len(copies)}개',
                        'click_count': f'클릭수 높은 순 {len(copies)}개',
                        'conversion_count': f'전환수 높은 순 {len(copies)}개'
                    }
                    
                    sort_title = sort_titles.get(sort_by[1], f'문구 목록 ({len(copies)}개)')
                    
                    # 정렬 제목 표시
                    st.markdown(f'''
                    <div class="sort-title">
                        <h3>📊 {sort_title}</h3>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    for i, copy in enumerate(copies):
                        # 성과에 따른 색상 분류
                        conversion_rate = copy.get('conversion_rate', 0)
                        performance_class = 'performance-low'
                        if conversion_rate > 0.1:
                            performance_class = 'performance-high'
                        elif conversion_rate > 0.05:
                            performance_class = 'performance-medium'
                        
                        # 채널에 따른 라벨 설정
                        title_label = '제목' if channel_filter == 'APP_PUSH' else '버튼'
                        message_label = '내용' if channel_filter == 'APP_PUSH' else '메시지'
                        
                        # HTML 구조를 Flask 버전과 유사하게 구성
                        archive_html = f'''
                        <div class="archive-item {performance_class}">
                            <div class="archive-header">
                                <div class="archive-title">#{i+1} {title_label}: {copy.get('title', copy.get('button', '없음'))}</div>
                                <div class="archive-date">{copy.get('send_date', 'N/A')}</div>
                            </div>
                            <div class="archive-message"><strong>{message_label}:</strong> {copy.get('message', '없음')}</div>
                            <div class="archive-meta">
                                <div class="meta-item-target">
                                    <span class="meta-label">타겟</span>
                                    <span class="meta-value">{copy.get('target_audience', 'N/A')}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">전환율</span>
                                    <span class="meta-value">{(conversion_rate * 100):.1f}%</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">CTR</span>
                                    <span class="meta-value">{((copy.get('ctr', 0)) * 100):.1f}%</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">노출수</span>
                                    <span class="meta-value">{(copy.get('impression_count', 0)):,}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">클릭수</span>
                                    <span class="meta-value">{(copy.get('click_count', 0)):,}</span>
                                </div>
                                <div class="meta-item">
                                    <span class="meta-label">전환수</span>
                                    <span class="meta-value">{(copy.get('conversion_count', 0)):,}</span>
                                </div>
                            </div>
                        </div>
                        '''
                        
                        st.markdown(archive_html, unsafe_allow_html=True)
                
                else:
                    st.info("📭 해당 조건에 맞는 문구가 없습니다.")
                    
            except Exception as e:
                st.error(f"❌ 문구를 불러오는 중 오류가 발생했습니다: {str(e)}")
                st.exception(e)

