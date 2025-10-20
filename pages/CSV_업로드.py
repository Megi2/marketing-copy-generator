import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime
import re

# app 디렉토리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from db import get_trends_db, get_phrases_db
from core.vector_store import VectorStore

# 페이지 설정
st.set_page_config(
    page_title="CSV 업로드 및 DB 업데이트",
    page_icon="📊",
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
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .info-message {
        background: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 메인 헤더
st.markdown("""
<div class="main-header">
    <h1>📊 CSV 업로드 및 DB 업데이트</h1>
    <p>CSV 파일을 업로드하여 마케팅 데이터베이스를 업데이트합니다</p>
</div>
""", unsafe_allow_html=True)

def clean_str(x) -> str:
    """문자열 정리 - merge_rcs_with_keywords.py에서 가져옴"""
    BAD_STRINGS = {"nan", "none", "null", "nil", "-", "—", "–", ""}
    if pd.isna(x):
        return ""
    s = str(x).strip()
    return "" if s.lower() in BAD_STRINGS else s

def to_int(x) -> int:
    """정수 변환 - merge_rcs_with_keywords.py에서 가져옴"""
    BAD_STRINGS = {"nan", "none", "null", "nil", "-", "—", "–", ""}
    try:
        if pd.isna(x):
            return 0
        if isinstance(x, str):
            if x.strip().lower() in BAD_STRINGS:
                return 0
            x = x.replace(",", "").strip()
        return int(float(x))
    except Exception:
        return 0

def percent_to_ratio(v) -> float:
    """퍼센트를 비율로 변환 - merge_rcs_with_keywords.py에서 가져옴"""
    BAD_STRINGS = {"nan", "none", "null", "nil", "-", "—", "–", ""}
    try:
        if pd.isna(v):
            return 0.0
        if isinstance(v, str):
            if v.strip().lower() in BAD_STRINGS:
                return 0.0
            t = v.strip()
            has = t.endswith("%")
            t = t.replace("%", "").replace(",", "").strip()
            num = float(t)
            return num/100.0 if has or num > 1 else num
        num = float(v)
        return num/100.0 if num > 1 else num
    except Exception:
        return 0.0

def parse_send_date(s: str) -> str:
    """발송일 파싱 - merge_rcs_with_keywords.py에서 가져옴"""
    s = clean_str(s)
    if not s:
        return ""
    # If already 8 digits (YYYYMMDD format)
    if re.fullmatch(r"\d{8}", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    # Common separators
    m = re.search(r"(\d{2,4})[.\-/](\d{1,2})[.\-/](\d{1,2})", s)
    if m:
        y, mo, d = m.groups()
        y = int(y)
        if y < 100:
            y = 2000 + y  # 2-digit year -> 2000+YY
        return f"{y:04d}-{int(mo):02d}-{int(d):02d}"
    # Month/Day (assume unknown year -> prefix 0000)
    m2 = re.search(r"(\d{1,2})[.\-/](\d{1,2})", s)
    if m2:
        mo, d = m2.groups()
        return f"0000-{int(mo):02d}-{int(d):02d}"
    return ""

def parse_send_time(s: str) -> str:
    """발송시간 파싱 - merge_rcs_with_keywords.py에서 가져옴"""
    s = clean_str(s)
    if not s:
        return ""
    t = s.replace(" ", "")
    # Detect AM/PM or 오전/오후
    pm = False
    am = False
    if "오전" in t or t.upper().startswith("AM"):
        am = True
        t = t.replace("오전", "").replace("AM", "")
    if "오후" in t or t.upper().startswith("PM"):
        pm = True
        t = t.replace("오후", "").replace("PM", "")
    # Extract hour/minute
    h = m = None
    m1 = re.search(r"(\d{1,2})시(?:(\d{1,2})분?)?", t)
    if m1:
        h = int(m1.group(1))
        m = int(m1.group(2)) if m1.group(2) else 0
    else:
        m2 = re.search(r"(\d{1,2}):(\d{1,2})", t)
        if m2:
            h = int(m2.group(1)); m = int(m2.group(2))
        else:
            m3 = re.search(r"^(\d{1,2})$", t)
            if m3:
                h = int(m3.group(1)); m = 0
    if h is None:
        return ""
    if pm and h < 12:
        h += 12
    if am and h == 12:
        h = 0
    return f"{h:02d}{m:02d}"

def clean_numeric_value(value):
    """숫자 값에서 콤마와 공백 제거"""
    if pd.isna(value) or value == '':
        return 0
    if isinstance(value, str):
        # 콤마와 공백 제거
        cleaned = re.sub(r'[,\s]', '', str(value))
        # 숫자가 아닌 문자 제거 (%, 원 등)
        cleaned = re.sub(r'[^\d.-]', '', cleaned)
        try:
            return float(cleaned) if cleaned else 0
        except ValueError:
            return 0
    return float(value) if value else 0

def clean_percentage_value(value):
    """퍼센트 값 정리"""
    if pd.isna(value) or value == '':
        return 0
    if isinstance(value, str):
        # % 기호 제거
        cleaned = re.sub(r'%', '', str(value))
        try:
            return float(cleaned) / 100 if cleaned else 0
        except ValueError:
            return 0
    return float(value) if value else 0

# merge_simple_forloop.py에서 가져온 헬퍼 함수들
def percent_to_ratio(val) -> float:
    """퍼센트를 비율로 변환"""
    try:
        if pd.isna(val):
            return 0.0
        if isinstance(val, str):
            txt = val.strip()
            has_pct = txt.endswith("%")
            txt = txt.replace("%", "").replace(",", "").strip()
            num = float(txt)
            if has_pct or num > 1:
                return num / 100.0
            return num
        num = float(val)
        if num > 1:
            return num / 100.0
        return num
    except Exception:
        return 0.0

def convert_date(date_str) -> str:
    """8/31(일) -> 20250831 형식으로 변환"""
    try:
        if pd.isna(date_str) or date_str == '':
            return None
        date_str = str(date_str).strip()
        # 8/31(일) -> 20250831 형식으로 변환
        if '(' in date_str and ')' in date_str:
            date_part = date_str.split('(')[0]  # 8/31
            month, day = date_part.split('/')
            # 2025년으로 가정 (실제로는 현재 연도 사용 가능)
            return f"2025{month.zfill(2)}{day.zfill(2)}"
        return None
    except:
        return None

def to_int(x) -> int:
    """정수로 변환"""
    try:
        if pd.isna(x):
            return 0
        if isinstance(x, str):
            x = x.replace(",", "").strip()
        return int(float(x))
    except Exception:
        return 0

def clean_str(s) -> str:
    """문자열 정리"""
    if pd.isna(s):
        return ""
    return str(s).strip()

def parse_app_push_csv(df):
    """APP PUSH CSV 파일 파싱 - merge_simple_forloop.py 로직 참고"""
    data = []
    
    # merge_simple_forloop.py의 EXPECTED_COLS와 동일한 컬럼명 사용
    expected_columns = [
        "발송일자", "발송시간", "팀", "카테고리/오퍼", "행사명", "메세지(제목)", "메세지(내용)",
        "발송통수", "발송통수(성공)", "발송성공률", "오픈수", "오픈율 (%)", "구매자수", "구매전환율 (%)",
        "판매 매출 (원)", "UV", "타겟", "비고"
    ]
    
    # 컬럼명이 다르면 기본 컬럼명으로 설정
    if len(df.columns) >= len(expected_columns):
        df.columns = expected_columns[:len(df.columns)]
    
    # 팀 매핑 (merge_simple_forloop.py와 동일한 로직)
    teams = df["팀"].fillna("").astype(str).tolist()
    team_to_id = {}
    nxt = 1
    for t in teams:
        if t not in team_to_id:
            team_to_id[t] = nxt
            nxt += 1
    
    for index, row in df.iterrows():
        # 내용이 비어있으면 스킵
        message = clean_str(row.get('메세지(내용)', ''))
        if not message:
            continue
            
        # 제목이 비어있으면 스킵
        title = clean_str(row.get('메세지(제목)', ''))
        if not title:
            continue
        
        # 발송일자 파싱 (merge_simple_forloop.py의 convert_date 로직 사용)
        send_date = convert_date(row.get('발송일자', ''))
        if not send_date:
            continue
        
        # 데이터 구성 (merge_simple_forloop.py와 동일한 구조)
        item = {
            "team_id": team_to_id.get(row.get("팀"), 1),
            "channel": "APP_PUSH",
            "content_data": {
                "title": title,
                "message": message
            },
            "target_audience": clean_str(row.get('타겟', '')),
            "tone": "",
            "reference_text": None,
            "send_date": send_date,
            "send_time": "",  # APP PUSH는 시간 정보가 없음
            "impression_count": to_int(row.get('발송통수(성공)', 0)),
            "click_count": to_int(row.get('오픈수', 0)),
            "ctr": percent_to_ratio(row.get('오픈율 (%)', 0)),
            "conversion_count": to_int(row.get('구매자수', 0)),
            "conversion_rate": percent_to_ratio(row.get('구매전환율 (%)', 0)),
            "trend_keywords": None,
            "is_ai_generated": False
        }
        
        data.append(item)
    
    return data

def parse_rcs_csv(df):
    """RCS CSV 파일 파싱 - merge_rcs_with_keywords.py 로직 참고"""
    data = []
    
    # merge_rcs_with_keywords.py의 로직을 참고하여 컬럼 매핑
    # 원본 파일에서는 C~P 컬럼 (2~15 인덱스)을 사용
    # 컬럼명을 정확히 매핑
    expected_columns = [
        "발송일", "시간", "브랜드", "내용", "버튼명", "타겟",
        "발송성공수", "클릭 수", "UV", "유입율", "M", "N", "구매자수", "구매전환율"
    ]
    
    # 컬럼명이 다르면 기본 컬럼명으로 설정
    if len(df.columns) >= 14:
        df.columns = expected_columns[:len(df.columns)]
    
    for index, row in df.iterrows():
        # 내용이 비어있으면 스킵
        content = clean_str(row.get('내용', ''))
        if not content:
            continue
        
        # 발송일자 파싱 (merge_rcs_with_keywords.py의 parse_send_date 로직 사용)
        send_date = parse_send_date(row.get('발송일', ''))
        
        # 발송시간 파싱 (merge_rcs_with_keywords.py의 parse_send_time 로직 사용)
        send_time = parse_send_time(row.get('시간', ''))
        
        # 데이터 구성
        item = {
            "team_id": 1,  # 고정값
            "channel": "RCS",
            "content_data": {
                "message": content,
                "button": clean_str(row.get('버튼명', ''))
            },
            "target_audience": clean_str(row.get('타겟', '')),
            "tone": "",
            "reference_text": None,
            "send_date": send_date,
            "send_time": send_time,
            "impression_count": to_int(row.get('발송성공수', 0)),
            "click_count": to_int(row.get('클릭 수', 0)),
            "ctr": percent_to_ratio(row.get('유입율', 0)),
            "conversion_count": to_int(row.get('구매자수', 0)),
            "conversion_rate": percent_to_ratio(row.get('구매전환율', 0)),
            "trend_keywords": None,
            "is_ai_generated": False
        }
        
        data.append(item)
    
    return data

def save_json_file(data, filename):
    """JSON 파일 저장"""
    json_path = os.path.join('app', 'data', 'json', filename)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return json_path

def update_database_from_json(json_data, channel_type):
    """JSON 데이터를 기반으로 데이터베이스 업데이트 (중복 방지)"""
    conn = get_phrases_db()
    cursor = conn.cursor()
    
    # send_time 컬럼 존재 여부 확인
    cursor.execute("PRAGMA table_info(marketing_copies)")
    columns = [column[1] for column in cursor.fetchall()]
    has_send_time = 'send_time' in columns
    
    updated_count = 0
    skipped_count = 0
    
    for item in json_data:
        try:
            # 중복 체크: team_id, channel, content_data, send_date가 동일한 데이터가 있는지 확인
            content_json = json.dumps(item['content_data'], ensure_ascii=False, sort_keys=True)
            
            if has_send_time:
                cursor.execute("""
                    SELECT copy_id FROM marketing_copies 
                    WHERE team_id = ? AND channel = ? AND content_data = ? AND send_date = ? AND send_time = ?
                """, (
                    item['team_id'],
                    item['channel'],
                    content_json,
                    item.get('send_date', ''),
                    item.get('send_time', '')
                ))
            else:
                cursor.execute("""
                    SELECT copy_id FROM marketing_copies 
                    WHERE team_id = ? AND channel = ? AND content_data = ? AND send_date = ?
                """, (
                    item['team_id'],
                    item['channel'],
                    content_json,
                    item.get('send_date', '')
                ))
            
            existing = cursor.fetchone()
            if existing:
                skipped_count += 1
                continue
            if channel_type == 'app_push':
                # APP PUSH 데이터 삽입
                if has_send_time:
                    cursor.execute("""
                        INSERT OR REPLACE INTO marketing_copies 
                        (team_id, channel, content_data, target_audience, tone, reference_text, 
                         send_date, send_time, impression_count, click_count, ctr, 
                         conversion_count, conversion_rate, trend_keywords, is_ai_generated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['team_id'],
                        item['channel'],
                        json.dumps(item['content_data'], ensure_ascii=False),
                        item['target_audience'],
                        item['tone'],
                        item['reference_text'],
                        item.get('send_date', ''),
                        item.get('send_time', ''),
                        item['impression_count'],
                        item['click_count'],
                        item['ctr'],
                        item['conversion_count'],
                        item['conversion_rate'],
                        json.dumps(item['trend_keywords']) if item['trend_keywords'] else None,
                        item['is_ai_generated']
                    ))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO marketing_copies 
                        (team_id, channel, content_data, target_audience, tone, reference_text, 
                         send_date, impression_count, click_count, ctr, 
                         conversion_count, conversion_rate, trend_keywords, is_ai_generated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['team_id'],
                        item['channel'],
                        json.dumps(item['content_data'], ensure_ascii=False),
                        item['target_audience'],
                        item['tone'],
                        item['reference_text'],
                        item.get('send_date', ''),
                        item['impression_count'],
                        item['click_count'],
                        item['ctr'],
                        item['conversion_count'],
                        item['conversion_rate'],
                        json.dumps(item['trend_keywords']) if item['trend_keywords'] else None,
                        item['is_ai_generated']
                    ))
            else:
                # RCS 데이터 삽입
                if has_send_time:
                    cursor.execute("""
                        INSERT OR REPLACE INTO marketing_copies 
                        (team_id, channel, content_data, target_audience, tone, reference_text, 
                         send_date, send_time, impression_count, click_count, ctr, 
                         conversion_count, conversion_rate, trend_keywords, is_ai_generated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['team_id'],
                        item['channel'],
                        json.dumps(item['content_data'], ensure_ascii=False),
                        item['target_audience'],
                        item['tone'],
                        item['reference_text'],
                        item['send_date'],
                        item['send_time'],
                        item['impression_count'],
                        item['click_count'],
                        item['ctr'],
                        item['conversion_count'],
                        item['conversion_rate'],
                        json.dumps(item['trend_keywords']) if item['trend_keywords'] else None,
                        item['is_ai_generated']
                    ))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO marketing_copies 
                        (team_id, channel, content_data, target_audience, tone, reference_text, 
                         send_date, impression_count, click_count, ctr, 
                         conversion_count, conversion_rate, trend_keywords, is_ai_generated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['team_id'],
                        item['channel'],
                        json.dumps(item['content_data'], ensure_ascii=False),
                        item['target_audience'],
                        item['tone'],
                        item['reference_text'],
                        item['send_date'],
                        item['impression_count'],
                        item['click_count'],
                        item['ctr'],
                        item['conversion_count'],
                        item['conversion_rate'],
                        json.dumps(item['trend_keywords']) if item['trend_keywords'] else None,
                        item['is_ai_generated']
                    ))
            
            updated_count += 1
            
        except Exception as e:
            st.error(f"데이터베이스 업데이트 중 오류: {str(e)}")
            continue
    
    conn.commit()
    conn.close()
    
    return updated_count, skipped_count

def update_vector_store():
    """벡터 스토어 업데이트"""
    try:
        vector_store = VectorStore()
        vector_store.recreate_vector_store()
        return True
    except Exception as e:
        st.error(f"벡터 스토어 업데이트 중 오류: {str(e)}")
        return False

# 메인 폼
st.markdown('<div class="form-container">', unsafe_allow_html=True)

st.subheader("CSV 파일 업로드")

# 파일 타입 선택
file_type = st.selectbox(
    "파일 타입 선택",
    ["APP PUSH", "RCS"],
    help="업로드할 CSV 파일의 타입을 선택하세요"
)

# 파일 업로드
uploaded_file = st.file_uploader(
    f"{file_type} CSV 파일을 업로드하세요",
    type=['csv'],
    help=f"{file_type} 형식의 CSV 파일을 업로드하세요"
)

if uploaded_file is not None:
    try:
        # CSV 파일 읽기
        if file_type == "APP PUSH":
            # APP PUSH는 전체 데이터를 읽도록 수정 (기존 제한 제거)
            # 4행부터 끝까지, E~V열 (iloc 3:, 4:22)
            df_all = pd.read_csv(uploaded_file, header=None, encoding='utf-8')
            df = df_all.iloc[3:, 4:22].copy()  # 3행부터 끝까지, E~V열
            
            # merge_simple_forloop.py의 EXPECTED_COLS와 동일한 컬럼명 사용
            expected_columns = [
                "발송일자", "발송시간", "팀", "카테고리/오퍼", "행사명", "메세지(제목)", "메세지(내용)",
                "발송통수", "발송통수(성공)", "발송성공률", "오픈수", "오픈율 (%)", "구매자수", "구매전환율 (%)",
                "판매 매출 (원)", "UV", "타겟", "비고"
            ]
            df.columns = expected_columns
            
            # null 값이 있는 행 필터링 (중요한 컬럼들 체크)
            important_cols = ["발송일자", "팀", "메세지(제목)", "메세지(내용)", "발송통수(성공)", "오픈수"]
            st.info(f"필터링 전 원본 데이터: {len(df)}개 레코드")
            
            # 중요 컬럼들 중 하나라도 null이면 제외
            df_filtered = df.dropna(subset=important_cols)
            st.info(f"null 값 필터링 후: {len(df_filtered)}개 레코드")
            df = df_filtered
        else:
            # RCS는 헤더 없이 읽고 3행부터 데이터 시작 (merge_rcs_with_keywords.py 참고)
            df = pd.read_csv(uploaded_file, header=None, encoding='utf-8')
            # 3행부터 데이터 시작 (인덱스 2부터)
            df = df.iloc[2:].reset_index(drop=True)
            # C~P 컬럼 (2~15 인덱스) 사용
            if df.shape[1] >= 16:
                df = df.iloc[:, 2:16]
            elif df.shape[1] >= 14:
                df = df.iloc[:, 2:16] if df.shape[1] >= 16 else df.iloc[:, 2:]
            else:
                # 컬럼이 부족하면 빈 컬럼 추가
                for i in range(df.shape[1], 16):
                    df[i] = ""
                df = df.iloc[:, 2:16]
        
        st.success(f"CSV 파일이 성공적으로 읽혔습니다. 총 {len(df)} 행의 데이터가 있습니다.")
        
        # 데이터 미리보기
        with st.expander("데이터 미리보기", expanded=False):
            st.dataframe(df.head(10))
        
        # 컬럼 정보 표시
        with st.expander("컬럼 정보", expanded=False):
            st.write("**발견된 컬럼들:**")
            for i, col in enumerate(df.columns):
                st.write(f"{i+1}. {col}")
            
            # 필수 컬럼 확인
            if file_type == "APP PUSH":
                st.write("\n**컬럼 구조 (merge_simple_forloop.py 기준):**")
                st.write("발송일자, 발송시간, 팀, 카테고리/오퍼, 행사명, 메세지(제목), 메세지(내용), 발송통수, 발송통수(성공), 발송성공률, 오픈수, 오픈율 (%), 구매자수, 구매전환율 (%), 판매 매출 (원), UV, 타겟, 비고")
                st.write("✅ 제목 컬럼: 메세지(제목)")
                st.write("✅ 내용 컬럼: 메세지(내용)")
            else:
                # RCS는 고정된 컬럼 구조 사용
                st.write("\n**컬럼 구조:**")
                st.write("발송일, 시간, 브랜드, 내용, 버튼명, 타겟, 발송성공수, 클릭 수, UV, 유입율, M, N, 구매자수, 구매전환율")
                st.write("✅ 내용 컬럼: 4번째 컬럼 (내용)")
        
        # 처리 버튼
        if st.button("📊 데이터 처리 및 DB 업데이트", type="primary"):
            with st.spinner("데이터를 처리하고 있습니다..."):
                try:
                    # CSV 파싱
                    if file_type == "APP PUSH":
                        json_data = parse_app_push_csv(df)
                        filename = f"app_push_{datetime.now().strftime('%b').upper()}.json"
                    else:
                        json_data = parse_rcs_csv(df)
                        filename = f"rcs_merged.json"
                    
                    st.info(f"파싱된 데이터: {len(json_data)} 개 항목")
                    
                    # 데이터베이스 업데이트
                    updated_count, skipped_count = update_database_from_json(json_data, file_type.lower().replace(' ', '_'))
                    st.success(f"데이터베이스가 업데이트되었습니다: {updated_count} 개 항목 추가, {skipped_count} 개 중복 스킵")
                    
                    # 벡터 스토어 업데이트
                    with st.spinner("벡터 스토어를 업데이트하고 있습니다..."):
                        if update_vector_store():
                            st.success("벡터 스토어가 성공적으로 업데이트되었습니다!")
                            
                            # 성공 알림 및 파일 초기화
                            st.balloons()
                            st.success("🎉 모든 처리가 완료되었습니다!")
                            
                            # 파일 업로드 초기화
                            st.rerun()
                        else:
                            st.error("벡터 스토어 업데이트에 실패했습니다.")
                    
                except Exception as e:
                    st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")
                    st.exception(e)
    
    except Exception as e:
        st.error(f"CSV 파일 읽기 중 오류가 발생했습니다: {str(e)}")
        st.exception(e)

st.markdown('</div>', unsafe_allow_html=True)

# 사이드바 정보
with st.sidebar:
    st.header("📋 사용 가이드")
    
    st.markdown("""
    ### APP PUSH 파일 형식 
    - 앱푸시 발송 실적 관리.excl 파일
    - 파일 > 내보내기 > CSV UTF-8로 다운로드
    
    ### RCS 파일 형식
    - [RCS]발송_통합실적관리.excl 파일
    - 파일 > 내보내기 > CSV UTF-8로 다운로드

    ### 주의 사항
    - 본 과정은 시간이 다소 소요됩니다. 진행 중 화면을 벗어나지 마세요.
    - 혹여나 데이터가 중복으로 업로드 되었다고 생각되면 알려주세요.(AI-TFT 전진하)
    """)
    
    st.markdown("---")
    st.header("📊 현재 상태")
    
    # 데이터베이스 상태 확인
    try:
        conn = get_phrases_db()
        cursor = conn.cursor()
        
        # 총 데이터 수
        cursor.execute("SELECT COUNT(*) FROM marketing_copies")
        total_count = cursor.fetchone()[0]
        
        # 채널별 데이터 수
        cursor.execute("SELECT channel, COUNT(*) FROM marketing_copies GROUP BY channel")
        channel_counts = cursor.fetchall()
        
        st.write(f"**총 데이터:** {total_count:,} 개")
        
        for channel, count in channel_counts:
            st.write(f"**{channel}:** {count:,} 개")
        
        conn.close()
        
    except Exception as e:
        st.error(f"데이터베이스 상태 확인 중 오류: {str(e)}")
