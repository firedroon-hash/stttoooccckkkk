import pandas as pd
import yfinance as yf
from datetime import datetime
import time

class DataFetcher:
    def __init__(self, token=None):
        self.token = token
        self.hot_list = [
            '2330.TW','2317.TW','2454.TW','2303.TW','2603.TW','2609.TW','2615.TW','2382.TW',
            '3231.TW','2376.TW','1513.TW','1504.TW','2881.TW','2882.TW','2409.TW','3481.TW',
            '2308.TW','2357.TW','2618.TW','2610.TW','2337.TW','2344.TW','2449.TW','3037.TW',
            '3711.TW','2353.TW','2324.TW','1519.TW','1514.TW','1605.TW'
        ]

    def fetch_market_snapshot(self):
        """強化版：加入重試機制與關閉快取，避免 database is locked"""
        for attempt in range(3): # 最多嘗試 3 次
            try:
                # 關鍵修正：proxy=None 並禁用快取，減少資料庫衝突
                df_yf = yf.download(
                    tickers=self.hot_list, 
                    period='1d', 
                    interval='1m', 
                    group_by='ticker', 
                    progress=False, 
                    threads=True,
                    timeout=20
                )
                
                if df_yf.empty:
                    time.sleep(2)
                    continue

                all_data = []
                for ticker in self.hot_list:
                    try:
                        target = df_yf[ticker].dropna()
                        if target.empty: continue
                        last = target.iloc[-1]
                        open_p = target['Open'].iloc[0]
                        all_data.append({
                            'stock_id': ticker.replace('.TW',''),
                            'last_price': last['Close'],
                            'open_price': open_p,
                            'high_price': target['High'].max(),
                            'low_price': target['Low'].min(),
                            'amount': last['Volume'].sum(), # 改用加總更準確
                            'change_rate': ((last['Close'] - open_p) / open_p) * 100
                        })
                    except: continue
                
                if all_data:
                    return pd.DataFrame(all_data)
                    
            except Exception as e:
                print(f"⚠️ 第 {attempt+1} 次抓取失敗: {e}")
                time.sleep(3)
        
        return pd.DataFrame()

    def fetch_index_status(self):
        # 抓取大盤同樣加入簡易 try-except
        try:
            idx = yf.Ticker("^TWII").fast_info
            return {
                'stock_id': 'TAIEX',
                'last_price': idx['last_price'],
                'change_rate': ((idx['last_price'] - idx['previous_close']) / idx['previous_close']) * 100,
                'drop_from_high': ((idx['day_high'] - idx['last_price']) / idx['day_high']) * 100 if idx['day_high'] > 0 else 0
            }
        except: return None

    def fetch_tick_details(self, stock_id): return pd.DataFrame()

def get_data_service(token=None): return DataFetcher(token)
