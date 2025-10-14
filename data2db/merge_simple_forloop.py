#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json
import pandas as pd
from typing import Any, Dict, List, Optional

def percent_to_ratio(val) -> float:
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
    try:
        if pd.isna(x):
            return 0
        if isinstance(x, str):
            x = x.replace(",", "").strip()
        return int(float(x))
    except Exception:
        return 0
EXPECTED_COLS = [
    "발송일자","발송시간","팀","카테고리/오퍼","행사명","메세지(제목)","메세지(내용)",
    "발송통수","발송통수(성공)","발송성공률","오픈수","오픈율 (%)","구매자수","구매전환율 (%)",
    "판매 매출 (원)","UV","타겟","비고"
]

def read_no_header(path: str) -> pd.DataFrame:
    for enc in ("utf-8-sig","utf-8","cp949"):
        try:
            return pd.read_csv(path, header=None, encoding=enc)
        except Exception:
            pass
    return pd.read_csv(path, header=None, encoding="utf-8", engine="python")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True, help="원본 CSV (헤더 없음)")
    ap.add_argument("--mk", required=True, help="메시지-키워드 CSV (헤더 없음, A=메세지 B=키워드)")
    ap.add_argument("--output", default="merged_simple_forloop.json", help="출력 JSON 경로")
    args = ap.parse_args()

    # 1) 원본: 4~841행, E~V열
    df_all = read_no_header(args.original)
    df = df_all.iloc[3:841, 4:22].copy()  # 1-based 4..841 → iloc 3..840, cols E..V → 4..21
    df.columns = EXPECTED_COLS

    # 2) 메시지-키워드: 첫 두 컬럼 사용
    mk = read_no_header(args.mk).iloc[:, :2].copy()
    mk.columns = ["message", "keywords_raw"]
    mk["message"] = mk["message"].astype(str).str.strip()
    mk["keywords_raw"] = mk["keywords_raw"].astype(str).str.strip()
    
    # 2-1) 메시지별로 키워드 그룹화 (중복 방지)
    print(f"원본 메시지-키워드: {len(mk)}개 레코드")
    mk_grouped = mk.groupby("message")["keywords_raw"].apply(
        lambda x: list(set([kw.strip() for kw in x if kw.strip()]))
    ).reset_index()
    mk_grouped.columns = ["message", "keywords_list"]
    print(f"그룹화 후: {len(mk_grouped)}개 고유 메시지")

    # 3) LEFT JOIN on message text (이제 중복 없음)
    base = df.copy()
    base["메세지(내용)"] = base["메세지(내용)"].astype(str).str.strip()
    print(f"원본 실적 데이터: {len(base)}개 레코드")
    merged = pd.merge(
        base,
        mk_grouped,
        left_on="메세지(내용)",
        right_on="message",
        how="left",
        suffixes=("", "_mk")
    )
    print(f"머지 후: {len(merged)}개 레코드")

    teams = merged["팀"].fillna("").astype(str).tolist()
    team_to_id: Dict[str, int] = {}
    nxt = 1
    for t in teams:
        if t not in team_to_id:
            team_to_id[t] = nxt
            nxt += 1
    # 4) keywords 처리 (이미 리스트로 그룹화됨)
    def get_keywords(keywords_list):
        if isinstance(keywords_list, list):
            return keywords_list
        elif isinstance(keywords_list, str) and keywords_list.strip():
            return [p.strip() for p in keywords_list.split(",") if p.strip()]
        else:
            return []

    # 5) Build list[dict] explicitly via for-loop
    records = []
    print(len(merged))
    for _, row in merged.iterrows():
        rec = {
            "team_id": team_to_id.get(row.get("팀"), 0),
            "channel": "app_push",
            "contents" :{
            "title": row.get("메세지(제목)"),
            "message": row.get("메세지(내용)"),
            },
            "keywords": get_keywords(row.get("keywords_list")),
            "target_audience": str(row.get("타겟") or "").strip(),
            "tone": "",
            "reference_text": None,
            "send_date": convert_date(row.get("발송일자")),
            "impression_count": to_int(row.get("발송통수(성공)")),
            "click_count": to_int(row.get("오픈수")),
            "ctr": percent_to_ratio(row.get("오픈율 (%)")),
            "conversion_count": to_int(row.get("구매자수")),
            "conversion_rate": percent_to_ratio(row.get("구매전환율 (%)")),
            "trend_keywords": None,
            "is_ai_generated": False,
        }
        records.append(rec)

    # 6) Save JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"완료: {args.output} (records={len(records)})")

if __name__ == "__main__":
    main()
