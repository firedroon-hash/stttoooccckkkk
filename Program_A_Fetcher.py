import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

class DataFetcher:
    def __init__(self, token=None):
        self.token = token

    def fetch_market_snapshot(self):
        try:
            url = "https://twse.com.tw"
            df = pd.DataFrame(requests.get(url, timeout=10).json())
            df = df.rename(columns={'Code':'stock_id', 'ClosingPrice':'last_price', 'Transaction':'amount', 'Change':'change_val'})
            df['last_price'] = pd.to_numeric(df['last_price'], errors='coerce')
            df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
            df['change_val'] = pd.to_numeric(df['change_val'], errors='coerce')
            df['change_rate'] = (df['change_val'] / (df['last_price'] - df['change_val'])) * 100
            return df.dropna(subset=['last_price'])
        except:
            return pd.DataFrame()

    def fetch_index_status(self):
        try:
            idx = yf.Ticker("^TWII").fast_info
            return {'stock_id': 'TAIEX', 'last_price': idx['last_price'], 'change_rate': ((idx['last_price'] - idx['previous_close']) / idx['previous_close']) * 100}
        except: return None

    def fetch_tick_details(self, stock_id):
        try:
            df = yf.Ticker(f"{stock_id}.TW").history(period="1d", interval="1m").tail(10)
            return pd.DataFrame([{'tick_type': 1 if r['Close'] >= (r['Open']+r['High']+r['Low'])/3 else 0} for _, r in df.iterrows()])
        except: return pd.DataFrame()

def get_data_service(token=None): return DataFetcher(token)
