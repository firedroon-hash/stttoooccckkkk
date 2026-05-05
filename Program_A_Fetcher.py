import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np

class DataFetcher:
    def __init__(self, token=None):
        # 精選 30 檔高流動性標的，確保監控效率與速度
        self.hot_list = [
            '2330.TW','2317.TW','2454.TW','2303.TW','2603.TW','2609.TW','2615.TW','2382.TW',
            '3231.TW','2376.TW','1513.TW','1504.TW','2881.TW','2882.TW','2409.TW','3481.TW',
            '2308.TW','2357.TW','2618.TW','2610.TW','2337.TW','2344.TW','2449.TW','3037.TW',
            '3711.TW','2353.TW','2324.TW','1519.TW','1514.TW','1605.TW'
        ]

    def fetch_market_snapshot(self):
        """利用 yfinance 批次下載功能，一次抓取所有標的"""
        try:
            # 開啟 threads=True 進行多執行緒加速
            df_yf = yf.download(self.hot_list, period='1d', interval='1m', group_by='ticker', progress=False, threads=True)
            all_data = []
            
            for ticker in self.hot_list:
                try:
                    target = df_yf[ticker].dropna()
                    if target.empty: continue
                    last = target.iloc[-1]
                    # 計算今日漲幅 (相較於今日開盤價)
                    open_p = target['Open'].iloc[0]
                    curr_p = last['Close']
                    all_data.append({
                        'stock_id': ticker.replace('.TW',''),
                        'last_price': curr_p,
                        'amount': last['Volume'],
                        'change_rate': ((curr_p - open_p) / open_p) * 100
                    })
                except: continue
            
            return pd.DataFrame(all_data)
        except Exception as e:
            print(f"❌ 數據抓取失敗: {e}")
            return pd.DataFrame()

    def fetch_index_status(self):
        """快速獲取大盤漲跌"""
        try:
            idx = yf.Ticker("^TWII").fast_info
            return {
                'stock_id': 'TAIEX',
                'change_rate': ((idx['last_price'] - idx['previous_close']) / idx['previous_close']) * 100,
                'last_price': idx['last_price']
            }
        except: return None

    def fetch_tick_details(self, stock_id):
        # 回傳空 Dataframe 讓 B 程式套用預設 0.5 外盤比，節省抓取時間
        return pd.DataFrame()

def get_data_service(token=None): return DataFetcher(token)
