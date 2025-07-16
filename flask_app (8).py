from flask import Flask, jsonify, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import requests

app = Flask(__name__)

def get_fear_greed_index():
    """CNN 공포탐욕지수 가져오기"""
    try:
        # alternative.me API를 사용 (CNN과 유사한 공포탐욕지수 제공)
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                return {
                    'value': int(latest['value']),
                    'classification': latest['value_classification'],
                    'timestamp': latest['timestamp']
                }
    except Exception as e:
        print(f"공포탐욕지수 가져오기 실패: {e}")

    return None

def get_vix_data():
    """VIX 지수 가져오기"""
    try:
        vix_ticker = yf.Ticker("^VIX")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5)

        data = vix_ticker.history(start=start_date, end=end_date)

        if not data.empty:
            current_vix = data['Close'].iloc[-1]
            return {
                'value': round(current_vix, 2),
                'timestamp': data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        print(f"VIX 데이터 가져오기 실패: {e}")

    return None

def calculate_stochastic(high, low, close, k_period, d_period, smooth_k=1):
    """
    스토캐스틱 오실레이터 계산
    k_period: %K 기간
    d_period: %D 기간 (이동평균)
    smooth_k: %K 스무딩 기간
    """
    # 최고가와 최저가의 기간별 값 계산
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    # %K 계산
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))

    # %K 스무딩 (기본값 1이면 스무딩 안함)
    if smooth_k > 1:
        k_percent = k_percent.rolling(window=smooth_k).mean()

    # %D 계산 (%K의 이동평균)
    d_percent = k_percent.rolling(window=d_period).mean()

    return k_percent, d_percent

def analyze_ticker(ticker_symbol):
    """개별 티커 분석"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=150)

        data = ticker.history(start=start_date, end=end_date)

        if data.empty:
            return None

        # 최근 종가
        current_price = data['Close'].iloc[-1]

        # 20일 이동평균선 계산
        ma_20 = data['Close'].rolling(window=20).mean().iloc[-1]

        # 스토캐스틱 계산
        high = data['High']
        low = data['Low']
        close = data['Close']

        # 스토캐스틱 5,3,3
        stoch_5_k, stoch_5_d = calculate_stochastic(high, low, close, 5, 3, 3)
        stoch_5_k_current = stoch_5_k.iloc[-1]

        # 스토캐스틱 10,6,6
        stoch_10_k, stoch_10_d = calculate_stochastic(high, low, close, 10, 6, 6)
        stoch_10_k_current = stoch_10_k.iloc[-1]

        # 스토캐스틱 20,12,12
        stoch_20_k, stoch_20_d = calculate_stochastic(high, low, close, 20, 12, 12)
        stoch_20_k_current = stoch_20_k.iloc[-1]

        return {
            "ticker": ticker_symbol,
            "current_price": round(current_price, 2),
            "ma_20": round(ma_20, 2),
            "price_below_ma20": current_price < ma_20,
            "stochastic_analysis": {
                "stoch_5_3_3": {
                    "k_value": round(stoch_5_k_current, 2),
                    "k_below_30": stoch_5_k_current < 30
                },
                "stoch_10_6_6": {
                    "k_value": round(stoch_10_k_current, 2),
                    "k_below_30": stoch_10_k_current < 30
                },
                "stoch_20_12_12": {
                    "k_value": round(stoch_20_k_current, 2),
                    "k_below_30": stoch_20_k_current < 30
                }
            },
            "summary": {
                "all_stoch_oversold": (stoch_5_k_current < 30 and
                                     stoch_10_k_current < 30 and
                                     stoch_20_k_current < 30),
                "price_and_stoch_bearish": (current_price < ma_20 and
                                          stoch_5_k_current < 30 and
                                          stoch_10_k_current < 30 and
                                          stoch_20_k_current < 30)
            }
        }

    except Exception as e:
        return None

def get_chart_data(ticker_symbol):
    """차트용 데이터 생성"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        end_date = datetime.now()
        # 200일 이동평균을 위해 최소 300 거래일 필요 (약 430 캘린더 일)
        start_date = end_date - timedelta(days=500)  # 500일로 증가

        data = ticker.history(start=start_date, end=end_date)

        if data.empty:
            return None

        # 이동평균선 계산
        data['MA5'] = data['Close'].rolling(window=5).mean()
        data['MA20'] = data['Close'].rolling(window=20).mean()
        data['MA50'] = data['Close'].rolling(window=50).mean()
        data['MA120'] = data['Close'].rolling(window=120).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()

        # 스토캐스틱 계산
        high = data['High']
        low = data['Low']
        close = data['Close']

        # 스토캐스틱 5,3,3
        stoch_5_k, stoch_5_d = calculate_stochastic(high, low, close, 5, 3, 3)
        data['Stoch_5_3_3_K'] = stoch_5_k
        data['Stoch_5_3_3_D'] = stoch_5_d

        # 스토캐스틱 10,6,6
        stoch_10_k, stoch_10_d = calculate_stochastic(high, low, close, 10, 6, 6)
        data['Stoch_10_6_6_K'] = stoch_10_k
        data['Stoch_10_6_6_D'] = stoch_10_d

        # 스토캐스틱 20,12,12
        stoch_20_k, stoch_20_d = calculate_stochastic(high, low, close, 20, 12, 12)
        data['Stoch_20_12_12_K'] = stoch_20_k
        data['Stoch_20_12_12_D'] = stoch_20_d

        # 200일 이동평균이 계산된 데이터만 사용 (최근 60일)
        # 200일 이동평균이 NaN이 아닌 구간부터 사용
        valid_data = data.dropna(subset=['MA200'])

        if len(valid_data) < 60:
            # 유효한 데이터가 60일보다 적으면 전체 사용
            chart_data = valid_data.copy()
        else:
            # 최근 60일 사용
            chart_data = valid_data.tail(60).copy()

        # 날짜를 문자열로 변환
        chart_data.index = chart_data.index.strftime('%Y-%m-%d')

        # NaN 값을 None으로 변경 (JSON 직렬화를 위해)
        chart_data = chart_data.where(pd.notnull(chart_data), None)

        return {
            "dates": chart_data.index.tolist(),
            "close": chart_data['Close'].tolist(),
            "ma5": chart_data['MA5'].tolist(),
            "ma20": chart_data['MA20'].tolist(),
            "ma50": chart_data['MA50'].tolist(),
            "ma120": chart_data['MA120'].tolist(),
            "ma200": chart_data['MA200'].tolist(),
            "stoch_5_3_3_k": chart_data['Stoch_5_3_3_K'].tolist(),
            "stoch_5_3_3_d": chart_data['Stoch_5_3_3_D'].tolist(),
            "stoch_10_6_6_k": chart_data['Stoch_10_6_6_K'].tolist(),
            "stoch_10_6_6_d": chart_data['Stoch_10_6_6_D'].tolist(),
            "stoch_20_12_12_k": chart_data['Stoch_20_12_12_K'].tolist(),
            "stoch_20_12_12_d": chart_data['Stoch_20_12_12_D'].tolist()
        }

    except Exception as e:
        return None

def get_multi_ticker_analysis():
    """여러 티커 분석 데이터 수집"""
    # VIX를 제외한 종목들
    tickers = ["MSFT", "GOOG", "META", "AMZN", "AAPL", "TSLA", "NVDA", "AVGO", "ORCL", "PLTR", "IONQ", "RKLB", "TEM", "HIMS", "CRDO", "CLS", "MSTY"]
    results = []
    errors = []

    for ticker in tickers:
        analysis = analyze_ticker(ticker)
        if analysis:
            results.append(analysis)
        else:
            errors.append(f"{ticker} 데이터를 가져올 수 없습니다.")

    # VIX와 공포탐욕지수 별도 수집
    vix_data = get_vix_data()
    fear_greed_data = get_fear_greed_index()

    return {
        "results": results,
        "errors": errors,
        "vix_data": vix_data,
        "fear_greed_data": fear_greed_data,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.route('/')
def home():
    """메인 페이지 (모바일 최적화)"""
    return render_template('index.html')

@app.route('/analysis')
def analysis_page():
    """분석 결과 HTML 페이지 (모바일 최적화)"""
    result = get_multi_ticker_analysis()

    if not result['results']:
        error_msg = result['errors'] if result['errors'] else ["데이터를 가져올 수 없습니다."]
        return render_template('error.html', errors=error_msg)

    return render_template('analysis.html', data=result)

@app.route('/analysis/json')
def analysis_json():
    """분석 결과 JSON 반환"""
    result = get_multi_ticker_analysis()
    return jsonify(result)

@app.route('/chart/<ticker>')
def chart_page(ticker):
    """개별 종목 차트 페이지"""
    chart_data = get_chart_data(ticker.upper())

    if not chart_data:
        return render_template('error.html', errors=[f"{ticker} 차트 데이터를 가져올 수 없습니다."])

    return render_template('chart.html', ticker=ticker.upper(), chart_data=json.dumps(chart_data))

@app.route('/chart/data/<ticker>')
def chart_data_json(ticker):
    """차트 데이터 JSON 반환"""
    chart_data = get_chart_data(ticker.upper())

    if not chart_data:
        return jsonify({"error": f"{ticker} 데이터를 가져올 수 없습니다."}), 404

    return jsonify(chart_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')