st.write("=== pykrx 디버깅 ===")
date = "20260309"
try:
    df = stock.get_market_cap_by_ticker(date, market="KOSPI")
    st.write(f"shape: {df.shape}")
    st.write(f"columns: {list(df.columns)}")
    st.write(f"index name: {df.index.name}")
    st.write(f"dtypes: {df.dtypes}")
    st.write(df.head(3))
except Exception as e:
    st.write(f"에러: {e}")
    import traceback
    st.write(traceback.format_exc())
