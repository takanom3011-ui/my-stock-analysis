import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# ページ設定
# ==========================================
st.set_page_config(page_title="株価シグナル検知アプリ", page_icon="📈", layout="wide")
st.title("📈 株価トレンド判定アルゴリズム")

# ==========================================
# 1. 銘柄リスト
# ==========================================
jp_custom = [9202, 9201, 8801, 7203, 7707, 7532, 9984, 8031, 8001, 8002, 6758, 9401, 8802, 8591, 8058, 4385, 6993, 6963, 4091, 3563, 4476, 6098, 4165, 4188, 4755]
jp_core = [8035, 6857, 6146, 6723, 6920, 6954, 7735, 6501, 6701, 6702, 6503, 7267, 7201, 7270, 7269, 6301, 6367, 7011, 6273, 6113, 8306, 8316, 8411, 8766, 8725, 8604, 9432, 9433, 9434, 2413, 4661, 4689, 3659, 9735, 9983, 3382, 8267, 2801, 2802, 2503, 2914, 4911, 4568, 4502, 4503, 4519, 4523, 4543, 5401, 5411, 1605, 5020, 3402, 4063, 6981, 7974, 9613, 7832, 9501]
jp_tickers = sorted([f"{t}.T" for t in set(jp_custom + jp_core)])
us_tickers = sorted(list(set(["NVDA", "AAPL", "MSFT", "AMZN", "TSLA", "META", "GOOGL", "GOOG", "AVGO", "AMD", "QCOM", "TXN", "AMAT", "INTC", "MU", "LRCX", "ADI", "NFLX", "ADBE", "CSCO", "CRM", "PANW", "INTU", "COST", "PEP", "TMUS", "CMCSA", "AMGN", "ISRG", "BKNG", "VRTX"])))

# サイドバー設定
st.sidebar.header("設定")
target_market = st.sidebar.multiselect("対象市場", ["日本株", "米国株"], default=["日本株", "米国株"])
days_to_check = st.sidebar.slider("検索期間 (過去X日)", 1, 30, 10)

# ==========================================
# 2. ロジック関数 (修正版)
# ==========================================
def calculate_indicators(df):
    # 指標計算
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

# 【重要】どんなデータ形式が来ても強制的に数値にする関数
def safe_float(val):
    try:
        # 配列やSeriesなら中身を取り出す
        if isinstance(val, (pd.Series, np.ndarray, list)):
            if hasattr(val, "item"):
                return float(val.item())
            if len(val) > 0:
                return float(val[0])
        return float(val)
    except:
        return 0.0

def analyze_recent_week(ticker, market_type, check_days):
    try:
        # データ取得
        df = yf.download(ticker, period="6mo", progress=False)
        
        # 【重要修正】データの「2重カラム」を強制的に1段にする
        # columns.nlevels > 1 はMultiIndexであることを意味します
        if isinstance(df.columns, pd.MultiIndex):
             df.columns = df.columns.get_level_values(0)
            
        if len(df) < 60: return [], None
        
        df = calculate_indicators(df)
        
        macd = df['MACD'].values
        hist = df['Hist'].values
        rsi = df['RSI'].values
        close = df['Close'].values
        dates = df.index
        
        daily_signals = []
        start_idx = len(df) - check_days
        
        # 安全に数値を取り出す (生存確認用)
        latest_price = safe_float(close[-1])
        
        for i in range(start_idx, len(df)):
            if i < 0: continue
            signals = []
            
            # 各指標の値を取得 (配列の場合は強制的にスカラーに変換)
            current_macd = safe_float(macd[i])
            current_hist = safe_float(hist[i])
            current_rsi = safe_float(rsi[i])
            current_close = safe_float(close[i])
                
            current_date = dates[i].strftime('%Y-%m-%d')
            
            prev_hist = safe_float(hist[i-1])
            prev_macd = safe_float(macd[i-1])
            
            # Signal列の取得
            prev_sig = safe_float(df['Signal'].values[i-1])
            curr_sig = safe_float(df['Signal'].values[i])

            # === A. 買いシグナル ===
            # 1. 2nd Attempt
            if current_macd < 0 and current_hist > 0:
                if np.any(hist[i-12:i-1] < 0):
                    start_look = max(0, i-100)
                    recent_hist_slice = hist[start_look:i+1]
                    recent_macd_slice = macd[start_look:i+1]
                    
                    signs = np.sign(recent_hist_slice)
                    # signsを1次元配列に平坦化
                    if signs.ndim > 1: signs = signs.flatten()
                    
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

            # 2. Re-entry
            if current_hist > 0 and current_hist > prev_hist:
                recent_squeeze = False
                for k in range(2, 7):
                    h = safe_float(hist[i-k])
                    m = safe_float(macd[i-k])
                    if h > 0 and h < (abs(m) * 0.10):
                        recent_squeeze = True
                        break
                if recent_squeeze:
                    signals.append("BUY: Re-entry")

            # === B. 売りシグナル ===
            price_5d = safe_float(close[i-5])
            rsi_5d = safe_float(rsi[i-5])
            
            # 1. RSI Divergence
            if (current_close > price_5d) and (current_rsi < rsi_5d) and (current_rsi > 60):
                signals.append("SELL: RSI Div")
            
            # 2. Squeeze Alert
            if current_hist > 0:
                if current_hist < (abs(current_macd) * 0.10):
                    if prev_hist > current_hist:
                        signals.append("SELL: Squeeze")
            
            # 3. Dead Cross
            if current_macd < curr_sig:
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
        return daily_signals, latest_price

    except Exception as e:
        # エラーが起きても停止させない
        return [], None

# ==========================================
# 3. メイン処理
# ==========================================
if st.button("分析を開始する", type="primary"):
    
    target_tickers = []
    if "日本株" in target_market:
        for t in jp_tickers: target_tickers.append((t, "JP"))
    if "米国株" in target_market:
        for t in us_tickers: target_tickers.append((t, "US"))
    
    if not target_tickers:
        st.warning("市場を選択してください。")
    else:
        st.write(f"全 {len(target_tickers)} 銘柄をスキャン中...")
        my_bar = st.progress(0)
        status_text = st.empty()
        
        all_events = []
        scanned_data = [] 
        total = len(target_tickers)
        
        for idx, (ticker, mkt) in enumerate(target_tickers):
            status_text.text(f"Scanning: {ticker} ({idx+1}/{total})")
            my_bar.progress((idx + 1) / total)
            
            events, price = analyze_recent_week(ticker, mkt, days_to_check)
            all_events.extend(events)
            if price:
                scanned_data.append({"Ticker": ticker, "Latest Price": price})
        
        status_text.text("完了！")
        my_bar.empty()

        if all_events:
            df_res = pd.DataFrame(all_events)
            df_res = df_res.sort_values(by=["Date", "Country", "Ticker"], ascending=[False, True, True])
            
            st.success(f"{len(df_res)} 件のシグナルを検出しました。")
            
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
            
            csv = df_res.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="CSVデータをダウンロード",
                data=csv,
                file_name='stock_signals.csv',
                mime='text/csv',
            )
        else:
            st.info("指定期間内にシグナルは検出されませんでした。")

        # 生存確認用リスト（折りたたみ）
        with st.expander("詳細：スキャン済み銘柄の最新株価"):
            if scanned_data:
                st.dataframe(pd.DataFrame(scanned_data), use_container_width=True)
            else:
                st.write("データ取得に成功した銘柄がありませんでした。")

else:
    st.write("左のサイドバーで設定を行い、「分析を開始する」ボタンを押してください。")
