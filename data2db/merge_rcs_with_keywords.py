#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json, os, re
import pandas as pd

BAD_STRINGS = {"nan","none","null","nil","-","—","–",""}

def read_no_header(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig","utf-8","cp949","utf-8"):
        try:
            return pd.read_csv(path, header=None, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path, header=None, encoding="utf-8", engine="python")

def read_keywords_csv(path: str) -> pd.DataFrame:
    # Try with header first
    df = None
    for enc in ("utf-8-sig","utf-8","cp949","utf-8"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        # headerless fallback
        df = read_no_header(path)
    # Find columns
    msg_col = None; kw_col = None
    for c in df.columns:
        name = str(c).strip()
        lname = name.lower()
        if name in ("원본 문구","본문","내용") or lname in ("message","text","content"):
            msg_col = c
        if name in ("키워드","Keywords","keywords"):
            kw_col = c
    if msg_col is None or kw_col is None:
        # fallback to first two columns
        msg_col = df.columns[0]
        kw_col = df.columns[1] if df.shape[1] > 1 else df.columns[0]
    out = df[[msg_col, kw_col]].copy()
    out.columns = ["원본 문구","키워드"]
    out["원본 문구"] = out["원본 문구"].astype(str).str.strip()
    out["키워드"] = out["키워드"].astype(str).str.strip()
    # drop empty/invalid message rows in keywords CSV as well
    out = out[~out["원본 문구"].str.strip().str.lower().isin(BAD_STRINGS)].reset_index(drop=True)
    return out

def clean_str(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).strip()
    return "" if s.lower() in BAD_STRINGS else s

def to_int(x) -> int:
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
    try:
        if pd.isna(v):
            return 0.0
        if isinstance(v, str):
            if v.strip().lower() in BAD_STRINGS:
                return 0.0
            t = v.strip()
            has = t.endswith("%")
            t = t.replace("%","").replace(",","").strip()
            num = float(t)
            return num/100.0 if has or num>1 else num
        num = float(v)
        return num/100.0 if num>1 else num
    except Exception:
        return 0.0

def split_keywords(s: str):
    if not isinstance(s, str):
        return []
    s = s.strip()
    if not s or s.lower() in BAD_STRINGS:
        return []
    parts = [p.strip() for p in s.split(",")]
    parts = [p for p in parts if p and p.lower() not in BAD_STRINGS]
    # dedup preserve order
    seen=set(); out=[]
    for p in parts:
        if p not in seen:
            seen.add(p); out.append(p)
    return out

def parse_send_date(s: str) -> str:
    """Return YYYY-MM-DD from strings like '25.08.01', '2025-08-01', '8/1', '20250801'"""
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
    """Return HHmm from strings like '10시 00분', '오후 3시 5분', '10:00', 'PM 3:05'"""
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True, help="원본 CSV 경로 (헤더 없음 가정, C..P, 3행부터)")
    ap.add_argument("--keywords", required=True, help="키워드 CSV 경로 (원본 문구, 키워드)")
    ap.add_argument("--output", default="rcs_merged.json", help="출력 JSON 경로")
    ap.add_argument("--start-row", type=int, default=3, help="1-기준 시작 행 (기본: 3)")
    args = ap.parse_args()

    # 1) Original slice rows/cols
    df_all = read_no_header(args.original)
    start_idx = max(args.start_row - 1, 0)
    if df_all.shape[1] < 16:
        # pad to at least P column
        for _ in range(16 - df_all.shape[1]):
            df_all[df_all.shape[1]] = ""
    sub = df_all.iloc[start_idx:, 2:16].copy().reset_index(drop=True)
    # Assign names for clarity (C..P)
    sub.columns = [
        "발송일","시간","브랜드","내용","버튼명","타겟",
        "발송성공수","클릭 수","UV","유입율","M","N","구매자수","구매전환율"
    ]

    # Sanitize early (avoid 'nan' strings)
    for col in sub.columns:
        sub[col] = sub[col].apply(clean_str)

    # Parse send_date/time
    sub["send_date"] = sub["발송일"].map(parse_send_date)
    sub["send_time"] = sub["시간"].map(parse_send_time)

    # 2) Keywords
    kw = read_keywords_csv(args.keywords)

    # 3) Join on content
    sub["내용"] = sub["내용"].apply(clean_str)
    kw["원본 문구"] = kw["원본 문구"].apply(clean_str)
    
    # 키워드 데이터 처리 옵션
    print(f"키워드 데이터 원본 길이: {len(kw)}")
    
    # 옵션 1: 중복 제거 (첫 번째 키워드만 유지)
    kw_dedup = kw.drop_duplicates(subset=["원본 문구"], keep="first")
    print(f"중복 제거 후 길이: {len(kw_dedup)}")
    
    # 옵션 2: 키워드 합치기 (여러 키워드를 하나로 합치기)
    # kw_grouped = kw.groupby("원본 문구")["키워드"].apply(lambda x: ", ".join(x.unique())).reset_index()
    # print(f"키워드 합친 후 길이: {len(kw_grouped)}")
    
    print(f"문구 데이터 길이: {len(sub)}")
    merged = pd.merge(
        sub,
        kw_dedup,  # 또는 kw_grouped 사용
        left_on="내용",
        right_on="원본 문구",
        how="left"
    )
    print(f"머지 후 길이: {len(merged)}")
    # Drop rows where message/content is blank after cleaning
    merged["내용"] = merged["내용"].apply(clean_str)
    merged = merged[merged["내용"] != ""].reset_index(drop=True)

    # 4) team_id fixed to 1
    FIXED_TEAM_ID = 1

    records = []
    for _, r in merged.iterrows():
        kws = ", ".join(split_keywords(clean_str(r.get("키워드"))))
        rec = {
            "team_id": FIXED_TEAM_ID,
            "channel": "RCS",
            "content_data": {
                "message": clean_str(r.get("내용")),
                "button": clean_str(r.get("버튼명"))
            },
            "keywords": kws,
            "target_audience": clean_str(r.get("타겟")),
            "tone": "",
            "reference_text": None,
            "send_date": r.get("send_date") or "",
            "send_time": r.get("send_time") or "",
            "impression_count": to_int(r.get("발송성공수")),
            "click_count": to_int(r.get("클릭 수")),
            "ctr": percent_to_ratio(r.get("유입율")),
            "conversion_count": to_int(r.get("구매자수")),
            "conversion_rate": percent_to_ratio(r.get("구매전환율")),
            "trend_keywords": None,
            "is_ai_generated": False
        }
        records.append(rec)

    # 6) Write JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"JSON 저장: {args.output} (records={len(records)})")

if __name__ == "__main__":
    main()
