# 임시 디버깅 - 확인 후 제거
import streamlit as st
from pykrx import stock
from datetime import datetime, timedelta

st.write("=== pykrx 디버깅 ===")
for i in range(10):
    date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
    try:
        df = stock.get_market_cap_by_ticker(date, market="KOSPI")
        st.write(f"{date}: shape={df.shape}, columns={list(df.columns)}, empty={df.empty}")
        if not df.empty:
            st.write(df.head(2))
            break
    except Exception as e:
        st.write(f"{date}: 에러 - {e}")
