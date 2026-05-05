# ==============================================================================
# 程式名稱：Program_A_Fetcher.py (全維度數據中心 - v38.1 全功能不刪減版)
# ------------------------------------------------------------------------------
# 完整性查核：
# 1. 保留 A 程式初版所有數據維度 (開盤、現價、成交量、漲幅)。
# 2. 保留 TAIEX 大盤即時數據流 (供 B/C 程序判定急殺攔截)。
# 3. 保留 Tick 明細接口 (以 1m 微觀數據模擬，確保 C 程序外盤佔比邏輯不失效)。
# 4. 新增：Open_Price 欄位，確保 D 程式能分析「開盤至今落差」。
# ==============================================================================

import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np

class DataFetcher:
    def __init__(self, token=None):
        # 保留 FinMind Token 接口以相容舊 B 程序，但主要使用 yfinance 加速
        self.token = token
        # 擴充至 40 檔核心熱門標的，涵蓋權值、AI、航運、重電
        self.hot_list = [
            '2330.TW','2317.TW','2454.TW','2303.TW','2603.TW','2609.TW','2615.TW','2382.TW',
            '3231.TW','2376.TW','1513.TW','1504.TW','2881.TW','2882.TW','2409.TW','3481.TW',
            '2308.TW','2357.TW','2618.TW','2610.TW','2337.TW','2344.TW','2449.TW','3037.TW',
            '3711.TW','2353.TW','2324.TW','1519.TW','1514.TW','1605.TW', '1513.TW', '1101.TW',
            '2606.TW', '2617.TW', '1608.TW', '1609.TW', '2368.TW', '3035.TW', '3661.TW', '3017.TW'
        ]

    def fetch_market_snapshot(self):
        """[功能 3] 抓取全市場即時快照 (熱門股加速版)"""
        try:
            # 使用多執行緒批次抓取
            df_yf = yf.download(self.hot_list, period='1d', interval='1m', group_by='ticker', progress=False, threads=True)
            all_data = []
            
            for ticker in self.hot_list:
                try:
                    target = df_yf[ticker].dropna()
                    if target.empty: continue
                    last = target.iloc[-1]
                    
                    # 補齊所有 B 程式所需欄位
                    all_data.append({
                        'stock_id': ticker.replace('.TW',''),
                        'last_price': last['Close'],
                        'open_price': target['Open'].iloc[0],
                        'high_price': target['High'].max(),
                        'low_price': target['Low'].min(),
                        'amount': last['Volume'],
                        # 漲幅計算 (與開盤相比)
                        'change_rate': ((last['Close'] - target['Open'].iloc[0]) / target['Open'].iloc[0]) * 100
                    })
                except: continue
            
            return pd.DataFrame(all_data)
        except Exception as e:
            print(f"❌ 數據抓取失敗: {e}")
            return pd.DataFrame()

    def fetch_index_status(self):
        """[新增防線] 抓取加權指數即時狀態 - 供判定「急殺」"""
        try:
            # 獲取大盤加權指數 (^TWII)
            idx = yf.Ticker("^TWII").fast_info
            curr = idx['last_price']
            prev = idx['previous_close']
            high = idx['day_high']
            
            return {
                'stock_id': 'TAIEX',
                'last_price': curr,
                'change_rate': ((curr - prev) / prev) * 100,
                # 計算從今日高點回落的比例 (防線 B 關鍵數據)
                'drop_from_high': ((high - curr) / high) * 100 if high > 0 else 0
            }
        except:
            return None

    def fetch_tick_details(self, stock_id):
        """[新增防線] 模擬成交明細 - 供偵測「主力內外盤」"""
        try:
            # 抓取最近 15 分鐘的微觀數據來模擬 Tick
            ticker = yf.Ticker(f"{stock_id}.TW")
            df_hist = ticker.history(period="1d", interval="1m").tail(15)
            
            if df_hist.empty: return pd.DataFrame()

            ticks = []
            for _, row in df_hist.iterrows():
                # 模擬邏輯：收盤價 > 分盤均價視為買盤(1)，反之為賣盤(0)
                avg_p = (row['Open'] + row['High'] + row['Low']) / 3
                tick_type = 1 if row['Close'] >= avg_p else 0
                ticks.append({'tick_type': tick_type, 'price': row['Close'], 'volume': row['Volume']})
            
            return pd.DataFrame(ticks)
        except:
            return pd.DataFrame()

def get_data_service(token=None):
    return DataFetcher(token)
