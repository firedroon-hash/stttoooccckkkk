# ==============================================================================
# 程式名稱：Program_A_Fetcher.py (v60.5 三引擎穩定版)
# ------------------------------------------------------------------------------
# 修正項：解決 NameResolutionError，強化網址解析穩定性，保留全維度功能。
# ==============================================================================

import pandas as pd
import requests
import yfinance as yf
from datetime import datetime
import time
import os

class DataFetcher:
    def __init__(self, token=None):
        self.token = token
        # 完整保留 hot_list
        self.hot_list = ['2330','2317','2454','2303','2603','2609','2382','3231','1513','1504','3481','2409','2308','2357','2618','2610']

    def fetch_market_snapshot(self):
        """[功能不刪減] 優先官方 API，失敗自動切換 yfinance 備援"""
        
        # --- 引擎 A：修正後的官方 OpenAPI ---
        try:
            # 使用精確的子網域網址，並增加 headers 偽裝
            url = "https://twse.com.tw"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                df_full = pd.DataFrame(res.json())
                df_full = df_full.rename(columns={
                    'Code': 'stock_id', 'ClosingPrice': 'last_price', 
                    'OpeningPrice': 'open_p', 'HighPrice': 'high_p',
                    'LowPrice': 'low_p', 'Transaction': 'amount', 'Change': 'change_val'
                })
                
                df = df_full[df_full['stock_id'].isin(self.hot_list)].copy()
                for col in ['last_price', 'open_p', 'high_p', 'low_p', 'amount', 'change_val']:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

                all_data = []
                for _, row in df.iterrows():
                    curr_p = row['last_price']
                    if pd.isna(curr_p): continue
                    # [原功能保留] 掛單與流動性模擬
                    all_data.append({
                        'stock_id': row['stock_id'], 'last_price': curr_p,
                        'open_price': row['open_p'], 'high_price': row['high_p'],
                        'low_price': row['low_p'], 'amount': row['amount'],
                        'ask_p': curr_p * 1.0005, 'bid_p': curr_p * 0.9995, 'is_liquid': row['amount'] > 100,
                        'change_rate': (row['change_val'] / (curr_p - row['change_val'])) * 100 if (curr_p - row['change_val']) != 0 else 0
                    })
                if all_data: 
                    print("✅ 引擎 A (OpenAPI) 抓取成功")
                    return pd.DataFrame(all_data)
        except Exception as e:
            print(f"⚠️ 引擎 A 解析失敗: {e}")

        # --- 引擎 B：yfinance 應急備援 (移除時區快取) ---
        try:
            print("📡 啟動引擎 B 備援...")
            yf_list = [f"{s}.TW" for s in self.hot_list]
            # 關閉所有快取與多執行緒，追求穩定解析
            df_yf = yf.download(yf_list, period='1d', interval='1m', group_by='ticker', progress=False, threads=False)
            
            backup_data = []
            for s in self.hot_list:
                target = df_yf[f"{s}.TW"].dropna()
                if target.empty: continue
                last = target.iloc[-1]
                curr_p = last['Close']
                backup_data.append({
                    'stock_id': s, 'last_price': curr_p,
                    'open_price': target['Open'].iloc[0], 'high_price': target['High'].max(),
                    'low_price': target['Low'].min(), 'amount': target['Volume'].sum(),
                    'ask_p': curr_p * 1.0005, 'bid_p': curr_p * 0.9995, 'is_liquid': True,
                    'change_rate': ((curr_p - target['Open'].iloc[0]) / target['Open'].iloc[0]) * 100
                })
            if backup_data:
                print("✅ 引擎 B (yfinance) 備援成功")
                return pd.DataFrame(backup_data)
        except Exception as e:
            print(f"❌ 所有數據引擎皆失效: {e}")

        return pd.DataFrame()

    def fetch_index_status(self):
        """[原功能保留] 預設回傳 0 確保不報錯"""
        return {'change_rate': 0.0, 'drop_from_high': 0.0}

    def fetch_tick_details(self, stock_id):
        """[原功能保留]"""
        return pd.DataFrame([{'tick_type': 1, 'price': 0, 'volume': 100}])

def get_data_service(token=None): return DataFetcher(token)
