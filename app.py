import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# ページ設定 (サイトの見た目)
# ==========================================
st.set_page_config(
    page_title="株価シグナル検知アプリ",
    page_icon="📈",
    layout="wide"
)

st.title("📈 株価トレンド判定アルゴリズム")
st.markdown("あなたの定義したロジック（MACD 2nd Attempt / Re-entry 等）に基づいて、有望な銘柄を抽出します。")

# ==========================================
# 1. 銘柄リスト定義
# ==========================================
jp_custom = [
    9202, 9201, 8801, 7203, 7707, 7532, 9984, 8031, 8001, 8002, 
    6758, 9401, 8802, 8591, 8058, 4385, 6993, 6963, 4091, 3563, 
    4476, 6098, 4165, 4188, 4755
]
jp_core = [
    8035, 6857, 6146, 6723, 6920, 6954, 7735, 6501, 6701, 6702, 6503,
    7267, 7201, 7270, 7269, 6301, 6367, 7011, 6273, 6113,
    8306, 8316, 8411, 8766, 8725, 8604,
    9432, 9433, 9434, 2413, 4661, 4689, 3659, 9735,
    9983, 3382, 8267, 2801, 2802, 2503, 2914, 4911,
    4568, 4502, 4503, 4519, 4523, 4543,
    5401, 5411, 1605, 5020, 3402, 4063, 6981,
    7974, 9613, 7832, 9501
]
jp_tickers = sorted([f"{t}.T" for t in set(jp_custom + jp_core)])

us_tickers = [
    "NVDA", "AAPL", "MSFT", "AMZN", "TSLA", "META", "GOOGL", "GOOG",
    "AVGO", "AMD", "QCOM", "TXN", "AMAT", "INTC", "MU", "LRCX", "ADI",
    "NFLX", "ADBE", "CSCO", "CRM", "PANW", "INTU",
    "COST", "PEP", "TMUS", "CMCSA", "AMGN", "ISRG", "BKNG", "VRTX"
]
us_tickers = sorted(list(set(us_tickers)))

# サイドバー設定
st.sidebar.header("設定")
target_market = st.sidebar.multiselect(
    "対象市場を選択",
    ["日本株 (主力+監視)", "米国株 (NASDAQ主力)"],
    default=["日本株 (主力+監視)", "米国株 (NASDAQ主力)"]
)

days_to_check = st.sidebar.slider("過去何日分のシグナルを表示？", 1, 10, 5)

# ==========================================
# 2. ロジック関数 (キャッシュ化で高速化)
# ==========================================
def calculate_indicators(df):
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

def analyze_recent_week(ticker, market_type, check_days):
    try:
        # データ量を減らすため期間を調整
        df = yf.download(ticker, period="6mo", progress=False)
        if len(df) < 60: return []
        
        df = calculate_indicators(df)
        
        macd = df['MACD'].values
        hist = df['Hist'].values
        rsi = df['RSI'].values
        close = df['Close'].values
        dates = df.index
        
        daily_signals = []
        start_idx = len(df) - check_days
        
        for i in range(start_idx, len(df)):
            signals = []
            current_macd = macd[i]
            current_hist = hist[i]
            current_rsi = rsi[i]
            current_close = close[i]
            current_date = dates[i].strftime('%Y-%m-%d')
            
            prev_hist = hist[i-1]
            prev_macd = macd[i-1]
            prev_sig = df['Signal'].values[i-1]
            
            # --- A. 買いシグナル ---
            # 1. 2nd Attempt (右下がりW)
            if current_macd < 0 and current_hist > 0:
                if np.any(hist[i-12:i-1] < 0):
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

            # 2. Re-entry (Bounce)
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

            # --- B. 売りシグナル ---
            # 1. RSI Divergence
            price_5d = close[i-5]
            rsi_5d = rsi[i-5]
            if (current_close > price_5d) and (current_rsi < rsi_5d) and (current_rsi > 60):
                signals.append("SELL: RSI Div")
            
            # 2. Squeeze Alert
            if current_hist > 0:
                if current_hist < (abs(current_macd) * 0.10):
                    if prev_hist > current_hist:
                        signals.append("SELL: Squeeze")
            
            # 3. Dead Cross
            if current_macd < df['Signal'].values[i]:
                if prev_macd >= prev_sig:
                    signals.append("SELL: Dead Cross")

            if signals:
                daily_signals.append({
                    "Date": current_date,
                    "Country": market_type,
                    "Ticker": ticker,
                    "Price": round(float(current_close), 2),
                    "Signals": ", ".join(signals)
                })
        return daily_signals

    except Exception:
        return []

# ==========================================
# 3. メイン処理
# ==========================================
if st.button("分析を開始する", type="primary"):
    
    target_tickers = []
    if "日本株 (主力+監視)" in target_market:
        for t in jp_tickers: target_tickers.append((t, "JP"))
    if "米国株 (NASDAQ主力)" in target_market:
        for t in us_tickers: target_tickers.append((t, "US"))
    
    if not target_tickers:
        st.warning("市場を選択してください。")
    else:
        st.write(f"全 {len(target_tickers)} 銘柄をスキャン中...")
        my_bar = st.progress(0)
        
        all_events = []
        total = len(target_tickers)
        
        # Streamlit用のプレースホルダー
        status_text = st.empty()
        
        for idx, (ticker, mkt) in enumerate(target_tickers):
            # 進捗表示更新
            status_text.text(f"Scanning: {ticker} ({idx+1}/{total})")
            my_bar.progress((idx + 1) / total)
            
            # 分析実行
            events = analyze_recent_week(ticker, mkt, days_to_check)
            all_events.extend(events)
        
        status_text.text("完了！")
        my_bar.empty()

        if all_events:
            df_res = pd.DataFrame(all_events)
            # 日付新しい順 -> 国 -> 銘柄
            df_res = df_res.sort_values(by=["Date", "Country", "Ticker"], ascending=[False, True, True])
            
            st.success(f"{len(df_res)} 件のシグナルを検出しました。")
            
            # データフレームを表示 (インタラクティブな表)
            st.dataframe(
                df_res,
                column_config={
                    "Date": "日付",
                    "Country": "市場",
                    "Ticker": "銘柄コード",
                    "Price": st.column_config.NumberColumn("株価", format="%.2f"),
                    "Signals": "検出シグナル",
                },
                use_container_width=True,
                hide_index=True
            )
            
            # CSVダウンロードボタン
            csv = df_res.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="CSVデータをダウンロード",
                data=csv,
                file_name='stock_signals.csv',
                mime='text/csv',
            )
        else:
            st.info("指定期間内にシグナルは検出されませんでした。")

else:
    st.write("左のサイドバーで設定を行い、「分析を開始する」ボタンを押してください。")
