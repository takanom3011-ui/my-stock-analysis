import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ==========================================
# デバッグ設定
# ==========================================
st.set_page_config(page_title="株価分析デバッグ", layout="wide")
st.title("🛠 デバッグモード：エラー解析")

st.warning("Jupyterと結果が違う原因を特定するため、エラーを隠さずに表示します。")

# ==========================================
# 1. 銘柄リスト (そのまま)
# ==========================================
jp_custom = [9202, 9201, 8801, 7203, 7707, 7532, 9984, 8031, 8001, 8002, 6758, 9401, 8802, 8591, 8058, 4385, 6993, 6963, 4091, 3563, 4476, 6098, 4165, 4188, 4755]
jp_core = [8035, 6857, 6146, 6723, 6920, 6954, 7735, 6501, 6701, 6702, 6503, 7267, 7201, 7270, 7269, 6301, 6367, 7011, 6273, 6113, 8306, 8316, 8411, 8766, 8725, 8604, 9432, 9433, 9434, 2413, 4661, 4689, 3659, 9735, 9983, 3382, 8267, 2801, 2802, 2503, 2914, 4911, 4568, 4502, 4503, 4519, 4523, 4543, 5401, 5411, 1605, 5020, 3402, 4063, 6981, 7974, 9613, 7832, 9501]
jp_tickers = sorted([f"{t}.T" for t in set(jp_custom + jp_core)])
us_tickers = ["NVDA", "AAPL", "MSFT"] # デバッグ用に減らしています

# ==========================================
# 2. ロジック (エラー表示機能付き)
# ==========================================
def calculate_indicators(df):
    # ここでエラーが起きやすいのでチェック
    if 'Close' not in df.columns:
        # yfinanceのバージョンによってカラムがMultiIndexになる場合がある
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def analyze_recent_week(ticker, market_type):
    # try-except を外してエラーをむき出しにする
    
    # 1. ダウンロード
    df = yf.download(ticker, period="6mo", progress=False)
    
    # 【重要】データが空ならその旨を表示
    if df.empty:
        # st.write(f"⚠️ {ticker}: データが空です (Download Failed)")
        return []

    # 2. 指標計算
    try:
        df = calculate_indicators(df)
    except Exception as e:
        st.error(f"❌ {ticker} の計算中にエラー発生: {e}")
        st.write("▼ 取得したデータの先頭を表示します (カラム名を確認してください)")
        st.write(df.head()) # どんなデータが来ているか見る
        return []
    
    macd = df['MACD'].values
    hist = df['Hist'].values
    rsi = df['RSI'].values
    close = df['Close'].values
    dates = df.index
    
    daily_signals = []
    days_to_check = 10 # 期間を長めに
    start_idx = len(df) - days_to_check
    
    for i in range(start_idx, len(df)):
        if i < 0: continue
        signals = []
        current_macd = macd[i]
        current_hist = hist[i]
        current_rsi = rsi[i]
        current_close = close[i]
        current_date = dates[i].strftime('%Y-%m-%d')
        
        prev_hist = hist[i-1]
        
        # 簡易ロジックチェック (Jupyterと同じか確認)
        # 2nd Attempt
        if current_macd < 0 and current_hist > 0:
            if np.any(hist[i-12:i-1] < 0):
                 # ブロック解析省略せず実行
                start_look = max(0, i-100)
                recent_hist_slice = hist[start_look:i+1]
                recent_macd_slice = macd[start_look:i+1]
                signs = np.sign(recent_hist_slice)
                for k in range(1, len(signs)):
                    if signs[k] == 0: signs[k] = signs[k-1]
                blocks = []
                if len(signs) > 0:
                    c_sign = signs[0]
                    c_len = 0
                    s_idx = 0
                    for k, s in enumerate(signs):
                        if s == c_sign:
                            c_len += 1
                        else:
                            blocks.append({'sign': c_sign, 'len': c_len, 'end': k-1, 'start': s_idx})
                            c_sign = s
                            c_len = 1
                            s_idx = k
                    blocks.append({'sign': c_sign, 'len': c_len, 'end': len(signs)-1, 'start': s_idx})
                
                if len(blocks) >= 4:
                    valley2 = blocks[-2]
                    hill = blocks[-3]
                    valley1 = blocks[-4]
                    if (valley2['sign'] < 0 and hill['sign'] > 0 and valley1['sign'] < 0):
                        if valley2['len'] >= 2 and hill['len'] >= 2 and valley1['len'] >= 2:
                            v2_min = np.min(recent_macd_slice[valley2['start']:valley2['end']+1])
                            v1_min = np.min(recent_macd_slice[valley1['start']:valley1['end']+1])
                            if v2_min < v1_min * 0.95:
                                signals.append("BUY: 2nd Attempt")

        # Re-entry
        if current_hist > 0 and current_hist > prev_hist:
            recent_squeeze = False
            for k in range(2, 7):
                h = hist[i-k]
                m = macd[i-k]
                if h > 0 and h < (abs(m) * 0.10):
                    recent_squeeze = True
                    break
            if recent_squeeze:
                signals.append("BUY: Re-entry")

        if signals:
            daily_signals.append({
                "Date": current_date,
                "Country": market_type,
                "Ticker": ticker,
                "Price": round(float(current_close), 2),
                "Signals": ", ".join(signals)
            })
            
    return daily_signals

# ==========================================
# 3. 実行ボタン
# ==========================================
if st.button("デバッグ分析開始"):
    
    st.write("処理を開始します... (エラーがあれば下に赤字で出ます)")
    
    # 最初の1銘柄だけ詳細表示（生存確認）
    first_ticker = jp_tickers[0]
    st.write(f"試しに1銘柄 ({first_ticker}) のデータを取得して中身を見ます:")
    df_test = yf.download(first_ticker, period="1mo", progress=False)
    st.dataframe(df_test.head())

    all_events = []
    
    # 日本株ループ
    for t in jp_tickers:
        events = analyze_recent_week(t, "JP")
        all_events.extend(events)
        
    # 米国株ループ (デバッグ用3銘柄)
    for t in us_tickers:
        events = analyze_recent_week(t, "US")
        all_events.extend(events)

    if all_events:
        st.success(f"{len(all_events)} 件検出！")
        df_res = pd.DataFrame(all_events)
        st.dataframe(df_res)
    else:
        st.error("やはり結果は0件でした。上記にエラーメッセージは出ていませんか？")
