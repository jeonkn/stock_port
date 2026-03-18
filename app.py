# 임시 디버깅 - 확인 후 제거
import streamlit as st
from pykrx import stock
from datetime import datetime, timedelta

st.write("=== 원본 컬럼 확인 ===")
from pykrx.stock.market.ticker import MKD30040
date = "20260309"
try:
    fetcher = MKD30040()
    raw = fetcher.fetch(date, "KOSPI")
    st.write(f"shape: {raw.shape}")
    st.write(f"columns: {list(raw.columns)}")
    st.write(raw.head(3))
except Exception as e:
    import traceback
    st.write(traceback.format_exc())
