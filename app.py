import streamlit as st
import pandas as pd
from pykrx import stock
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time

# 페이지 설정
st.set_page_config(page_title="한국/미국 주식 기술적 분석", layout="wide")

# 미국 주식 시총 상위 50개 티커 (주기적으로 업데이트 필요)
US_TOP50_TICKERS = ["MSFT", "GOOG", "META", "AMZN", "AAPL", "TSLA", "NVDA", "AVGO", "ORCL", "PLTR", "IONQ", "RKLB", "TEM", "HIMS", "CRDO", "CLS", "NVO", "JOBY", "SPOT", "OKLO", "RCL", "NBIS", "JPM", "PGY", "SMCI"]

def format_market_cap(value):
    """시가총액을 축약 형태로 표시"""
    if value >= 1e12:  # 1조 이상
        return f"{value/1e12:.1f}T"
    elif value >= 1e9:  # 10억 이상  
        return f"{value/1e9:.1f}B"
    elif value >= 1e6:  # 100만 이상
        return f"{value/1e6:.1f}M"
    else:
        return f"{value:,.0f}"

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_market_cap_top50():
    """시총 상위 50개 종목 조회 (한국)"""
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

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_us_stock_data():
    """미국 주식 상위 50개 종목 정보 조회"""
    try:
        results = []
        progress_placeholder = st.empty()
        
        for i, ticker in enumerate(US_TOP50_TICKERS):
            progress_placeholder.text(f"미국 주식 정보 조회 중... ({i+1}/{len(US_TOP50_TICKERS)})")
            
            try:
                stock_info = yf.Ticker(ticker)
                info = stock_info.info
                
                # 시가총액과 회사명 추출
                market_cap = info.get('marketCap', 0)
                company_name = info.get('longName', ticker)
                
                results.append({
                    'ticker': ticker,
                    'name': company_name,
                    'market_cap': market_cap
                })
                
                time.sleep(0.1)  # API 제한 방지
                
            except Exception as e:
                st.warning(f"종목 {ticker} 정보 조회 실패: {e}")
                continue
        
        progress_placeholder.empty()
        
        # DataFrame 생성하고 시가총액 기준 정렬
        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('market_cap', ascending=False).reset_index(drop=True)
        
        return df
        
    except Exception as e:
        st.error(f"미국 주식 데이터 조회 오류: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=1800)  # 30분 캐시
def calculate_technical_indicators_kr(ticker, period_days=252):
    """한국 주식 기술적 지표 계산"""
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
        
        # RSI 계산 (14일) - Wilder's Smoothing 방식
        def calculate_rsi(prices, window=14):
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # 첫 번째 평균은 단순 평균
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            # Wilder's Smoothing 적용
            for i in range(window, len(gain)):
                avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (window-1) + gain.iloc[i]) / window
                avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (window-1) + loss.iloc[i]) / window
            
            rs = avg_gain / avg_loss
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

@st.cache_data(ttl=1800)  # 30분 캐시
def calculate_technical_indicators_us(ticker, period_days=252):
    """미국 주식 기술적 지표 계산"""
    try:
        # yfinance로 1년 + 여유분 데이터 조회
        stock_data = yf.Ticker(ticker)
        df = stock_data.history(period="2y")  # 2년 데이터로 충분한 여유 확보
        
        if df.empty or len(df) < 20:
            return None
        
        # 현재가 (최신 종가)
        current_price = df['Close'].iloc[-1]
        
        # RSI 계산 (14일)
        def calculate_rsi(prices, window=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        rsi = calculate_rsi(df['Close']).iloc[-1]
        
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
        
        percent_b, band_width = calculate_bollinger_bands(df['Close'])
        
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

def load_korean_stocks():
    """한국 주식 데이터 로딩"""
    with st.spinner("한국 주식 시가총액 상위 50개 종목 조회 중..."):
        top50_data = get_market_cap_top50()
    
    if top50_data.empty:
        st.error("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return None
    
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
        
        indicators = calculate_technical_indicators_kr(ticker)
        
        if indicators:
            results.append({
                '종목코드': ticker,
                '종목명': row['종목명'],
                '현재가': f"{indicators['current_price']:,}원",
                'RSI': f"{indicators['rsi']:.2f}",
                '볼린저밴드%B': f"{indicators['percent_b']:.4f}",
                '볼린저밴드폭': f"{indicators['band_width']:.4f}",
                '52주볼린저밴드폭평균': f"{indicators['avg_52w_band_width']:.4f}",
                '시가총액': format_market_cap(row['시가총액']),
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
    
    return pd.DataFrame(results)

def load_us_stocks():
    """미국 주식 데이터 로딩"""
    with st.spinner("미국 주식 상위 50개 종목 조회 중..."):
        us_stocks = get_us_stock_data()
    
    if us_stocks.empty:
        st.error("미국 주식 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return None
    
    st.success(f"총 {len(us_stocks)}개 종목 조회 완료")
    
    # 진행 상태 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 결과 저장할 리스트
    results = []
    
    # 각 종목별 기술적 지표 계산
    for i, row in us_stocks.iterrows():
        ticker = row['ticker']
        name = row['name']
        market_cap = row['market_cap']
        
        status_text.text(f"처리 중: {name} ({i+1}/{len(us_stocks)})")
        progress_bar.progress((i + 1) / len(us_stocks))
        
        indicators = calculate_technical_indicators_us(ticker)
        
        if indicators:
            results.append({
                '종목코드': ticker,
                '종목명': name,
                '현재가': f"${indicators['current_price']:.2f}",
                'RSI': f"{indicators['rsi']:.2f}",
                '볼린저밴드%B': f"{indicators['percent_b']:.4f}",
                '볼린저밴드폭': f"{indicators['band_width']:.4f}",
                '52주볼린저밴드폭평균': f"{indicators['avg_52w_band_width']:.4f}",
                '시가총액': format_market_cap(market_cap),
                # 필터링용 원본 값 저장
                'RSI_raw': indicators['rsi'],
                'percent_b_raw': indicators['percent_b'],
                'band_width_raw': indicators['band_width'],
                'avg_52w_band_width_raw': indicators['avg_52w_band_width']
            })
        
        # API 호출 제한을 위한 짧은 대기
        time.sleep(0.2)
    
    # 진행 상태 숨기기
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(results)

def apply_filters(df, rsi_filter, bb_percent_filter, bb_width_filter):
    """필터 적용 (메모리에서 빠르게 처리)"""
    if df is None or df.empty:
        return df, False
    
    filtered_df = df.copy()
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
    
    return filtered_df, filter_applied

def display_results(df, original_count, filter_applied, country):
    """결과 표시"""
    if df is None or df.empty:
        if df is None:
            return
        st.warning("선택한 필터 조건에 맞는 종목이 없습니다.")
        return
    
    # 필터링용 원본 컬럼 제거
    display_df = df.drop(columns=['RSI_raw', 'percent_b_raw', 'band_width_raw', 'avg_52w_band_width_raw'])
    
    st.markdown(f"### 📊 {country} 주식 기술적 지표 결과")
    
    if filter_applied:
        st.markdown(f"**필터링 결과**: {len(display_df)}개 종목 (전체 {original_count}개 중)")
    else:
        st.markdown(f"**전체 종목**: {len(display_df)}개")
        
    st.markdown(f"**업데이트 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 테이블 표시
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            '종목코드': st.column_config.TextColumn('종목코드', width=100),
            '종목명': st.column_config.TextColumn('종목명', width=120),
            '현재가': st.column_config.TextColumn('현재가', width=100),
            'RSI': st.column_config.TextColumn('RSI', width=80),
            '볼린저밴드%B': st.column_config.TextColumn('볼린저밴드%B', width=120),
            '볼린저밴드폭': st.column_config.TextColumn('볼린저밴드폭', width=120),
            '52주볼린저밴드폭평균': st.column_config.TextColumn('52주볼린저밴드폭평균', width=150),
            '시가총액': st.column_config.TextColumn('시가총액', width=100)
        }
    )
    
    # CSV 다운로드
    csv_data = display_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 CSV 파일 다운로드",
        data=csv_data,
        file_name=f"{country.lower()}_stocks_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def main():
    st.title("🌍 한국/미국 주식 기술적 분석")
    st.markdown("### 시가총액 상위 50개 종목의 기술적 지표 분석")
    
    # 세션 상태 초기화
    if 'korean_data' not in st.session_state:
        st.session_state.korean_data = None
    if 'us_data' not in st.session_state:
        st.session_state.us_data = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'current_country' not in st.session_state:
        st.session_state.current_country = "한국"
    
    # 사이드바 설정
    st.sidebar.header("설정")
    
    # 국가 선택
    country = st.sidebar.selectbox(
        "🌍 국가 선택",
        ["한국", "미국"],
        index=0
    )
    
    # 국가가 변경되었는지 확인
    if country != st.session_state.current_country:
        st.session_state.current_country = country
        st.session_state.data_loaded = False
    
    # 데이터 로딩 버튼
    col1, col2 = st.sidebar.columns(2)
    with col1:
        load_button = st.button("📊 데이터 로딩")
    with col2:
        refresh_button = st.button("🔄 새로고침")
    
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
    
    # 새로고침 처리
    if refresh_button:
        st.cache_data.clear()
        st.session_state.korean_data = None
        st.session_state.us_data = None
        st.session_state.data_loaded = False
        st.rerun()
    
    # 데이터 로딩 처리
    if load_button or not st.session_state.data_loaded:
        if country == "한국":
            if st.session_state.korean_data is None:
                st.session_state.korean_data = load_korean_stocks()
            st.session_state.data_loaded = True
        else:  # 미국
            if st.session_state.us_data is None:
                st.session_state.us_data = load_us_stocks()
            st.session_state.data_loaded = True
    
    # 데이터가 로딩되지 않은 경우 안내
    if not st.session_state.data_loaded:
        st.info(f"👆 사이드바에서 '📊 데이터 로딩' 버튼을 클릭하여 {country} 주식 데이터를 불러오세요.")
        return
    
    # 현재 선택된 국가의 데이터 가져오기
    if country == "한국":
        current_data = st.session_state.korean_data
    else:
        current_data = st.session_state.us_data
    
    if current_data is None or current_data.empty:
        st.error("데이터를 불러올 수 없습니다. 새로고침 후 다시 시도해주세요.")
        return
    
    # 필터 적용 (메모리에서 빠르게 처리)
    filtered_data, filter_applied = apply_filters(current_data, rsi_filter, bb_percent_filter, bb_width_filter)
    
    # 결과 표시
    display_results(filtered_data, len(current_data), filter_applied, country)
    
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
        
        **시가총액 표시**: T(조), B(십억), M(백만) 단위로 축약 표시
        """)

if __name__ == "__main__":
    main()
