import streamlit as st
import pandas as pd
from pykrx import stock
import numpy as np
from datetime import datetime, timedelta
import time

# 페이지 설정
st.set_page_config(page_title="한국 주식 기술적 분석", layout="wide")

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_market_cap_top50():
    """시총 상위 50개 종목 조회"""
    try:
        today = datetime.now().strftime("%Y%m%d")
        # 코스피 + 코스닥 전체 종목의 시가총액 조회
        kospi_cap = stock.get_market_cap_by_ticker(today, market="KOSPI")
        kosdaq_cap = stock.get_market_cap_by_ticker(today, market="KOSDAQ")
        
        # 합치고 시가총액 기준 상위 50개 선택
        all_cap = pd.concat([kospi_cap, kosdaq_cap])
        top50 = all_cap.nlargest(50, '시가총액')
        
        # 종목명 추가
        tickers = top50.index.tolist()
        names = []
        for ticker in tickers:
            try:
                name = stock.get_market_ticker_name(ticker)
                names.append(name)
            except:
                names.append(f"종목{ticker}")
        
        top50['종목명'] = names
        return top50
    except Exception as e:
        st.error(f"시가총액 데이터 조회 오류: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)  # 30분 캐시
def calculate_technical_indicators(ticker, period_days=252):
    """기술적 지표 계산"""
    try:
        # 데이터 조회 기간 설정 (1년 + 여유분)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days + 100)
        
        end_str = end_date.strftime("%Y%m%d")
        start_str = start_date.strftime("%Y%m%d")
        
        # 주가 데이터 조회
        df = stock.get_market_ohlcv_by_date(start_str, end_str, ticker)
        
        if df.empty or len(df) < 20:
            return None
        
        # 현재가 (최신 종가)
        current_price = df['종가'].iloc[-1]
        
        # RSI 계산 (14일)
        def calculate_rsi(prices, window=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        rsi = calculate_rsi(df['종가']).iloc[-1]
        
        # 볼린저 밴드 계산 (20일)
        def calculate_bollinger_bands(prices, window=20, num_std=2):
            rolling_mean = prices.rolling(window).mean()
            rolling_std = prices.rolling(window).std()
            upper_band = rolling_mean + (rolling_std * num_std)
            lower_band = rolling_mean - (rolling_std * num_std)
            
            # %B 계산
            percent_b = (prices - lower_band) / (upper_band - lower_band)
            
            # 밴드폭 계산 (상대적)
            band_width = (upper_band - lower_band) / rolling_mean
            
            return percent_b, band_width
        
        percent_b, band_width = calculate_bollinger_bands(df['종가'])
        
        # 최신 볼린저 밴드 %B값
        current_percent_b = percent_b.iloc[-1] if not pd.isna(percent_b.iloc[-1]) else 0
        
        # 최신 볼린저 밴드폭
        current_band_width = band_width.iloc[-1] if not pd.isna(band_width.iloc[-1]) else 0
        
        # 52주(약 252일) 볼린저 밴드폭 평균
        if len(band_width) >= 252:
            avg_52w_band_width = band_width.tail(252).mean()
        else:
            avg_52w_band_width = band_width.mean()
        
        return {
            'current_price': current_price,
            'rsi': rsi if not pd.isna(rsi) else 0,
            'percent_b': current_percent_b,
            'band_width': current_band_width,
            'avg_52w_band_width': avg_52w_band_width if not pd.isna(avg_52w_band_width) else 0
        }
        
    except Exception as e:
        st.warning(f"종목 {ticker} 데이터 처리 오류: {e}")
        return None

def main():
    st.title("🇰🇷 한국 주식 기술적 분석")
    st.markdown("### 시가총액 상위 50개 종목의 기술적 지표 분석")
    
    # 사이드바 설정
    st.sidebar.header("설정")
    
    # 필터링 옵션
    st.sidebar.subheader("📊 필터링 옵션")
    
    rsi_filter = st.sidebar.selectbox(
        "RSI 필터",
        ["전체", "40 미만"],
        index=0
    )
    
    bb_percent_filter = st.sidebar.selectbox(
        "볼린저 밴드 %B 필터", 
        ["전체", "0.5 미만"],
        index=0
    )
    
    bb_width_filter = st.sidebar.selectbox(
        "볼린저 밴드폭 필터",
        ["전체", "52주 평균보다 작음"],
        index=0
    )
    
    refresh_button = st.sidebar.button("데이터 새로고침")
    
    if refresh_button:
        st.cache_data.clear()
        st.rerun()
    
    # 로딩 표시
    with st.spinner("시가총액 상위 50개 종목 조회 중..."):
        top50_data = get_market_cap_top50()
    
    if top50_data.empty:
        st.error("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return
    
    st.success(f"총 {len(top50_data)}개 종목 조회 완료")
    
    # 진행 상태 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 결과 저장할 리스트
    results = []
    
    # 각 종목별 기술적 지표 계산
    for i, (ticker, row) in enumerate(top50_data.iterrows()):
        status_text.text(f"처리 중: {row['종목명']} ({i+1}/{len(top50_data)})")
        progress_bar.progress((i + 1) / len(top50_data))
        
        indicators = calculate_technical_indicators(ticker)
        
        if indicators:
            results.append({
                '종목코드': ticker,
                '종목명': row['종목명'],
                '현재가': f"{indicators['current_price']:,}",
                'RSI': f"{indicators['rsi']:.2f}",
                '볼린저밴드%B': f"{indicators['percent_b']:.4f}",
                '볼린저밴드폭': f"{indicators['band_width']:.4f}",
                '52주볼린저밴드폭평균': f"{indicators['avg_52w_band_width']:.4f}",
                '시가총액': f"{row['시가총액']:,}",
                # 필터링용 원본 값 저장
                'RSI_raw': indicators['rsi'],
                'percent_b_raw': indicators['percent_b'],
                'band_width_raw': indicators['band_width'],
                'avg_52w_band_width_raw': indicators['avg_52w_band_width']
            })
        
        # API 호출 제한을 위한 짧은 대기
        time.sleep(0.1)
    
    # 진행 상태 숨기기
    progress_bar.empty()
    status_text.empty()
    
    if not results:
        st.error("기술적 지표를 계산할 수 있는 종목이 없습니다.")
        return
    
    # 결과 DataFrame 생성
    result_df = pd.DataFrame(results)
    
    # 필터링 적용
    filtered_df = result_df.copy()
    filter_applied = False
    
    # RSI 필터
    if rsi_filter == "40 미만":
        filtered_df = filtered_df[filtered_df['RSI_raw'] < 40]
        filter_applied = True
    
    # 볼린저 밴드 %B 필터
    if bb_percent_filter == "0.5 미만":
        filtered_df = filtered_df[filtered_df['percent_b_raw'] < 0.5]
        filter_applied = True
    
    # 볼린저 밴드폭 필터
    if bb_width_filter == "52주 평균보다 작음":
        filtered_df = filtered_df[filtered_df['band_width_raw'] < filtered_df['avg_52w_band_width_raw']]
        filter_applied = True
    
    # 필터링용 원본 컬럼 제거
    display_df = filtered_df.drop(columns=['RSI_raw', 'percent_b_raw', 'band_width_raw', 'avg_52w_band_width_raw'])
    
    st.markdown("### 📊 기술적 지표 결과")
    
    if filter_applied:
        st.markdown(f"**필터링 결과**: {len(display_df)}개 종목 (전체 {len(result_df)}개 중)")
    else:
        st.markdown(f"**전체 종목**: {len(display_df)}개")
        
    st.markdown(f"**업데이트 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 테이블 표시
    if len(display_df) == 0:
        st.warning("선택한 필터 조건에 맞는 종목이 없습니다.")
    else:
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                '종목코드': st.column_config.TextColumn('종목코드', width=100),
                '종목명': st.column_config.TextColumn('종목명', width=120),
                '현재가': st.column_config.TextColumn('현재가(원)', width=100),
                'RSI': st.column_config.TextColumn('RSI', width=80),
                '볼린저밴드%B': st.column_config.TextColumn('볼린저밴드%B', width=120),
                '볼린저밴드폭': st.column_config.TextColumn('볼린저밴드폭', width=120),
                '52주볼린저밴드폭평균': st.column_config.TextColumn('52주볼린저밴드폭평균', width=150),
                '시가총액': st.column_config.TextColumn('시가총액(원)', width=130)
            }
        )
    
    # 지표 설명
    with st.expander("📖 지표 설명"):
        st.markdown("""
        **RSI (Relative Strength Index)**: 14일 기준, 과매수(70 이상)/과매도(30 이하) 판단
        
        **볼린저 밴드 %B**: 현재가가 볼린저 밴드 내에서 차지하는 위치 (0~1)
        - 0.5: 중간선(이동평균선) 위치
        - 1.0 이상: 상단 밴드 돌파
        - 0.0 이하: 하단 밴드 이탈
        
        **볼린저 밴드폭**: 상단 밴드와 하단 밴드 간격의 상대적 크기
        - 값이 클수록 변동성이 큰 상태
        
        **52주 볼린저 밴드폭 평균**: 최근 1년간 볼린저 밴드폭의 평균값
        - 현재 변동성과 과거 평균 변동성 비교 가능
        """)
    
    # CSV 다운로드
    if len(display_df) > 0:
        csv_data = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 CSV 파일 다운로드",
            data=csv_data,
            file_name=f"korean_stocks_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()