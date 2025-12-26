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
# 【重要】免責事項・注意喚起
# ==========================================
st.warning("""
**【免責事項・ご利用上の注意】**
本アプリは、過去の株価データに基づき、特定のアルゴリズム（MACD、RSI等）によるシグナルを機械的に抽出・表示するツールです。
**特定の銘柄の売買を推奨・勧誘するものではありません。**
投資に関する最終的な決定は、ご自身の判断と責任において行ってください。本アプリの情報を用いて利用者が行う一切の行為について、開発者は何ら責任を負うものではありません。
""")

# ==========================================
# 0. 銘柄名マッピング (主要銘柄の名称定義)
# ==========================================
ticker_names = {
    # --- 日本株 ---
    "7203.T": "トヨタ自動車", "9984.T": "ソフトバンクG", "6758.T": "ソニーG",
    "9432.T": "NTT", "9433.T": "KDDI", "9434.T": "ソフトバンク",
    "8306.T": "三菱UFJ", "8316.T": "三井住友FG", "8411.T": "みずほFG",
    "7974.T": "任天堂", "6954.T": "ファナック", "6857.T": "アドバンテスト",
    "8035.T": "東京エレクトロン", "6146.T": "ディスコ", "6920.T": "レーザーテック",
    "6098.T": "リクルート", "4661.T": "オリエンタルランド", "6501.T": "日立製作所",
    "9202.T": "ANA", "9201.T": "JAL", "8801.T": "三井不動産", "8802.T": "三菱地所",
    "8058.T": "三菱商事", "8031.T": "三井物産", "8001.T": "伊藤忠", "8002.T": "丸紅",
    "6367.T": "ダイキン", "4568.T": "第一三共", "4502.T": "武田薬品", "4503.T": "アステラス",
    "2914.T": "JT", "3382.T": "セブン&アイ", "9983.T": "ファーストリテイリング",
    "5401.T": "日本製鉄", "1605.T": "INPEX", "7011.T": "三菱重工",
    "7707.T": "PSS", "7532.T": "パンパシHD", "9401.T": "TBS", "8591.T": "オリックス",
    "4385.T": "メルカリ", "6993.T": "大黒屋", "6963.T": "ローム", "4091.T": "日本酸素",
    "3563.T": "F&L Life", "4476.T": "AI CROSS", "4165.T": "プレイド", "4188.T": "三菱ケミカル",
    "4755.T": "楽天G", "6723.T": "ルネサス", "7735.T": "SCREEN",
    "6701.T": "NEC", "6702.T": "富士通", "6503.T": "三菱電機",
    "7267.T": "ホンダ", "7201.T": "日産", "7270.T": "SUBARU", "7269.T": "スズキ",
    "6301.T": "コマツ", "6273.T": "SMC", "6113.T": "アマダ",
    "8766.T": "東京海上", "8725.T": "MS&AD", "8604.T": "野村HD",
    "2413.T": "エムスリー", "4689.T": "LINEヤフー", "3659.T": "ネクソン", "9735.T": "セコム",
    "8267.T": "イオン", "2801.T": "キッコーマン", "2802.T": "味の素", "2503.T": "キリンHD",
    "4911.T": "資生堂", "4519.T": "中外製薬", "4523.T": "エーザイ", "4543.T": "テルモ",
    "5411.T": "JFE", "5020.T": "ENEOS", "3402.T": "東レ", "4063.T": "信越化学",
    "6981.T": "村田製作所", "9613.T": "NTTデータ", "7832.T": "バンナム", "9501.T": "東電",
    # --- 米国株 ---
    "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon",
    "TSLA": "Tesla", "META": "Meta", "GOOGL": "Google (A)", "GOOG": "Google (C)",
    "NFLX": "Netflix", "ADBE": "Adobe", "INTC": "Intel", "AMD": "AMD",
    "QCOM": "Qualcomm", "CSCO": "Cisco", "PEP": "PepsiCo", "COST": "Costco",
    "AMAT": "Applied Materials", "MU": "Micron", "TXN": "Texas Inst",
    "AVGO": "Broadcom", "LRCX": "Lam Research", "ADI": "Analog Devices",
    "CRM": "Salesforce", "PANW": "Palo Alto", "INTU": "Intuit",
    "TMUS": "T-Mobile", "CMCSA": "Comcast", "AMGN": "Amgen",
    "ISRG": "Intuitive Surg", "BKNG": "Booking", "VRTX": "Vertex"
}

# ==========================================
# 1. 銘柄リスト定義 (デフォルトリスト)
# ==========================================
jp_custom = [9202, 9201, 8801, 7203, 7707, 7532, 9984, 8031, 8001, 8002, 6758, 9401, 8802, 8591, 8058, 4385, 6993, 6963, 4091, 3563, 4476, 6098, 4165, 4188, 4755]
jp_core = [8035, 6857, 6146, 6723, 6920, 6954, 7735, 6501, 6701, 6702, 6503, 7267, 7201, 7270, 7269, 6301, 6367, 7011, 6273, 6113, 8306, 8316, 8411, 8766, 8725, 8604, 9432, 9433, 9434, 2413, 4661, 4689, 3659, 9735, 9983, 3382, 8267, 2801, 2802, 2503, 2914, 4911, 4568, 4502, 4503, 4519, 4523, 4543, 5401, 5411, 1605, 5020, 3402, 4063, 6981, 7974, 9613, 7832, 9501]
jp_tickers = sorted([f"{t}.T" for t in set(jp_custom + jp_core)])
us_tickers = sorted(list(set(["NVDA", "AAPL", "MSFT", "AMZN", "TSLA", "META", "GOOGL", "GOOG", "AVGO", "AMD", "QCOM", "TXN", "AMAT", "INTC", "MU", "LRCX", "ADI", "NFLX", "ADBE", "CSCO", "CRM", "PANW", "INTU", "COST", "PEP", "TMUS", "CMCSA", "AMGN", "ISRG", "BKNG", "VRTX"])))

# ==========================================
# サイドバー設定 (検索機能付き)
# ==========================================
st.sidebar.header("設定")

# 1. 既存リストからの選択
target_lists = st.sidebar.multiselect(
    "銘柄リストから選択", 
    ["日本株 (主力)", "米国株 (主力)"],
    default=["日本株 (主力)"]
)

# 2. 自由入力欄
st.sidebar.subheader("個別の銘柄コードを追加")
custom_input = st.sidebar.text_input(
    "コードを入力 (カンマ区切りで複数可)", 
    placeholder="例: 9101, TSLA"
)
st.sidebar.caption("※日本株は数字4桁でOK (自動で.Tがつきます)")

days_to_check = st.sidebar.slider("検索期間 (過去X日)", 1, 30, 10)

# ==========================================
# 2. ロジック関数 (変更なし)
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

def safe_float(val):
    try:
        if isinstance(val, (pd.Series, np.ndarray, list)):
            if hasattr(val, "item"): return float(val.item())
            if len(val) > 0: return float(val[0])
        return float(val)
    except:
        return 0.0

def analyze_recent_week(ticker, market_type, check_days):
    try:
        df = yf.download(ticker, period="6mo", progress=False)
        
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
        
        latest_price = safe_float(close[-1])
        stock_name = ticker_names.get(ticker, ticker) # 辞書になければコードを表示
        
        for i in range(start_idx, len(df)):
            if i < 0: continue
            signals = []
            
            # 各指標の値
            current_macd = safe_float(macd[i])
            current_hist = safe_float(hist[i])
            current_rsi = safe_float(rsi[i])
            current_close = safe_float(close[i])
            current_date = dates[i].strftime('%Y-%m-%d')
            prev_hist = safe_float(hist[i-1])
            prev_macd = safe_float(macd[i-1])
            prev_sig = safe_float(df['Signal'].values[i-1])
            curr_sig = safe_float(df['Signal'].values[i])

            # === A. 買いシグナル ===
            if current_macd < 0 and current_hist > 0:
                if np.any(hist[i-12:i-1] < 0):
                    start_look = max(0, i-100)
                    recent_hist = hist[start_look:i+1]
                    recent_macd = macd[start_look:i+1]
                    signs = np.sign(recent_hist)
                    if signs.ndim > 1: signs = signs.flatten()
                    for k in range(1, len(signs)):
                        if signs[k] == 0: signs[k] = signs[k-1]
                    blocks = []
                    if len(signs) > 0:
                        c_sign, c_len, s_idx = signs[0], 0, 0
                        for k, s in enumerate(signs):
                            if s == c_sign: c_len += 1
                            else:
                                blocks.append({'sign': c_sign, 'len': c_len, 'end': k-1, 'start': s_idx})
                                c_sign, c_len, s_idx = s, 1, k
                        blocks.append({'sign': c_sign, 'len': c_len, 'end': len(signs)-1, 'start': s_idx})
                    if len(blocks) >= 4:
                        v2, h, v1 = blocks[-2], blocks[-3], blocks[-4]
                        if v2['sign'] < 0 and h['sign'] > 0 and v1['sign'] < 0:
                            if v2['len'] >= 2 and h['len'] >= 2 and v1['len'] >= 2:
                                v2_min = np.min(recent_macd[v2['start']:v2['end']+1])
                                v1_min = np.min(recent_macd[v1['start']:v1['end']+1])
                                if v2_min < v1_min * 0.95:
                                    signals.append("🟢 買う: 底打ち (Wボトム)")

            if current_hist > 0 and current_hist > prev_hist:
                recent_squeeze = False
                for k in range(2, 7):
                    h = safe_float(hist[i-k])
                    m = safe_float(macd[i-k])
                    if h > 0 and h < (abs(m) * 0.10): recent_squeeze = True; break
                if recent_squeeze: signals.append("🟢 買う: 押し目 (Re-entry)")

            # === B. 売りシグナル ===
            price_5d = safe_float(close[i-5])
            rsi_5d = safe_float(rsi[i-5])
            if (current_close > price_5d) and (current_rsi < rsi_5d) and (current_rsi > 60):
                signals.append("🔴 売る: 加熱感 (RSI乖離)")
            if current_hist > 0 and current_hist < (abs(current_macd) * 0.10) and prev_hist > current_hist:
                signals.append("🔴 売る: スクイーズ")
            if current_macd < curr_sig and prev_macd >= prev_sig:
                signals.append("🔴 売る: デッドクロス")

            if signals:
                daily_signals.append({
                    "Date": current_date, "Country": market_type, "Name": stock_name,
                    "Ticker": ticker, "Price": round(float(current_close), 2),
                    "Signals": ", ".join(signals)
                })
        return daily_signals, latest_price

    except Exception:
        return [], None

# ==========================================
# 3. メイン処理 (検索ロジック追加)
# ==========================================
if st.button("分析を開始する", type="primary"):
    
    # 1. 検索対象リストを作成 (セットを使って重複排除)
    target_tickers = set()
    
    # A. 既存リストからの追加
    if "日本株 (主力)" in target_lists:
        for t in jp_tickers: target_tickers.add((t, "JP"))
    if "米国株 (主力)" in target_lists:
        for t in us_tickers: target_tickers.add((t, "US"))
        
    # B. 自由入力からの追加
    if custom_input:
        # 全角を半角に、カンマ区切りをリスト化
        raw_inputs = custom_input.replace("、", ",").replace(" ", ",").split(",")
        for t in raw_inputs:
            t_clean = t.strip()
            if not t_clean: continue
            
            # 日本株コード (4桁数字) なら自動で .T をつける
            if t_clean.isdigit() and len(t_clean) == 4:
                final_ticker = f"{t_clean}.T"
                market = "JP"
            else:
                final_ticker = t_clean.upper()
                # .Tが含まれていれば日本株扱い、なければ米国株扱い
                market = "JP" if ".T" in final_ticker else "US"
            
            target_tickers.add((final_ticker, market))
    
    # リスト化してソート
    final_target_list = sorted(list(target_tickers))
    
    if not final_target_list:
        st.warning("銘柄リストを選択するか、銘柄コードを入力してください。")
    else:
        st.write(f"全 {len(final_target_list)} 銘柄をスキャン中...")
        my_bar = st.progress(0)
        status_text = st.empty()
        
        all_events = []
        scanned_data = [] 
        total = len(final_target_list)
        
        for idx, (ticker, mkt) in enumerate(final_target_list):
            status_text.text(f"Scanning: {ticker} ({idx+1}/{total})")
            my_bar.progress((idx + 1) / total)
            
            events, price = analyze_recent_week(ticker, mkt, days_to_check)
            all_events.extend(events)
            
            s_name = ticker_names.get(ticker, ticker)
            if price: scanned_data.append({"Name": s_name, "Ticker": ticker, "Latest Price": price})
        
        status_text.text("完了！")
        my_bar.empty()

        if all_events:
            df_res = pd.DataFrame(all_events)
            cols = ["Date", "Country", "Name", "Ticker", "Price", "Signals"]
            df_res = df_res[cols]
            df_res = df_res.sort_values(by=["Date", "Country", "Ticker"], ascending=[False, True, True])
            
            st.success(f"{len(df_res)} 件のシグナルを検出しました。")
            st.dataframe(
                df_res,
                column_config={
                    "Date": "日付", "Country": "市場", "Name": "銘柄名",
                    "Ticker": "コード", "Price": st.column_config.NumberColumn("株価", format="%.2f"),
                    "Signals": "判定",
                },
                use_container_width=True, hide_index=True
            )
            csv = df_res.to_csv(index=False).encode('utf-8')
            st.download_button("CSVデータをダウンロード", csv, 'stock_signals.csv', 'text/csv')
        else:
            st.info("指定期間内にシグナルは検出されませんでした。")

        with st.expander("詳細：スキャン済み銘柄の最新株価"):
            if scanned_data:
                st.dataframe(pd.DataFrame(scanned_data), use_container_width=True)
            else:
                st.write("データ取得に成功した銘柄がありませんでした。")

else:
    st.write("左のサイドバーでリストを選択するか、コードを入力して「分析を開始する」を押してください。")
