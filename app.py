import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# ページ設定 (ver 3.1: 銘柄大幅追加版)
# ==========================================
st.set_page_config(page_title="株価シグナル検知アプリ", page_icon="📈", layout="wide")
st.title("📈 株価トレンド判定アルゴリズム (ver 3.1)")

# ==========================================
# 免責事項
# ==========================================
st.warning("""
**【免責事項・ご利用上の注意】**
本アプリは機械的な計算結果を表示するものであり、**特定の銘柄の売買を推奨するものではありません。**
投資判断はご自身の責任において行ってください。
""")

# ==========================================
# 0. 銘柄名マッピング (追加分含む全184+α銘柄)
# ==========================================
ticker_names = {
    # --- 日本株 (元リスト + 新規追加184銘柄) ---
    "1319.T": "NF日経300", "1553.T": "MXS東海", "5075.T": "アップコン", "1812.T": "鹿島建設",
    "1777.T": "川崎設備工業", "1438.T": "岐阜造園", "1893.T": "五洋建設", "1803.T": "清水建設",
    "1928.T": "積水ハウス", "1811.T": "錢高組", "1801.T": "大成建設", "1766.T": "東建コーポ",
    "1892.T": "徳倉建設", "1946.T": "トーエネック", "1444.T": "ニッソウ", "1738.T": "NITTOH",
    "275A.T": "ハンワホームズ", "1869.T": "名工建設", "1870.T": "矢作建設工業", "1780.T": "ヤマウラ",
    "2209.T": "井村屋G", "2811.T": "カゴメ", "2224.T": "コモ", "2902.T": "太陽化学",
    "2053.T": "中部飼料", "2551.T": "マルサンアイ", "2207.T": "meito", "2806.T": "ユタカフーズ",
    "3571.T": "ソトー", "3202.T": "ダイトウボウ", "3205.T": "ダイドーリミテッド", "3577.T": "東海染工",
    "3524.T": "日東製網", "3504.T": "丸八HD", "3958.T": "笹徳印刷", "3947.T": "ダイナパック",
    "4206.T": "アイカ工業", "7928.T": "旭化学工業", "4124.T": "大阪油化工業", "4616.T": "川上塗料",
    "4361.T": "川口化学工業", "4240.T": "クラスターT", "4125.T": "三和油化工業", "4063.T": "信越化学",
    "4463.T": "日華化学", "4920.T": "日本色材工業", "7950.T": "日本デコラックス", "7871.T": "フクビ化学",
    "4247.T": "ポバール興業", "7931.T": "未来工業", "4502.T": "武田薬品", "5020.T": "ENEOS",
    "5204.T": "石塚硝子", "5287.T": "イトーヨーギョー", "5333.T": "NGK", "5342.T": "ジャニス工業",
    "5386.T": "鶴弥", "5363.T": "TYK", "5332.T": "TOTO", "5271.T": "トーヨーアサノ",
    "7943.T": "ニチハ", "5343.T": "ニッコー", "5334.T": "日本特殊陶業", "5331.T": "ノリタケ",
    "5384.T": "FUJIMI", "5344.T": "MARUWA", "5356.T": "美濃窯業", "5482.T": "愛知製鋼",
    "5406.T": "神戸製鋼所", "5471.T": "大同特殊鋼", "5607.T": "中央可鍛工業", "5461.T": "中部鋼鈑",
    "5401.T": "日本製鉄", "5802.T": "住友電気工業", "5952.T": "アマテイ", "3442.T": "MIEコーポ",
    "5979.T": "カネソウ", "5984.T": "兼房", "3441.T": "山王", "3447.T": "信和",
    "3422.T": "J-MAX", "523A.T": "セイワHD", "5918.T": "瀧上工業", "5992.T": "中央発條",
    "5994.T": "ファインシンター", "3439.T": "三ツ知", "5938.T": "LIXIL", "5947.T": "リンナイ",
    "6345.T": "アイチ", "6111.T": "旭精機工業", "6396.T": "宇野澤組鐵工所", "6225.T": "エコム",
    "6136.T": "OSG", "6103.T": "オークマ", "6346.T": "キクカワ", "6340.T": "澁谷工業",
    "6339.T": "新東工業", "6407.T": "CKD", "6267.T": "ゼネラルパッカー", "6342.T": "太平製作所",
    "6470.T": "大豊工業", "6325.T": "タカキタ", "6430.T": "ダイコク電機", "6439.T": "中日本鋳工",
    "6134.T": "FUJI", "6142.T": "富士精工", "6203.T": "豊和工業", "6465.T": "ホシザキ",
    "6586.T": "マキタ", "7011.T": "三菱重工", "6623.T": "愛知電機", "6718.T": "アイホン",
    "6899.T": "ASTI", "4062.T": "イビデン", "7751.T": "キヤノン", "6999.T": "KOA",
    "6846.T": "中央製作所", "6655.T": "東洋電機", "6797.T": "名古屋電機工業", "6651.T": "日東工業",
    "6676.T": "バッファロー", "6501.T": "日立製作所", "6702.T": "富士通", "6504.T": "富士電機",
    "6448.T": "ブラザー", "6508.T": "明電舎", "6615.T": "UMCエレ", "7283.T": "愛三工業",
    "7259.T": "アイシン", "7227.T": "アスカ", "7266.T": "今仙電機", "7012.T": "川崎重工",
    "6473.T": "ジェイテクト", "7245.T": "大同メタル", "6902.T": "デンソー", "6995.T": "東海理電",
    "7231.T": "トピー工業", "7203.T": "トヨタ自動車", "3116.T": "トヨタ紡織", "7282.T": "豊田合成",
    "7102.T": "日本車輌", "7241.T": "フタバ産業", "7220.T": "武蔵精密", "7213.T": "レシップHD",
    "7723.T": "愛知時計電機", "7747.T": "朝日インテック", "7780.T": "メニコン", "7953.T": "菊水化学",
    "7878.T": "光・彩", "7946.T": "光陽社", "7896.T": "セブン工業", "7875.T": "竹田iP",
    "7790.T": "バルコス", "7870.T": "福島印刷", "7805.T": "プリントネット", "7975.T": "リヒトラブ",
    "9502.T": "中部電力", "9531.T": "東京ガス", "9533.T": "東邦ガス", "9073.T": "京極運輸商事",
    "9076.T": "セイノーHD", "9040.T": "大宝運輸", "9022.T": "JR東海", "9048.T": "名鉄",
    "9359.T": "伊勢湾海運", "9368.T": "キムラユニティー", "9306.T": "東陽倉庫", "9310.T": "日本トランスシティ",
    "9357.T": "名港海運", "4667.T": "アイサンテクノ", "418A.T": "ウリドキ", "2351.T": "ASJ",
    "3808.T": "OKウェブ", "5589.T": "オートサーバー", "3775.T": "ガイアックス", "3670.T": "協立情報通信",
    "9428.T": "クロップス", "3739.T": "コムシード", "3771.T": "システムリサーチ", "2480.T": "シスロケ",
    "3974.T": "SCAT", "550A.T": "ソフトテックス", "9476.T": "中央経済社HD", "9402.T": "中部日本放送",
    "4072.T": "電算システムHD", "4430.T": "東海ソフト", "2329.T": "東北新社", "4439.T": "東名",
    "2327.T": "日鉄ソリューションズ", "5241.T": "日本OA研究所", "4196.T": "ネオマーケティング", "3842.T": "ネクストジェン",
    "3922.T": "PR TIMES", "9471.T": "文溪堂", "4445.T": "リビンT", "3384.T": "アークコア",
    "3419.T": "アートグリーン", "9914.T": "植松商会", "7485.T": "岡谷鋼機", "8076.T": "カノークス",
    "3320.T": "クロスプラス", "3035.T": "ケイティケイ", "3543.T": "コメダ", "8130.T": "サンゲツ",
    "7607.T": "進和", "9987.T": "スズケン", "7675.T": "セントラルフォレスト", "8225.T": "タカチホ",
    "9982.T": "タキヒヨー", "8145.T": "中部水産", "8071.T": "東海エレ", "8015.T": "豊田通商",
    "9913.T": "日邦産業", "3559.T": "ピーバンドットコム", "8228.T": "マルイチ産商", "3321.T": "ミタチ産業",
    "8285.T": "三谷産業", "8031.T": "三井物産", "546A.T": "MIRAINI", "7488.T": "ヤガミ",
    "2722.T": "IKホールディングス", "3184.T": "ICDA", "7412.T": "アトム", "2753.T": "あみやき亭",
    "3028.T": "アルペン", "7630.T": "壱番屋", "8160.T": "木曽路", "3549.T": "クスリのアオキ",
    "259A.T": "ケイ・ウノ", "2780.T": "コメ兵HD", "3032.T": "ゴルフ・ドゥ", "9900.T": "サガミHD",
    "2734.T": "サーラ", "9969.T": "ショクブン", "7118.T": "伸和HD", "3066.T": "JBイレブン",
    "3086.T": "Jフロント", "7135.T": "ジャパンクラフト", "7649.T": "スギHD", "2681.T": "セカンドリテイリング",
    "3186.T": "ネクステージ", "7682.T": "浜木綿", "9956.T": "バローHD", "2778.T": "パレモ・HD",
    "138A.T": "光フードサービス", "7514.T": "ヒマラヤ", "3346.T": "ヒロタグループ", "3138.T": "富士山マガジン",
    "7593.T": "VTホールディングス", "3091.T": "ブロンコビリー", "7129.T": "ミアヘルサHD", "8190.T": "ヤマナカ",
    "3221.T": "ヨシックスHD", "3556.T": "リネットジャパン", "7389.T": "あいちFG", "8361.T": "大垣共立銀行",
    "7322.T": "三十三FG", "7380.T": "十六FG", "8522.T": "名古屋銀行", "8368.T": "百五銀行",
    "8309.T": "三井住友トラスト", "8316.T": "三井住友FG", "8306.T": "三菱UFJ", "8609.T": "岡三証券G",
    "8601.T": "大和証券G", "8616.T": "東海東京", "8604.T": "野村HD", "8725.T": "MS&AD",
    "377A.T": "エージェントIGH", "8904.T": "AVANTIA", "2983.T": "アールプランナー", "2986.T": "LAホールディングス",
    "8891.T": "AMGHD", "1878.T": "大東建託", "3469.T": "デュアルタップ", "5530.T": "日本システムバンク",
    "3461.T": "パルマ", "8803.T": "平和不動産", "8995.T": "誠建設工業", "3494.T": "マリオン",
    "3232.T": "三重交通GHD", "391A.T": "山忠", "9334.T": "アイビスHD", "9330.T": "揚羽",
    "246A.T": "アスア", "640A.T": "ASNOVA", "6029.T": "アトラグループ", "4760.T": "アルファ",
    "6565.T": "ABホテル", "624A.T": "かがやきHD", "4707.T": "キタック", "7075.T": "QLSHD",
    "6036.T": "KeePer技研", "6547.T": "グリーンズ", "7059.T": "コプロHD", "2376.T": "サイネックス",
    "2185.T": "シイエム・シイ", "2435.T": "シダー", "2169.T": "CDS", "6074.T": "JSS",
    "7073.T": "ジェイック", "2479.T": "ジェイテック", "6055.T": "ジャパンマテリアル", "9170.T": "成友興業",
    "9793.T": "ダイセキ", "2139.T": "中広", "2485.T": "ティア", "7362.T": "T.S.I",
    "8920.T": "東祥", "9643.T": "中日本興業", "9249.T": "日本エコシステム", "4658.T": "日本空調サービス",
    "6025.T": "日本PCサービス", "212A.T": "フィットイージー", "9221.T": "フルハシEPO", "2467.T": "VLCセキュリティ",
    "2424.T": "ブラス", "9664.T": "御園座", "6564.T": "ミダックHD", "7076.T": "名南M&A",
    "7369.T": "メイホーHD", "4732.T": "USS", "4681.T": "リゾートトラスト", "4691.T": "ワシントンホテル",
    "9984.T": "ソフトバンクG", "6758.T": "ソニーG", "6954.T": "ファナック", "6857.T": "アドバンテスト",
    "8035.T": "東京エレクトロン", "6146.T": "ディスコ", "6920.T": "レーザーテック", "6098.T": "リクルート",
    "4661.T": "オリエンタルランド", "9202.T": "ANA", "9201.T": "JAL", "8801.T": "三井不動産",
    "8802.T": "三菱地所", "8058.T": "三菱商事", "8001.T": "伊藤忠", "8002.T": "丸紅",
    "6367.T": "ダイキン", "4568.T": "第一三共", "4503.T": "アステラス", "2914.T": "JT",
    "3382.T": "セブン&アイ", "9983.T": "ファーストリテイリング", "1605.T": "INPEX", "7707.T": "PSS",
    "7532.T": "パンパシHD", "9401.T": "TBS", "8591.T": "オリックス", "4385.T": "メルカリ",
    "6993.T": "大黒屋", "6963.T": "ローム", "4091.T": "日本酸素", "3563.T": "F&L Life",
    "4476.T": "AI CROSS", "4165.T": "プレイド", "4188.T": "三菱ケミカル", "4755.T": "楽天G",
    "6723.T": "ルネサス", "7735.T": "SCREEN", "6701.T": "NEC", "6503.T": "三菱電機",
    "7267.T": "ホンダ", "7201.T": "日産", "7270.T": "SUBARU", "7269.T": "スズキ",
    "6301.T": "コマツ", "6273.T": "SMC", "6113.T": "アマダ", "8766.T": "東京海上",
    "2413.T": "エムスリー", "4689.T": "LINEヤフー", "3659.T": "ネクソン", "9735.T": "セコム",
    "8267.T": "イオン", "2801.T": "キッコーマン", "2802.T": "味の素", "2503.T": "キリンHD",
    "4911.T": "資生堂", "4519.T": "中外製薬", "4523.T": "エーザイ", "4543.T": "テルモ",
    "5411.T": "JFE", "3402.T": "東レ", "6981.T": "村田製作所", "9613.T": "NTTデータ",
    "7832.T": "バンナム", "9501.T": "東電",
    
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
# 1. 銘柄リスト定義
# ==========================================
# 日本株 (日経主力)
jp_core = [
    8035, 6857, 6146, 6723, 6920, 6954, 7735, 6501, 6701, 6702, 6503, 7267, 7201, 7270, 7269,
    6301, 6367, 7011, 6273, 6113, 8306, 8316, 8411, 8766, 8725, 8604, 9432, 9433, 9434, 2413,
    4661, 4689, 3659, 9735, 9983, 3382, 8267, 2801, 2802, 2503, 2914, 4911, 4568, 4502, 4503,
    4519, 4523, 4543, 5401, 5411, 1605, 5020, 3402, 4063, 6981, 7974, 9613, 7832, 9501
]

# 日本株 (追加・東海エリア・中小型銘柄リスト)
jp_added_raw = [
    "1319", "1553", "5075", "1812", "1777", "1438", "1893", "1803", "1928", "1811", "1801", "1766",
    "1892", "1946", "1444", "1738", "275A", "1869", "1870", "1780", "2209", "2811", "2224", "2902",
    "2053", "2551", "2207", "2806", "3571", "3202", "3205", "3577", "3524", "3504", "3958", "3947",
    "4206", "7928", "4124", "4616", "4361", "4240", "4125", "4063", "4463", "4920", "7950", "7871",
    "4247", "7931", "4502", "5020", "5204", "5287", "5333", "5342", "5386", "5363", "5332", "5271",
    "7943", "5343", "5334", "5331", "5384", "5344", "5356", "5482", "5406", "5471", "5607", "5461",
    "5401", "5802", "5952", "3442", "5979", "5984", "3441", "3447", "3422", "523A", "5918", "5992",
    "5994", "3439", "5938", "5947", "6345", "6111", "6396", "6225", "6136", "6103", "6346", "6340",
    "6339", "6407", "6267", "6342", "6470", "6325", "6430", "6439", "6134", "6142", "6203", "6465",
    "6586", "7011", "6623", "6718", "6899", "4062", "7751", "6999", "6846", "6655", "6797", "6651",
    "6676", "6501", "6702", "6504", "6448", "6508", "6615", "7283", "7259", "7227", "7266", "7012",
    "6473", "7245", "6902", "6995", "7231", "7203", "3116", "7282", "7102", "7241", "7220", "7213",
    "7723", "7747", "7780", "7953", "7878", "7946", "7896", "7875", "7790", "7870", "7805", "7975",
    "9502", "9531", "9533", "9073", "9076", "9040", "9022", "9048", "9359", "9368", "9306", "9310",
    "9357", "4667", "418A", "2351", "3808", "5589", "3775", "3670", "9428", "3739", "3771", "2480",
    "3974", "550A", "9476", "9402", "4072", "4430", "2329", "4439", "2327", "5241", "4196", "3842",
    "3922", "9471", "4445", "3384", "3419", "9914", "7485", "8076", "3320", "3035", "3543", "8130",
    "7607", "9987", "7675", "8225", "9982", "8145", "8071", "8015", "9913", "3559", "8228", "3321",
    "8285", "8031", "546A", "7488", "2722", "3184", "7412", "2753", "3028", "7630", "8160", "3549",
    "259A", "2780", "3032", "9900", "2734", "9969", "7118", "3066", "3086", "7135", "7649", "2681",
    "3186", "7682", "9956", "2778", "138A", "7514", "3346", "3138", "7593", "3091", "7129", "8190",
    "3221", "3556", "7389", "8361", "7322", "7380", "8522", "8368", "8309", "8316", "8306", "8609",
    "8601", "8616", "8604", "8725", "377A", "8904", "2983", "2986", "8891", "1878", "3469", "5530",
    "3461", "8803", "8995", "3494", "3232", "391A", "9334", "9330", "246A", "640A", "6029", "4760",
    "6565", "624A", "4707", "7075", "6036", "6547", "7059", "2376", "2185", "2435", "2169", "6074",
    "7073", "2479", "6055", "9170", "9793", "2139", "2485", "7362", "8920", "9643", "9249", "4658",
    "6025", "212A", "9221", "2467", "2424", "9664", "6564", "7076", "7369", "4732", "4681", "4691"
]

# チッカー変換 (.T 付与)
jp_core_tickers = sorted([f"{t}.T" for t in set(jp_core)])
jp_added_tickers = sorted([f"{t}.T" if not t.endswith(".T") else t for t in set(jp_added_raw)])

# 米国株
us_tickers = sorted(list(set([
    "NVDA", "AAPL", "MSFT", "AMZN", "TSLA", "META", "GOOGL", "GOOG", "AVGO", "AMD",
    "QCOM", "TXN", "AMAT", "INTC", "MU", "LRCX", "ADI", "NFLX", "ADBE", "CSCO",
    "CRM", "PANW", "INTU", "COST", "PEP", "TMUS", "CMCSA", "AMGN", "ISRG", "BKNG", "VRTX"
])))

# ==========================================
# サイドバー設定
# ==========================================
st.sidebar.header("設定")
target_lists = st.sidebar.multiselect(
    "銘柄リストから選択",
    ["日本株 (主力)", "日本株 (追加・東海エリア等)", "米国株 (主力)"],
    default=["日本株 (追加・東海エリア等)"]
)

st.sidebar.subheader("個別の銘柄コードを追加")
custom_input = st.sidebar.text_input("コードを入力 (例: 9101, TSLA)")
st.sidebar.caption("※日本株は数字4桁でOK")
days_to_check = st.sidebar.slider("検索期間 (過去X日)", 1, 30, 10)

# ==========================================
# 2. ロジック関数
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
        macd, hist, rsi, close = df['MACD'].values, df['Hist'].values, df['RSI'].values, df['Close'].values
        dates = df.index

        daily_signals = []
        start_idx = len(df) - (check_days + 1)
        if start_idx < 0: start_idx = 0

        latest_price = safe_float(close[-1])
        stock_name = ticker_names.get(ticker, ticker)

        for i in range(start_idx, len(df)):
            if i < 0: continue
            signals = []
            c_macd, c_hist, c_rsi, c_close = safe_float(macd[i]), safe_float(hist[i]), safe_float(rsi[i]), safe_float(close[i])
            c_date = dates[i].strftime('%Y-%m-%d')
            p_hist, p_macd = safe_float(hist[i-1]), safe_float(macd[i-1])
            p_sig = safe_float(df['Signal'].values[i-1])
            c_sig = safe_float(df['Signal'].values[i])

            # A. 買いシグナル
            if c_macd < 0 and c_hist > 0:
                if np.any(hist[i-12:i-1] < 0):
                    start_look = max(0, i-100)
                    recent_hist, recent_macd = hist[start_look:i+1], macd[start_look:i+1]
                    signs = np.sign(recent_hist)
                    if signs.ndim > 1: signs = signs.flatten()
                    for k in range(1, len(signs)):
                        if signs[k] == 0: signs[k] = signs[k-1]
                    blocks = []
                    if len(signs) > 0:
                        c_s, c_l, s_i = signs[0], 0, 0
                        for k, s in enumerate(signs):
                            if s == c_s: c_l += 1
                            else: blocks.append({'sign': c_s, 'len': c_l, 'end': k-1, 'start': s_i}); c_s, c_l, s_i = s, 1, k
                        blocks.append({'sign': c_s, 'len': c_l, 'end': len(signs)-1, 'start': s_i})
                    if len(blocks) >= 4:
                        v2, h, v1 = blocks[-2], blocks[-3], blocks[-4]
                        if v2['sign'] < 0 and h['sign'] > 0 and v1['sign'] < 0 and v2['len'] >= 2 and h['len'] >= 2 and v1['len'] >= 2:
                            v2_min, v1_min = np.min(recent_macd[v2['start']:v2['end']+1]), np.min(recent_macd[v1['start']:v1['end']+1])
                            if v2_min < v1_min * 0.95: signals.append("🟢 買う: 底打ち (Wボトム)")

            if c_hist > 0 and c_hist > p_hist:
                recent_squeeze = False
                for k in range(2, 7):
                    h, m = safe_float(hist[i-k]), safe_float(macd[i-k])
                    if h > 0 and h < (abs(m) * 0.10): recent_squeeze = True; break
                if recent_squeeze: signals.append("🟢 買う: 押し目 (Re-entry)")

            # B. 売りシグナル
            if (c_close > safe_float(close[i-5])) and (c_rsi < safe_float(rsi[i-5])) and (c_rsi > 60): signals.append("🔴 売る: 加熱感 (RSI乖離)")
            if c_hist > 0 and c_hist < (abs(c_macd) * 0.10) and p_hist > c_hist: signals.append("🔴 売る: スクイーズ")
            if c_macd < c_sig and p_macd >= p_sig: signals.append("🔴 売る: デッドクロス")

            if signals:
                daily_signals.append({
                    "Date": c_date, "Country": market_type, "Name": stock_name,
                    "Ticker": ticker, "Price": round(float(c_close), 2),
                    "Signals": ", ".join(signals)
                })
        return daily_signals, latest_price

    except Exception:
        return [], None

# ==========================================
# 3. メイン処理 (新規判定 & 履歴 ver3.1)
# ==========================================
if st.button("分析を開始する", type="primary"):

    target_tickers = set()
    if "日本株 (主力)" in target_lists:
        for t in jp_core_tickers: target_tickers.add((t, "JP"))
    if "日本株 (追加・東海エリア等)" in target_lists:
        for t in jp_added_tickers: target_tickers.add((t, "JP"))
    if "米国株 (主力)" in target_lists:
        for t in us_tickers: target_tickers.add((t, "US"))
        
    if custom_input:
        raw_inputs = custom_input.replace("、", ",").replace(" ", ",").split(",")
        for t in raw_inputs:
            t_clean = t.strip()
            if not t_clean: continue
            if (t_clean.isdigit() and len(t_clean) == 4) or t_clean.endswith("A"): 
                final_ticker, market = f"{t_clean}.T", "JP"
            else: 
                final_ticker, market = t_clean.upper(), ("JP" if ".T" in t_clean.upper() else "US")
            target_tickers.add((final_ticker, market))

    final_target_list = sorted(list(target_tickers))

    if not final_target_list:
        st.warning("銘柄を選択してください。")
    else:
        st.write(f"全 {len(final_target_list)} 銘柄をスキャン中...")
        my_bar = st.progress(0)
        status_text = st.empty()

        all_events = []
        scanned_data = [] 
        total = len(final_target_list)

        for idx, (ticker, mkt) in enumerate(final_target_list):
            s_name = ticker_names.get(ticker, ticker)
            status_text.text(f"Scanning ({idx+1}/{total}): {s_name} ({ticker})")
            my_bar.progress((idx + 1) / total)
            
            events, price = analyze_recent_week(ticker, mkt, days_to_check)
            all_events.extend(events)
            if price: scanned_data.append({"Name": s_name, "Ticker": ticker, "Latest Price": price})

        status_text.text("完了！")
        my_bar.empty()

        if all_events:
            df_res = pd.DataFrame(all_events)
            cols = ["Date", "Country", "Name", "Ticker", "Price", "Signals"]
            df_res = df_res[cols].sort_values(by=["Date", "Country", "Ticker"], ascending=[False, True, True])

            # --- 本日の新規・転換判定 ---
            st.divider()
            st.subheader("🔔 今日のエントリー候補 (新規・転換)")
            st.caption("※「買い」または「売り」の方向が**今日初めて**発生した銘柄のみ表示します。")

            latest_jp = df_res[df_res['Country']=="JP"]['Date'].max()
            latest_us = df_res[df_res['Country']=="US"]['Date'].max()

            fresh_list = []

            for ticker in df_res['Ticker'].unique():
                df_t = df_res[df_res['Ticker'] == ticker].sort_values('Date')
                if df_t.empty: continue

                latest_row = df_t.iloc[-1]
                l_date = latest_row['Date']
                l_mkt = latest_row['Country']
                l_sig_str = latest_row['Signals'] 

                target_date = latest_jp if l_mkt == "JP" else latest_us
                if pd.isna(target_date) or l_date != target_date:
                    continue 

                def get_direction_set(s):
                    s = str(s)
                    d_set = set()
                    if "買う" in s: d_set.add("BUY")
                    if "売る" in s: d_set.add("SELL")
                    return d_set

                current_dirs = get_direction_set(l_sig_str)
                status = "新規発生"

                if len(df_t) > 1:
                    prev_row = df_t.iloc[-2]
                    prev_sig_str = prev_row['Signals']
                    prev_dirs = get_direction_set(prev_sig_str)

                    if current_dirs == prev_dirs:
                        continue 

                    if ("BUY" in prev_dirs and "SELL" in current_dirs) or ("SELL" in prev_dirs and "BUY" in current_dirs):
                        prev_label = "買い" if "BUY" in prev_dirs else "売り"
                        status = f"🔄 転換 (前日: {prev_label})"

                row_dict = latest_row.to_dict()
                row_dict['Status'] = status
                fresh_list.append(row_dict)

            if fresh_list:
                df_fresh = pd.DataFrame(fresh_list)
                cols_fresh = ["Date", "Country", "Status", "Name", "Ticker", "Price", "Signals"]
                st.dataframe(
                    df_fresh[cols_fresh],
                    column_config={
                        "Date": "日付", "Country": "市場", "Status": "状態",
                        "Name": "銘柄名", "Ticker": "コード", 
                        "Price": st.column_config.NumberColumn("株価", format="%.2f"),
                        "Signals": "判定内容",
                    },
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("本日、新しく発生したシグナル（または転換）はありません。")

            # --- 過去のシグナル履歴 ---
            st.divider()
            st.subheader("📅 過去のシグナル履歴")
            st.dataframe(
                df_res,
                column_config={
                    "Date": "日付", "Country": "市場", "Name": "銘柄名", "Ticker": "コード",
                    "Price": st.column_config.NumberColumn("株価", format="%.2f"),
                    "Signals": "判定",
                },
                use_container_width=True, hide_index=True
            )
            csv = df_res.to_csv(index=False).encode('utf-8')
            st.download_button("全履歴CSVをダウンロード", csv, 'stock_signals.csv', 'text/csv')
        else:
            st.info("指定期間内にシグナルは検出されませんでした。")

        with st.expander("詳細：スキャン済み銘柄の最新株価"):
            if scanned_data: st.dataframe(pd.DataFrame(scanned_data), use_container_width=True)
            else: st.write("データ取得不可")

else:
    st.write("左のサイドバーでリストを選択するか、コードを入力して「分析を開始する」を押してください。")
