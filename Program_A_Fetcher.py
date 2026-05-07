import pandas as pd
import yfinance as yf
import shutil
import os
from datetime import datetime
import time

# 1. 強制停用時區快取
yf.set_tz_cache_location(None)

# 2. 強制刪除可能殘留的鎖定資料庫 (針對 GitHub Actions 環境)
cache_path = os.path.expanduser('~/.cache/py-yfinance')
if os.path.exists(cache_path):
    try:
        shutil.rmtree(cache_path)
        print("🧹 已清除 yfinance 殘留快取")
    except:
        pass
class DataFetcher:
    def __init__(self, token=None):
        self.hot_list = ['2330.TW','2317.TW','2454.TW','2303.TW','2603.TW','2609.TW','2382.TW','3231.TW','1513.TW','1504.TW','3481.TW','2409.TW','2308.TW','2357.TW','2618.TW','2610.TW']

    def fetch_market_snapshot(self):
        """[功能不刪減] 抓取全維度數據，並加入真實成交查證欄位"""
        for attempt in range(3):
            try:
                df_yf = yf.download(self.hot_list, period='1d', interval='1m', group_by='ticker', progress=False, threads=True)
                if df_yf.empty: continue
                all_data = []
                for ticker in self.hot_list:
                    try:
                        target = df_yf[ticker].dropna()
                        if target.empty: continue
                        last = target.iloc[-1]
                        curr_p = last['Close']
                        # [查證功能] 模擬掛單：買入看賣價(Ask), 賣出看買價(Bid)
                        # 台股高流動性股價差極小，以 0.05% 模擬真實點差
                        ask_p = curr_p * 1.0005 
                        bid_p = curr_p * 0.9995
                        # [流動性檢查] 1分鐘成交量需 > 100張 才視為「真實可成交」
                        is_liquid = True if last['Volume'] > 100 else False

                        all_data.append({
                            'stock_id': ticker.replace('.TW',''),
                            'last_price': curr_p,
                            'open_price': target['Open'].iloc[0],
                            'high_price': target['High'].max(),
                            'low_price': target['Low'].min(),
                            'amount': target['Volume'].sum(),
                            'ask_p': ask_p, 'bid_p': bid_p, 'is_liquid': is_liquid,
                            'change_rate': ((curr_p - target['Open'].iloc[0]) / target['Open'].iloc[0]) * 100
                        })
                    except: continue
                return pd.DataFrame(all_data)
            except: time.sleep(2)
        return pd.DataFrame()

    def fetch_index_status(self):
        """[原功能保留] 抓取大盤急殺判定數據"""
        try:
            idx = yf.Ticker("^TWII").fast_info
            return {'change_rate': ((idx['last_price'] - idx['previous_close']) / idx['previous_close']) * 100, 
                    'drop_from_high': ((idx['day_high'] - idx['last_price']) / idx['day_high']) * 100}
        except: return None

    def fetch_tick_details(self, stock_id):
        """[原功能保留] 抓取成交明細模擬外盤力道"""
        try:
            df = yf.Ticker(f"{stock_id}.TW").history(period="1d", interval="1m").tail(15)
            return pd.DataFrame([{'tick_type': 1 if r['Close'] >= (r['Open']+r['High']+r['Low'])/3 else 0, 
                                  'price': r['Close'], 'volume': r['Volume']} for _, r in df.iterrows()])
        except: return pd.DataFrame()

def get_data_service(token=None): return DataFetcher(token)
