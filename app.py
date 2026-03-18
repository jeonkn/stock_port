import sys, types, os

# pkg_resources 패치
try:
    import pkg_resources
except ModuleNotFoundError:
    mod = types.ModuleType("pkg_resources")
    def _resource_filename(package, resource):
        import importlib.util
        spec = importlib.util.find_spec(package)
        if spec and spec.origin:
            return os.path.join(os.path.dirname(spec.origin), resource)
        return resource
    mod.resource_filename = _resource_filename
    mod.require = lambda s: []
    mod.working_set = []
    sys.modules["pkg_resources"] = mod

# pykrx get_market_cap_by_ticker 몽키패치
from pykrx.stock import market as _market_module
import pandas as pd
from datetime import datetime, timedelta

_original_fetch = _market_module.MKD30040

class _PatchedMKD30040(_market_module.MKD30040):
    def fetch(self, date, market):
        df = super().fetch(date, market)
        # 영문 컬럼명 → 한국어로 매핑
        col_map = {
            'ISU_SRT_CD': '종목코드',
            'MKT_CLSS_TP_CD': '시장구분',
            'TDD_CLSPRC': '종가',
            'MKTCAP': '시가총액',
            'ACC_TRDVOL': '거래량',
            'ACC_TRDVAL': '거래대금',
            'LIST_SHRS': '상장주식수',
        }
        # 실제 컬럼 중 매핑 가능한 것만 변환
        rename = {k: v for k, v in col_map.items() if k in df.columns}
        if rename:
            df = df.rename(columns=rename)
        return df

_market_module.MKD30040 = _PatchedMKD30040

import streamlit as st
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
