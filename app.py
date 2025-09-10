import streamlit as st
import pandas as pd
from pykrx import stock
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import time
import requests

# 페이지 설정
st.set_page_config(page_title="한국/미국 주식 기술적 분석", layout="wide")

# 기본 미국 주식 시총 상위 50개 티커 (기본값)
DEFAULT_US_TICKERS = ["MSFT", "GOOG", "META", "AMZN", "AAPL", "TSLA", "NVDA", "AVGO", "ORCL", "PLTR", "IONQ", "RKLB", "TEM", "HIMS", "CRDO", "CLS", "NVO", "JOBY", "SPOT", "OKLO", "RCL", "NBIS", "JPM", "PGY", "SMCI"]

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

@st.cache_data(ttl=300)  # 5분 캐시
def get_market_indicators():
    """주요 시장 지표 조회"""
    indicators = {}
    
    try:
        # CNN 공포탐욕지수 (Alternative.me API 사용)
        fear_greed_url = "https://api.alternative.me/fng/"
        response = requests.get(fear_greed_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current_value = int(data['data'][0]['value'])
            previous_value = int(data['data'][1]['value'])
            indicators['fear_greed'] = {
                'name': 'CNN 공포탐욕지수',
                'current': current_value,
                'previous': previous_value,
                'change': current_value - previous_value,
                'change_pct': ((current_value - previous_value) / previous_value) * 100 if previous_value != 0 else 0
            }
    except:
        indicators['fear_greed'] = {
            'name': 'CNN 공포탐욕지수',
            'current': 0,
            'previous': 0,
            'change': 0,
            'change_pct': 0
        }
    
    # yfinance를 사용한 지표들
    symbols = {
        'vix': '^VIX',
        'sp500': '^GSPC',
        'nasdaq100': '^NDX',
        'usdkrw': 'KRW=X',
        'bitcoin': 'BTC-USD',
        'ethereum': 'ETH-USD'
    }
    
    names = {
        'vix': 'VIX 지수',
        'sp500': 'S&P 500',
        'nasdaq100': '나스닥 100',
        'usdkrw': '원/달러 환율',
        'bitcoin': '비트코인',
        'ethereum': '이더리움'
    }
    
    for key, symbol in symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = current - previous
                change_pct = (change / previous) * 100 if previous != 0 else 0
                
                indicators[key] = {
                    'name': names[key],
                    'current': current,
                    'previous': previous,
                    'change': change,
                    'change_pct': change_pct
                }
            else:
                indicators[key] = {
                    'name': names[key],
                    'current': 0,
                    'previous': 0,
                    'change': 0,
                    'change_pct': 0
                }
        except:
            indicators[key] = {
                'name': names[key],
                'current': 0,
                'previous': 0,
                'change': 0,
                'change_pct': 0
            }
    
    return indicators

def display_market_indicators():
    """시장 지표를 박스 형태로 표시"""
    indicators = get_market_indicators()
    
    st.markdown("### 📊 주요 시장 지표")
    
    # 첫 번째 행: CNN 공포탐욕지수, VIX, S&P 500, 나스닥 100
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        indicator = indicators['fear_greed']
        color = "🔴" if indicator['change'] > 0 else "🔵" if indicator['change'] < 0 else "⚪"
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            background-color: {'rgba(255,0,0,0.1)' if indicator['change'] > 0 else 'rgba(0,0,255,0.1)' if indicator['change'] < 0 else 'rgba(128,128,128,0.1)'};
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: #333;">{color} {indicator['name']}</h4>
            <h2 style="margin: 5px 0; color: #333;">{indicator['current']:.0f}</h2>
            <p style="margin: 0; color: {'red' if indicator['change'] > 0 else 'blue' if indicator['change'] < 0 else 'gray'};">
                {'+' if indicator['change'] > 0 else ''}{indicator['change']:+.0f} ({indicator['change_pct']:+.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        indicator = indicators['vix']
        color = "🔴" if indicator['change'] > 0 else "🔵" if indicator['change'] < 0 else "⚪"
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            background-color: {'rgba(255,0,0,0.1)' if indicator['change'] > 0 else 'rgba(0,0,255,0.1)' if indicator['change'] < 0 else 'rgba(128,128,128,0.1)'};
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: #333;">{color} {indicator['name']}</h4>
            <h2 style="margin: 5px 0; color: #333;">{indicator['current']:.2f}</h2>
            <p style="margin: 0; color: {'red' if indicator['change'] > 0 else 'blue' if indicator['change'] < 0 else 'gray'};">
                {'+' if indicator['change'] > 0 else ''}{indicator['change']:+.2f} ({indicator['change_pct']:+.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        indicator = indicators['sp500']
        color = "🔴" if indicator['change'] > 0 else "🔵" if indicator['change'] < 0 else "⚪"
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            background-color: {'rgba(255,0,0,0.1)' if indicator['change'] > 0 else 'rgba(0,0,255,0.1)' if indicator['change'] < 0 else 'rgba(128,128,128,0.1)'};
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: #333;">{color} {indicator['name']}</h4>
            <h2 style="margin: 5px 0; color: #333;">{indicator['current']:.0f}</h2>
            <p style="margin: 0; color: {'red' if indicator['change'] > 0 else 'blue' if indicator['change'] < 0 else 'gray'};">
                {'+' if indicator['change'] > 0 else ''}{indicator['change']:+.0f} ({indicator['change_pct']:+.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        indicator = indicators['nasdaq100']
        color = "🔴" if indicator['change'] > 0 else "🔵" if indicator['change'] < 0 else "⚪"
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            background-color: {'rgba(255,0,0,0.1)' if indicator['change'] > 0 else 'rgba(0,0,255,0.1)' if indicator['change'] < 0 else 'rgba(128,128,128,0.1)'};
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: #333;">{color} {indicator['name']}</h4>
            <h2 style="margin: 5px 0; color: #333;">{indicator['current']:.0f}</h2>
            <p style="margin: 0; color: {'red' if indicator['change'] > 0 else 'blue' if indicator['change'] < 0 else 'gray'};">
                {'+' if indicator['change'] > 0 else ''}{indicator['change']:+.0f} ({indicator['change_pct']:+.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # 두 번째 행: 원/달러 환율, 비트코인, 이더리움
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        indicator = indicators['usdkrw']
        color = "🔴" if indicator['change'] > 0 else "🔵" if indicator['change'] < 0 else "⚪"
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            background-color: {'rgba(255,0,0,0.1)' if indicator['change'] > 0 else 'rgba(0,0,255,0.1)' if indicator['change'] < 0 else 'rgba(128,128,128,0.1)'};
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: #333;">{color} {indicator['name']}</h4>
            <h2 style="margin: 5px 0; color: #333;">{indicator['current']:.0f}원</h2>
            <p style="margin: 0; color: {'red' if indicator['change'] > 0 else 'blue' if indicator['change'] < 0 else 'gray'};">
                {'+' if indicator['change'] > 0 else ''}{indicator['change']:+.0f}원 ({indicator['change_pct']:+.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        indicator = indicators['bitcoin']
        color = "🔴" if indicator['change'] > 0 else "🔵" if indicator['change'] < 0 else "⚪"
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            background-color: {'rgba(255,0,0,0.1)' if indicator['change'] > 0 else 'rgba(0,0,255,0.1)' if indicator['change'] < 0 else 'rgba(128,128,128,0.1)'};
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: #333;">{color} {indicator['name']}</h4>
            <h2 style="margin: 5px 0; color: #333;">${indicator['current']:,.0f}</h2>
            <p style="margin: 0; color: {'red' if indicator['change'] > 0 else 'blue' if indicator['change'] < 0 else 'gray'};">
                {'+' if indicator['change'] > 0 else ''}${indicator['change']:+,.0f} ({indicator['change_pct']:+.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        indicator = indicators['ethereum']
        color = "🔴" if indicator['change'] > 0 else "🔵" if indicator['change'] < 0 else "⚪"
        st.markdown(f"""
        <div style="
            border: 2px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            background-color: {'rgba(255,0,0,0.1)' if indicator['change'] > 0 else 'rgba(0,0,255,0.1)' if indicator['change'] < 0 else 'rgba(128,128,128,0.1)'};
            margin-bottom: 10px;
        ">
            <h4 style="margin: 0; color: #333;">{color} {indicator['name']}</h4>
            <h2 style="margin: 5px 0; color: #333;">${indicator['current']:,.0f}</h2>
            <p style="margin: 0; color: {'red' if indicator['change'] > 0 else 'blue' if indicator['change'] < 0 else 'gray'};">
                {'+' if indicator['change'] > 0 else ''}${indicator['change']:+,.0f} ({indicator['change_pct']:+.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # 빈 컬럼 (필요시 추가 지표 사용)
        st.write("")
    
    st.markdown("---")  # 구분선

@st.cache_data(ttl=3600)  # 1시간 캐시
def get_market_cap_top100():
    """시총 상위 100개 종목 조회 (한국)"""
    try:
        today = datetime.now().strftime("%Y%m%d")
        # 코스피 + 코스닥 전체 종목의 시가총액 조회
        kospi_cap = stock.get_market_cap_by_ticker(today, market="KOSPI")
        kosdaq_cap = stock.get_market_cap_by_ticker(today, market="KOSDAQ")
        
        # 합치고 시가총액 기준 상위 100개 선택
        all_cap = pd.concat([kospi_cap, kosdaq_cap])
        top100 = all_cap.nlargest(100, '시가총액')
        
        # 종목명 추가
        tickers = top100.index.tolist()
        names = []
        for ticker in tickers:
            try:
                name = stock.get_market_ticker_name(ticker)
                names.append(name)
            except:
                names.append(f"종목{ticker}")
        
        top100['종목명'] = names
        return top100
    except Exception as e:
        st.error(f"시가총액 데이터 조회 오류: {e}")
        return pd.DataFrame()

def validate_ticker(ticker):
    """티커가 유효한지 검증"""
    try:
        stock_info = yf.Ticker(ticker)
        info = stock_info.info
        # 기본적인 정보가 있는지 확인
        if info.get('symbol') or info.get('shortName') or info.get('longName'):
            return True
        return False
    except:
        return False

def get_us_stock_data(tickers_list):
    """미국 주식 정보 조회 (사용자 정의 티커 리스트 사용)"""
    try:
        results = []
        progress_placeholder = st.empty()
        
        for i, ticker in enumerate(tickers_list):
            progress_placeholder.text(f"미국 주식 정보 조회 중... ({i+1}/{len(tickers_list)})")
            
            try:
                stock_info = yf.Ticker(ticker)
                info = stock_info.info
                
                # 시가총액과 회사명 추출
                market_cap = info.get('marketCap', 0)
                company_name = info.get('longName', info.get('shortName', ticker))
                
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
    with st.spinner("한국 주식 시가총액 상위 100개 종목 조회 중..."):
        top100_data = get_market_cap_top100()
    
    if top100_data.empty:
        st.error("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return None
    
    st.success(f"총 {len(top100_data)}개 종목 조회 완료")
    
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

def manage_us_tickers():
    """미국 주식 티커 관리 인터페이스"""
    st.sidebar.subheader("🔧 미국 주식 티커 관리")
    
    # 세션 상태에서 현재 티커 리스트 가져오기
    if 'us_tickers' not in st.session_state:
        st.session_state.us_tickers = DEFAULT_US_TICKERS.copy()
    
    current_tickers = st.session_state.us_tickers
    
    # 현재 티커 수 표시
    st.sidebar.write(f"현재 등록된 종목: {len(current_tickers)}개")
    
    # 티커 추가 섹션
    with st.sidebar.expander("➕ 티커 추가", expanded=False):
        new_ticker = st.text_input(
            "추가할 티커 입력",
            placeholder="예: NFLX, DIS, etc.",
            key="new_ticker_input"
        ).upper().strip()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 추가", key="add_ticker"):
                if new_ticker:
                    if new_ticker not in current_tickers:
                        # 티커 유효성 검증
                        with st.spinner(f"{new_ticker} 유효성 검증 중..."):
                            if validate_ticker(new_ticker):
                                st.session_state.us_tickers.append(new_ticker)
                                st.success(f"{new_ticker} 추가됨!")
                                # 데이터 새로고침 필요
                                st.session_state.us_data = None
                                st.session_state.data_loaded = False
                                st.rerun()
                            else:
                                st.error(f"{new_ticker}는 유효하지 않은 티커입니다.")
                    else:
                        st.warning(f"{new_ticker}는 이미 등록된 티커입니다.")
                else:
                    st.warning("티커를 입력해주세요.")
        
        with col2:
            if st.button("🔄 초기화", key="reset_tickers"):
                st.session_state.us_tickers = DEFAULT_US_TICKERS.copy()
                st.session_state.us_data = None
                st.session_state.data_loaded = False
                st.success("티커 목록이 초기화되었습니다!")
                st.rerun()
    
    # 티커 제거 섹션
    with st.sidebar.expander("➖ 티커 제거", expanded=False):
        if current_tickers:
            # 현재 티커들을 정렬해서 표시
            sorted_tickers = sorted(current_tickers)
            
            # 선택 가능한 티커 리스트
            tickers_to_remove = st.multiselect(
                "제거할 티커 선택",
                sorted_tickers,
                key="tickers_to_remove"
            )
            
            if st.button("🗑️ 선택 항목 제거", key="remove_tickers"):
                if tickers_to_remove:
                    for ticker in tickers_to_remove:
                        if ticker in st.session_state.us_tickers:
                            st.session_state.us_tickers.remove(ticker)
                    
                    # 데이터 새로고침 필요
                    st.session_state.us_data = None
                    st.session_state.data_loaded = False
                    st.success(f"{len(tickers_to_remove)}개 티커가 제거되었습니다!")
                    st.rerun()
                else:
                    st.warning("제거할 티커를 선택해주세요.")
        else:
            st.write("제거할 티커가 없습니다.")
    
    # 현재 티커 목록 표시
    with st.sidebar.expander("📋 현재 티커 목록", expanded=False):
        if current_tickers:
            # 5개씩 한 줄에 표시
            ticker_chunks = [current_tickers[i:i+5] for i in range(0, len(current_tickers), 5)]
            for chunk in ticker_chunks:
                st.write(" • ".join(chunk))
        else:
            st.write("등록된 티커가 없습니다.")

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
    st.title("🌏 한국/미국 주식 기술적 분석")
    st.markdown("### 시가총액 상위 종목의 기술적 지표 분석")
    
    # 주요 시장 지표 표시
    display_market_indicators()
    
    # 세션 상태 초기화
    if 'korean_data' not in st.session_state:
        st.session_state.korean_data = None
    if 'us_data' not in st.session_state:
        st.session_state.us_data = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'current_country' not in st.session_state:
        st.session_state.current_country = "한국"
    if 'us_tickers' not in st.session_state:
        st.session_state.us_tickers = DEFAULT_US_TICKERS.copy()
    
    # 사이드바 설정
    st.sidebar.header("설정")
    
    # 국가 선택
    country = st.sidebar.selectbox(
        "🌏 국가 선택",
        ["한국", "미국"],
        index=0
    )
    
    # 미국 선택 시 티커 관리 인터페이스 표시
    if country == "미국":
        manage_us_tickers()
    
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
        ticker_count = len(st.session_state.us_tickers) if country == "미국" else 100
        st.info(f"👆 사이드바에서 '📊 데이터 로딩' 버튼을 클릭하여 {country} 주식 데이터({ticker_count}개 종목)를 불러오세요.")
        
        # 미국 주식인 경우 현재 등록된 티커 미리보기
        if country == "미국":
            with st.expander("📋 현재 등록된 미국 주식 티커 미리보기"):
                current_tickers = st.session_state.us_tickers
                st.write(f"총 {len(current_tickers)}개 종목이 등록되어 있습니다.")
                # 10개씩 한 줄에 표시
                ticker_chunks = [current_tickers[i:i+10] for i in range(0, len(current_tickers), 10)]
                for chunk in ticker_chunks:
                    st.write(" • ".join(chunk))
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
        - 0.5: 중간선 (이동평균선) 위치
        - 1.0 이상: 상단 밴드 돌파
        - 0.0 이하: 하단 밴드 이탈
        
        **볼린저 밴드폭**: 상단 밴드와 하단 밴드 간격의 상대적 크기
        - 값이 클수록 변동성이 큰 상태
        
        **52주 볼린저 밴드폭 평균**: 최근 1년간 볼린저 밴드폭의 평균값
        - 현재 변동성과 과거 평균 변동성 비교 가능
        
        **시가총액 표시**: T(조), B(십억), M(백만) 단위로 축약 표시
        
        ---
        
        **🔧 미국 주식 티커 관리 기능**:
        - 사이드바에서 원하는 미국 주식 티커를 추가/제거할 수 있습니다
        - 추가 시 자동으로 유효성 검증을 실시합니다
        - 초기화 버튼으로 기본 상위 25개 종목으로 되돌릴 수 있습니다
        
        ---
        
        **📊 주요 시장 지표**:
        - CNN 공포탐욕지수: 0-100 스케일로 시장 심리 측정
        - VIX 지수: 시장 변동성 측정 (공포 지수)
        - S&P 500 & 나스닥 100: 미국 주요 주가지수
        - 원/달러 환율: 한국 투자자 기준 중요 지표
        - 비트코인 & 이더리움: 주요 암호화폐 가격
        """)

if __name__ == "__main__":
    main()
    results = []
    
    # 각 종목별 기술적 지표 계산
    for i, (ticker, row) in enumerate(top100_data.iterrows()):
        status_text.text(f"처리 중: {row['종목명']} ({i+1}/{len(top100_data)})")
        progress_bar.progress((i + 1) / len(top100_data))
        
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
    # 세션 상태에서 사용자 정의 티커 리스트 가져오기
    current_tickers = st.session_state.get('us_tickers', DEFAULT_US_TICKERS.copy())
    
    with st.spinner(f"미국 주식 {len(current_tickers)}개 종목 조회 중..."):
        us_stocks = get_us_stock_data(current_tickers)
    
    if us_stocks.empty:
        st.error("미국 주식 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.")
        return None
    
    st.success(f"총 {len(us_stocks)}개 종목 조회 완료")
    
    # 진행 상태 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 결과
