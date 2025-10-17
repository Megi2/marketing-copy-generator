import streamlit as st
import streamlit.components.v1 as components
import json
import sys
import os

# app 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.logic import MarketingLogic

# 페이지 설정
st.set_page_config(
    page_title="마케팅 문구 생성 AI",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
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
    
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    .result-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #6d67a8;
        margin-top: 1rem;
    }
    
    .copy-item {
        background: #f8f9fa;
        padding: 16px;
        margin-bottom: 12px;
        border-radius: 8px;
        border-left: 4px solid #6d67a8;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        white-space: normal !important;
        min-height: auto;
        height: auto;
    }
    
    .copy-title {
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        overflow: visible !important;
        white-space: normal !important;
        font-size: 0.9rem !important;
    }
    
    .copy-message {
        color: #555;
        line-height: 1.4;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        overflow: visible !important;
        white-space: normal !important;
        font-size: 0.9rem !important;
    }
    
    .rcs-copy {
        flex: 1;
        min-height: auto;
        height: auto;
        overflow: visible;
        padding-bottom: 20px;
        margin-bottom: 16px;
    }
    
    .rcs-button {
        font-size: 15px;
        color: #2c3e50;
        margin-bottom: 8px;
        font-weight: 500;
    }
    
    .rcs-message {
        font-size: 14px;
        color: #555;
        line-height: 1.6;
        word-wrap: break-word;
        white-space: pre-wrap;
        max-height: none !important;
        overflow: visible !important;
        height: auto !important;
        min-height: auto !important;
        display: block !important;
        width: 100% !important;
        margin-bottom: 12px;
        padding-bottom: 8px;
    }
    
    .btn-copy {
        background: #6d67a8;
        color: white;
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        margin-left: 12px;
        align-self: center;
        flex-shrink: 0;
    }
    
    .copy-target {
        color: #666;
        font-size: 0.9rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .copy-metrics {
        color: #666;
        font-size: 0.9rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .copy-action {
        color: #666;
        font-size: 0.9rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #6d67a8 0%, #5a5480 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* 전체 컨테이너 텍스트 오버플로우 방지 */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Streamlit 기본 스타일 오버라이드 */
    .stMarkdown {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
    }
    
    /* 텍스트 박스 오버플로우 방지 */
    .stText {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
    }
    
    /* 모든 div 요소에 오버플로우 방지 */
    div {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* Streamlit 컬럼 오버플로우 방지 */
    .stColumn {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        overflow: visible !important;
    }
    
    /* Streamlit 컨테이너 강제 설정 */
    .stApp > div {
        max-width: 100% !important;
    }
    
    /* 복사 버튼 스타일 */
    .copy-btn {
        background: #6d67a8 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 4px 8px !important;
        font-size: 12px !important;
        cursor: pointer !important;
    }
    
    .copy-btn:hover {
        background: #5a5480 !important;
    }
    
    .copy-box {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 12px;
        margin: 8px 0 16px 0;
        font-size: 0.9rem;
        line-height: 1.4;
        word-wrap: break-word;
        overflow-wrap: break-word;
        max-width: 100%;
        white-space: pre-wrap;
        min-height: 60px;
        height: auto;
        overflow: visible !important;
        max-height: none !important;
    }
    
    .scroll {
        max-height: none;
        overflow-y: visible;
    }
    
    .metrics-container {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    
    .metric-item {
        font-size: 0.8rem;
        color: #666;
        padding: 2px 4px;
        background: #f0f0f0;
        border-radius: 3px;
    }
    
    /* Streamlit 기본 요소들 텍스트 잘림 방지 */
    .stContainer {
        overflow: visible !important;
        max-height: none !important;
    }
    
    .element-container {
        overflow: visible !important;
        max-height: none !important;
    }
    
    .stMarkdown > div {
        overflow: visible !important;
        max-height: none !important;
    }
    
    /* 모든 텍스트 요소 강제 설정 */
    * {
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    
    /* 특히 중요한 컨테이너들 */
    .main .block-container > div {
        overflow: visible !important;
        max-height: none !important;
    }
</style>

<script>
function copyToClipboard(elementId) {
    var textArea = document.getElementById(elementId);
    if (textArea) {
        textArea.select();
        textArea.setSelectionRange(0, 99999);
        document.execCommand('copy');
        alert('📋 클립보드에 복사되었습니다!');
    } else {
        alert('복사할 텍스트를 찾을 수 없습니다.');
    }
}
</script>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>📝 마케팅 문구 생성 AI</h1>
    <p>성과가 좋았던 문구를 반영하는 스마트한 카피라이팅</p>
</div>
""", unsafe_allow_html=True)

# 문구 생성 폼
with st.container():
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    with st.form("generate_form"):
        st.subheader("🎯 문구 생성 설정")
        
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input(
                "주제 (Topic) *", 
                placeholder="예: 봄 신상품 세일",
                help="생성할 마케팅 문구의 주제를 입력하세요"
            )
            
            channel = st.selectbox(
                "채널 (Channel)",
                ["RCS", "APP_PUSH"],
                help="메시지를 전송할 채널을 선택하세요"
            )
            
            use_emoji = st.selectbox(
                "이모지 사용",
                ["이모지 포함", "이모지 미포함"]
            )
        
        with col2:
            team_id = st.selectbox(
                "팀 ID (Team ID)",
                [
                    ("선택 안 함 (일반 스타일)", ""),
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
                ],
                help="팀별 스타일을 반영하려면 팀을 선택하세요"
            )
            
            brand = st.text_input(
                "브랜드 (Brand)",
                placeholder="예: 롯데백화점, 롯데마트"
            )
        
        # 추가 정보
        col3, col4 = st.columns(2)
        
        with col3:
            event_name = st.text_input(
                "행사명 (Event Name)",
                placeholder="예: 추석 대축제, 봄맞이 세일"
            )
            
            target_audience = st.text_input(
                "타겟 고객 (Target Audience)",
                placeholder="예: 20-30대 여성"
            )
        
        with col4:
            discount_type = st.text_input(
                "할인 유형 (Discount Type)",
                placeholder="예: 30%할인, 2000원 쿠폰, 특가전 ~50%",
                help="할인 관련 키워드를 쉼표로 구분하여 입력하세요"
            )
            
            appeal_point = st.text_input(
                "소구 포인트 (Appeal Point)",
                placeholder="예: 카드할인+신규고객혜택, 무료배송, 한정수량",
                help="고객에게 어필할 포인트를 쉼표로 구분하여 입력하세요"
            )
        
        # 톤앤매너와 기타 설정
        col5, col6 = st.columns(2)
        
        with col5:
            tone = st.selectbox(
                "톤앤매너 (Tone)",
                ["친근한", "전문적인", "감성적인", "긴박한", "프리미엄"]
            )
            
            reference_text = st.text_area(
                "참고 텍스트 (Reference)",
                placeholder="AI가 참고할 기초 텍스트 (선택사항)",
                height=100
            )
        
        with col6:
            count = st.number_input(
                "생성 개수",
                min_value=1,
                max_value=10,
                value=5,
                help="1개부터 10개까지 생성 가능합니다"
            )
        
        # 제출 버튼
        submitted = st.form_submit_button(
            "✨ 문구 생성하기",
            use_container_width=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 폼 제출 처리
    if submitted:
        if not topic:
            st.error("❌ 주제는 필수 입력 항목입니다.")
        else:
            # 로딩 표시
            with st.spinner("🤖 AI가 문구를 생성하고 있습니다..."):
                try:
                    # MarketingLogic 인스턴스 생성
                    logic = MarketingLogic()
                    
                    # 폼 데이터 구성
                    form_data = {
                        'topic': topic,
                        'channel': channel,
                        'use_emoji': 'true' if use_emoji == "이모지 포함" else 'false',
                        'team_id': team_id,
                        'brand': brand,
                        'event_name': event_name,
                        'target_audience': target_audience,
                        'discount_type': discount_type,
                        'appeal_point': appeal_point,
                        'tone': tone,
                        'reference_text': reference_text,
                        'count': count
                    }
                    
                    # 문구 생성
                    result = logic.generate_marketing_copy(form_data)
                    
                    # 결과 표시
                    st.success("문구 생성이 완료되었습니다!")
                    
                    copies = result.get('copies', [])
                    referenced_phrases = result.get('referenced_phrases', [])
                    
                    # 참고 문구 정보 표시
                    if referenced_phrases:
                        with st.expander("참고된 성과 좋은 문구", expanded=False):
                            for i, phrase in enumerate(referenced_phrases):
                                st.write(f"**{i+1}번째 참고 문구:**")
                                st.write(f"- 유사도: {phrase.get('similarity_score', 0):.1%}")
                                st.write(f"- 성과: CTR {phrase.get('ctr', 0):.2%}, 전환율 {phrase.get('conversion_rate', 0):.2%}")
                                st.write(f"- 제목: {phrase.get('title', '')}")
                                st.write(f"- 내용: {phrase.get('message', '')}")
                                st.write("---")
                    
                    # 생성된 문구들 표시
                    st.markdown("---")
                    st.subheader("생성된 문구")
                    
                    for i, copy in enumerate(copies):
                        with st.container(border=True):  # 상자
                            if channel == 'APP_PUSH' and isinstance(copy, dict) and 'title' in copy and 'message' in copy:
                                # RCS와 유사한 레이아웃으로 변경 - 컬럼으로 나누어서 텍스트는 왼쪽, 버튼은 오른쪽에 배치
                                col1, col2 = st.columns([4, 1])
                                
                                with col1:
                                    st.markdown(f"""
                                    <div class="rcs-copy">
                                        <div class="rcs-button">{i+1}. <strong>제목:</strong> {copy['title']}</div>
                                        <div class="rcs-message"><strong>내용:</strong><br>{copy['message'].replace(chr(10), '<br>')}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col2:
                                    copy_text = f"제목: {copy['title']}\n내용: {copy['message']}"
                                    copy_id = f"copy_text_{i}"
                                    components.html(
                                        f"""
                                        <div>
                                            <textarea id="{copy_id}" style="position: absolute; left: -9999px; opacity: 0;">{copy_text}</textarea>
                                            <button onclick="
                                                var textArea = document.getElementById('{copy_id}');
                                                textArea.select();
                                                textArea.setSelectionRange(0, 99999);
                                                document.execCommand('copy');
                                                alert('📋 클립보드에 복사되었습니다!');
                                            " style="
                                                background: #6d67a8;
                                                color: white;
                                                border: none;
                                                border-radius: 4px;
                                                padding: 8px 16px;
                                                cursor: pointer;
                                                font-size: 12px;
                                            ">복사</button>
                                        </div>
                                        """,
                                        height=38
                                    )
                    
                            else:
                                # RCS 형식
                                if isinstance(copy, dict):
                                    button_text = copy.get('button', '')
                                    message_text = copy.get('message', '')
                    
                                    if button_text or message_text:
                                        # APP_PUSH와 동일한 레이아웃으로 변경 - 컬럼으로 나누어서 텍스트는 왼쪽, 버튼은 오른쪽에 배치
                                        col1, col2 = st.columns([4, 1])
                                        
                                        with col1:
                                            st.markdown(f"""
                                            <div class="rcs-copy">
                                                <div class="rcs-button">{i+1}. <strong>버튼:</strong> {button_text}</div>
                                                <div class="rcs-message"><strong>메시지:</strong><br>{message_text.replace(chr(10), '<br>')}</div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        with col2:
                                            copy_text = f"버튼: {button_text}\n메시지: {message_text}"
                                            copy_id = f"rcs_copy_text_{i}"
                                            components.html(
                                                f"""
                                                <div>
                                                    <textarea id="{copy_id}" style="position: absolute; left: -9999px; opacity: 0;">{copy_text}</textarea>
                                                    <button onclick="
                                                        var textArea = document.getElementById('{copy_id}');
                                                        textArea.select();
                                                        textArea.setSelectionRange(0, 99999);
                                                        document.execCommand('copy');
                                                        alert('📋 클립보드에 복사되었습니다!');
                                                    " style="
                                                        background: #6d67a8;
                                                        color: white;
                                                        border: none;
                                                        border-radius: 4px;
                                                        padding: 8px 16px;
                                                        cursor: pointer;
                                                        font-size: 12px;
                                                    ">복사</button>
                                                </div>
                                                """,
                                                height=38
                                            )
                                    else:
                                        st.write(f"**{i+1}번째 문구:** {copy}")
                                else:
                                    st.write(f"**{i+1}번째 문구:** {copy}")
                    
                    # 생성된 문구를 세션 상태에 저장
                    st.session_state.generated_copies = copies
                    st.session_state.last_generation_params = form_data
                    
                except Exception as e:
                    st.error(f"❌ 문구 생성 중 오류가 발생했습니다: {str(e)}")
                    st.exception(e)

# 사이드바에 추가 정보 표시
with st.sidebar:
    
    # 최근 생성된 문구가 있으면 표시
    if 'generated_copies' in st.session_state:
        st.markdown("---")
        st.header("최근 생성된 문구")
        for i, copy in enumerate(st.session_state.generated_copies[:3]):  # 최근 3개만
            with st.expander(f"문구 {i+1}"):
                if isinstance(copy, dict):
                    if 'title' in copy and 'message' in copy:
                        st.write(f"**타이틀:** {copy['title']}")
                        st.write(f"**본문:** {copy['message']}")
                    elif 'button' in copy and 'message' in copy:
                        st.write(f"**버튼:** {copy['button']}")
                        st.write(f"**메시지:** {copy['message']}")
                else:
                    st.write(copy)
