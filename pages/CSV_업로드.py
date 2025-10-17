import streamlit as st
import pandas as pd
import json
import io
import sys
import os

# app 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from core.logic import MarketingLogic

# 페이지 설정
st.set_page_config(
    page_title="CSV 업로드 - 마케팅 문구 생성 AI",
    page_icon="📤",
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
    
    .upload-container {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    .file-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #6d67a8;
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    
    .preview-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
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
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>📤 CSV 업로드</h1>
    <p>마케팅 문구 데이터를 CSV 또는 JSON 파일로 업로드하세요</p>
</div>
""", unsafe_allow_html=True)

# 업로드 섹션
st.markdown('<div class="upload-container">', unsafe_allow_html=True)

st.subheader("📁 파일 업로드")

# 파일 업로드 위젯
uploaded_file = st.file_uploader(
    "CSV 또는 JSON 파일을 선택하세요",
    type=['csv', 'json'],
    help="마케팅 문구 데이터가 포함된 CSV 또는 JSON 파일을 업로드하세요"
)

if uploaded_file is not None:
    # 파일 정보 표시
    st.markdown('<div class="file-info">', unsafe_allow_html=True)
    st.write(f"**파일명:** {uploaded_file.name}")
    st.write(f"**파일 크기:** {uploaded_file.size:,} bytes")
    st.write(f"**파일 타입:** {uploaded_file.type}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 파일 내용 미리보기
    st.subheader("👀 파일 미리보기")
    
    try:
        if uploaded_file.name.lower().endswith('.json'):
            # JSON 파일 처리
            file_content = uploaded_file.read().decode('utf-8')
            data = json.loads(file_content)
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
                st.write(f"**총 {len(data)}개의 레코드가 있습니다.**")
                
                # 데이터프레임 미리보기
                st.dataframe(df.head(10), use_container_width=True)
                
                # 컬럼 정보
                st.write("**컬럼 정보:**")
                for col in df.columns:
                    st.write(f"- {col}: {df[col].dtype}")
            else:
                st.error("❌ JSON 파일은 배열 형태여야 합니다.")
                
        else:
            # CSV 파일 처리
            file_content = uploaded_file.read().decode('utf-8')
            
            try:
                df = pd.read_csv(io.StringIO(file_content), header=None)
            except UnicodeDecodeError:
                # CP949 인코딩 시도
                uploaded_file.seek(0)
                file_content = uploaded_file.read().decode('cp949')
                df = pd.read_csv(io.StringIO(file_content), header=None)
            
            st.write(f"**총 {len(df)}개의 행이 있습니다.**")
            
            # 데이터프레임 미리보기
            st.dataframe(df.head(10), use_container_width=True)
            
            # 컬럼 정보
            st.write("**컬럼 정보:**")
            st.write("CSV 파일은 헤더가 없는 형식으로 처리됩니다.")
            st.write("각 컬럼의 위치와 내용을 확인하세요.")
    
    except Exception as e:
        st.error(f"❌ 파일을 읽는 중 오류가 발생했습니다: {str(e)}")
    
    # 업로드 버튼
    st.subheader("🚀 데이터 업로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 데이터베이스에 업로드", type="primary", use_container_width=True):
            with st.spinner("데이터를 업로드하는 중..."):
                try:
                    logic = MarketingLogic()
                    
                    # 파일 내용 다시 읽기
                    uploaded_file.seek(0)
                    file_content = uploaded_file.read().decode('utf-8')
                    
                    # 업로드 처리 (기존 API 로직 활용)
                    if uploaded_file.name.lower().endswith('.json'):
                        # JSON 파일 처리
                        data = json.loads(file_content)
                        if not isinstance(data, list):
                            st.error("❌ JSON 파일은 배열 형태여야 합니다.")
                        else:
                            df = pd.DataFrame(data)
                            
                            # JSON 구조에 맞게 컬럼 매핑
                            if 'contents' in df.columns:
                                df['title'] = df['contents'].apply(lambda x: x.get('title', '') if isinstance(x, dict) else '')
                                df['message'] = df['contents'].apply(lambda x: x.get('message', '') if isinstance(x, dict) else '')
                            
                            # 팀명을 팀 ID로 매핑
                            team_mapping = {
                                '그로스마케팅': 1, '여행서비스TFT': 2, '버티컬마케팅팀': 3, '마케팅운영팀': 4,
                                '스포츠레저팀': 5, '패션팀': 6, '브랜드뷰티팀': 7, '리빙팀': 8, '식품팀': 9,
                                '유아동패션팀': 10, 'L.TOWN팀': 11, '제휴서비스상품팀': 12, 'b tft': 13,
                                '명품잡화팀': 14, '브랜드패션팀': 15, 'B2B팀': 16, '디지털가전팀': 17
                            }
                            
                            # 데이터 변환 및 저장
                            success_count = 0
                            error_count = 0
                            
                            for _, row in df.iterrows():
                                try:
                                    copy_data = {
                                        'team_id': int(row.get('team_id', 1)),
                                        'channel': str(row.get('channel', 'APP_PUSH')).upper(),
                                        'content_data': json.dumps({
                                            'title': str(row.get('title', '')),
                                            'message': str(row.get('message', '')),
                                        }, ensure_ascii=False),
                                        'keywords': None,
                                        'target_audience': str(row.get('target_audience', '')),
                                        'tone': str(row.get('tone', '')),
                                        'reference_text': None,
                                        'send_date': str(row.get('send_date', '')),
                                        'impression_count': int(row.get('impression_count', 0)),
                                        'click_count': int(row.get('click_count', 0)),
                                        'ctr': float(row.get('ctr', 0.0)),
                                        'conversion_count': int(row.get('conversion_count', 0)),
                                        'conversion_rate': float(row.get('conversion_rate', 0.0)),
                                        'trend_keywords': None,
                                        'is_ai_generated': bool(row.get('is_ai_generated', False)),
                                    }
                                    
                                    if logic.add_marketing_copy(copy_data):
                                        success_count += 1
                                    else:
                                        error_count += 1
                                        
                                except Exception as e:
                                    error_count += 1
                                    continue
                            
                            st.success(f"✅ {success_count}개 문구가 성공적으로 추가되었습니다.")
                            if error_count > 0:
                                st.warning(f"⚠️ {error_count}개 문구에서 오류가 발생했습니다.")
                    
                    else:
                        # CSV 파일 처리
                        try:
                            df = pd.read_csv(io.StringIO(file_content), header=None)
                        except UnicodeDecodeError:
                            df = pd.read_csv(io.StringIO(uploaded_file.read().decode('cp949')), header=None)
                        
                        # 팀명을 팀 ID로 매핑하는 딕셔너리
                        team_mapping = {
                            '그로스마케팅': 1, '여행서비스TFT': 2, '버티컬마케팅팀': 3, '마케팅운영팀': 4,
                            '스포츠레저팀': 5, '패션팀': 6, '브랜드뷰티팀': 7, '리빙팀': 8, '식품팀': 9,
                            '유아동패션팀': 10, 'L.TOWN팀': 11, '제휴서비스상품팀': 12, 'b tft': 13,
                            '명품잡화팀': 14, '브랜드패션팀': 15, 'B2B팀': 16, '디지털가전팀': 17
                        }
                        
                        # 데이터 변환 및 저장
                        success_count = 0
                        error_count = 0
                        
                        for _, row in df.iterrows():
                            try:
                                # 컬럼 위치 기반으로 데이터 추출
                                team_name = str(row.iloc[6]).strip() if len(row) > 6 else ''
                                team_id = team_mapping.get(team_name, 1)
                                
                                title = str(row.iloc[9]).strip() if len(row) > 9 else ''
                                message = str(row.iloc[10]).strip() if len(row) > 10 else ''
                                target_audience = str(row.iloc[20]).strip() if len(row) > 20 else ''
                                
                                # 날짜 변환 함수
                                def convert_date(date_str):
                                    try:
                                        if pd.isna(date_str) or date_str == '':
                                            return None
                                        date_str = str(date_str).strip()
                                        if '(' in date_str and ')' in date_str:
                                            date_part = date_str.split('(')[0]
                                            month, day = date_part.split('/')
                                            return f"2025{month.zfill(2)}{day.zfill(2)}"
                                        return None
                                    except:
                                        return None
                                
                                send_date = convert_date(row.iloc[3]) if len(row) > 3 else None
                                
                                # 숫자 데이터 처리
                                def safe_int(value, default=0):
                                    try:
                                        if pd.isna(value) or value == '':
                                            return default
                                        return int(float(str(value).replace(',', '')))
                                    except:
                                        return default
                                
                                def safe_float(value, default=0.0):
                                    try:
                                        if pd.isna(value) or value == '':
                                            return default
                                        return float(str(value).replace(',', '').replace('%', ''))
                                    except:
                                        return default
                                
                                impression_count = safe_int(row.iloc[12]) if len(row) > 12 else 0
                                click_count = safe_int(row.iloc[14]) if len(row) > 14 else 0
                                ctr = safe_float(row.iloc[15]) / 100 if len(row) > 15 else 0.0
                                conversion_count = safe_int(row.iloc[16]) if len(row) > 16 else 0
                                conversion_rate = safe_float(row.iloc[17]) / 100 if len(row) > 17 else 0.0
                                
                                # 데이터 구성
                                copy_data = {
                                    'team_id': team_id,
                                    'channel': 'APP_PUSH',
                                    'content_data': json.dumps({
                                        'title': title,
                                        'message': message,
                                    }, ensure_ascii=False),
                                    'keywords': None,
                                    'target_audience': target_audience,
                                    'tone': '',
                                    'reference_text': None,
                                    'send_date': send_date,
                                    'impression_count': impression_count,
                                    'click_count': click_count,
                                    'ctr': ctr,
                                    'conversion_count': conversion_count,
                                    'conversion_rate': conversion_rate,
                                    'trend_keywords': None,
                                    'is_ai_generated': False,
                                }
                                
                                # 데이터베이스에 저장
                                if logic.add_marketing_copy(copy_data):
                                    success_count += 1
                                else:
                                    error_count += 1
                                    
                            except Exception as e:
                                error_count += 1
                                continue
                        
                        st.success(f"✅ {success_count}개 문구가 성공적으로 추가되었습니다.")
                        if error_count > 0:
                            st.warning(f"⚠️ {error_count}개 문구에서 오류가 발생했습니다.")
                
                except Exception as e:
                    st.error(f"❌ 업로드 중 오류가 발생했습니다: {str(e)}")
                    st.exception(e)
    
    with col2:
        if st.button("🔄 벡터 저장소 동기화", use_container_width=True):
            with st.spinner("벡터 저장소를 동기화하는 중..."):
                try:
                    logic = MarketingLogic()
                    logic.vector_store.sync_from_database()
                    
                    st.success("✅ 벡터 저장소 동기화가 완료되었습니다.")
                    
                except Exception as e:
                    st.error(f"❌ 동기화 중 오류가 발생했습니다: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)

# 파일 형식 가이드
st.subheader("📋 파일 형식 가이드")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📄 CSV 파일 형식
    **컬럼 구조:**
    - E열(4): 발송일자
    - F열(5): 발송시간  
    - G열(6): 팀명
    - H열(7): 카테고리/오퍼
    - I열(8): 행사명
    - J열(9): 메시지(제목)
    - K열(10): 메시지(내용)
    - L열(11): 발송통수
    - M열(12): 발송통수(성공)
    - N열(13): 발송성공률
    - O열(14): 오픈수
    - P열(15): 오픈율(%)
    - Q열(16): 구매자수
    - R열(17): 구매전환율(%)
    - S열(18): 판매매출
    - T열(19): UV
    - U열(20): 타겟
    - V열(21): 비고
    """)

with col2:
    st.markdown("""
    ### 📄 JSON 파일 형식
    **필수 필드:**
    ```json
    [
        {
            "team_id": 1,
            "channel": "APP_PUSH",
            "title": "문구 제목",
            "message": "문구 내용",
            "target_audience": "타겟 고객",
            "tone": "톤앤매너",
            "send_date": "20250101",
            "impression_count": 1000,
            "click_count": 50,
            "ctr": 0.05,
            "conversion_count": 5,
            "conversion_rate": 0.1,
            "is_ai_generated": false
        }
    ]
    ```
    """)

# 사이드바에 추가 정보
with st.sidebar:
    st.header("업로드 가이드")
    st.markdown("""
    ### 파일 업로드
    - CSV 또는 JSON 파일을 업로드할 수 있습니다
    - 파일 크기는 200MB 이하로 제한됩니다
    - 업로드 후 벡터 저장소 동기화를 권장합니다
    
    ### 데이터 형식
    - **CSV**: 헤더 없는 형식으로 처리됩니다
    - **JSON**: 배열 형태의 객체 리스트여야 합니다
    - 팀명은 자동으로 팀 ID로 변환됩니다
    
    ### 주의사항
    - 중복 데이터는 자동으로 처리됩니다
    - 필수 필드가 누락된 경우 오류가 발생할 수 있습니다
    - 대용량 파일의 경우 처리 시간이 오래 걸릴 수 있습니다
    """)
    
    # 업로드 통계 (예시)
    st.markdown("---")
    st.header("업로드 통계")
    st.markdown("""
    **이번 주 업로드:**
    - 총 파일 수: 12개
    - 성공: 11개
    - 실패: 1개
    
    **누적 통계:**
    - 총 문구 수: 1,234개
    - 평균 성공률: 95.2%
    """)
    
    # 지원되는 팀 목록
    st.markdown("---")
    st.header("지원 팀 목록")
    teams = [
        "그로스마케팅팀",
        "버티컬마케팅팀", 
        "마케팅운영팀",
        "식품팀",
        "여행서비스TFT",
        "리빙팀",
        "스포츠레저팀",
        "패션팀",
        "브랜드뷰티팀",
        "유아동패션팀",
        "명품잡화팀",
        "L.TOWN팀",
        "B2B팀",
        "제휴서비스상품팀",
        "브랜드패션팀",
        "디지털가전팀"
    ]
    
    for team in teams:
        st.write(f"• {team}")
