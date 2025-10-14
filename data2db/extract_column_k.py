#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV에서 K열(메세지(내용))만 분리해 1컬럼 CSV로 저장하는 스크립트.

기본 가정
- 파일명: 앱푸시 발송 실적 관리(8월).csv (아무 CSV에도 사용 가능)
- 데이터는 4행부터 시작 → 상단 3행은 스킵
- K열은 0-인덱스 기준 10번째 컬럼
- 컬럼명이 '메세지(내용)' 또는 '메시지(내용)'이면 이름 기반으로 우선 선택

사용 예:
    python extract_column_k.py \
        --input "앱푸시 발송 실적 관리(8월).csv" \
        --output "messages_only.csv"

옵션:
    --start-row 4      # 1-기준 시작 행(기본 4)
    --end-row 841      # 1-기준 마지막 행(미지정 시 파일 끝까지)
    --colname "message"  # 출력 컬럼명(기본: message)
"""

import argparse
import sys
from typing import Optional

import pandas as pd


def read_csv_auto(path: str) -> pd.DataFrame:
    last_err: Optional[Exception] = None
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"CSV 읽기 실패: {last_err}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="입력 CSV 경로")
    p.add_argument("--output", default="messages_only.csv", help="출력 CSV 경로 (기본: messages_only.csv)")
    p.add_argument("--start-row", type=int, default=4, help="1-기준 시작 행 (기본: 4)")
    p.add_argument("--end-row", type=int, default=None, help="1-기준 마지막 행 (기본: 파일 끝)")
    p.add_argument("--colname", default="message", help="출력 컬럼명 (기본: message)")
    args = p.parse_args()

    df = read_csv_auto(args.input)

    # 컬럼 이름으로 우선 탐색
    msg_col = None
    for c in df.columns:
        cs = str(c).strip()
        if cs in ("메세지(내용)", "메시지(내용)"):
            msg_col = c
            break

    # 없으면 K열(1-기준 11번째 → 0-기준 10번째)
    if msg_col is None:
        if df.shape[1] < 11:
            raise ValueError("CSV 컬럼 수가 11개 미만이라 K열을 선택할 수 없습니다.")
        msg_col = df.columns[10]

    # 행 슬라이싱: 1-기준을 0-기준으로 변환
    start_idx = max(args.start_row - 1, 0)
    end_idx = args.end_row - 1 if args.end_row is not None else None

    # 헤더가 이미 분리되어 있으므로, 단순 위치 기반 슬라이싱
    df_slice = df.iloc[start_idx:end_idx, [df.columns.get_loc(msg_col)]].copy()

    # 컬럼명 정규화 및 공백/결측 처리
    df_slice.columns = [args.colname]
    df_slice[args.colname] = (
        df_slice[args.colname]
        .astype(str)
        .map(lambda s: s.strip())
    )
    # 완전 공백 행 제거
    df_slice = df_slice.replace({"": pd.NA}).dropna(how="all")

    # 저장 (엑셀 호환을 위해 UTF-8-SIG)
    df_slice.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"완료: {args.output} (rows={len(df_slice)})")


if __name__ == "__main__":
    main()
