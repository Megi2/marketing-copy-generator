#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, pandas as pd
def read_auto(path: str, header_any: bool = True) -> pd.DataFrame:
    encs=("utf-8-sig","utf-8","cp949")
    if header_any:
        for e in encs:
            try: return pd.read_csv(path, encoding=e)
            except Exception: pass
    for e in encs:
        try: return pd.read_csv(path, encoding=e, header=None)
        except Exception: pass
    return pd.read_csv(path, encoding="utf-8", header=None, engine="python")
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--output",default="messages_only_new.csv")
    a=ap.parse_args()
    df=read_auto(a.input,True)
    if df.shape[1]<6: df=read_auto(a.input,False)
    if df.shape[1]<6: raise ValueError("F열(내용) 없음")
    ser=df.iloc[2:,5].astype(str).map(str.strip).replace({"":pd.NA}).dropna().reset_index(drop=True)
    ser.to_frame("내용").to_csv(a.output,index=False,encoding="utf-8-sig")
    print(f"완료: {a.output} (rows={len(ser)})")
if __name__=="__main__": main()