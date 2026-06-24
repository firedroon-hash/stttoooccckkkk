import os
import pandas as pd
import yfinance as yf
from google.cloud import bigquery

# 強制讀取 GitHub 自動生成的金鑰
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"

client = bigquery.Client()
# 資料庫 1 路徑：專案ID.資料集ID.原始資料表
table_id = f"{client.project}.pi_data.stock_raw"

# 智慧判斷：檢查雲端有沒有資料
try:
    client.get_table(table_id)
    query_job = client.query(f"SELECT COUNT(*) FROM `{table_id}`")
    has_data = list(query_job.result())[0][0] > 0
except Exception:
    has_data = False

fetch_period = "1d" if has_data else "3y"
print(f"📡 【華立3010】模式啟動：抓取 {fetch_period} 數據...")

stock = yf.Ticker("3010.TW")
df = stock.history(period=fetch_period, interval="1d")

if not df.empty:
    df = df.reset_index()
    df_bq = pd.DataFrame()
    
    # 📝 剛性資料清洗：全面強制截斷小數點，確保數值純淨
    df_bq['trade_date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df_bq['open_price'] = df['Open'].round(2).astype(float)
    df_bq['high_price'] = df['High'].round(2).astype(float)
    df_bq['low_price'] = df['Low'].round(2).astype(float)
    df_bq['close_price'] = df['Close'].round(2).astype(float)
    df_bq['volume'] = df['Volume'].astype(int)  # 成交量強制為整數

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=True
    )
    job = client.load_table_from_dataframe(df_bq, table_id, job_config=job_config)
    job.result()
    print("🏁 【華立3010】原始數據已成功四捨五入並存入資料庫 1！")
else:
    print("⚠️ 今日非交易日，無新數據。")
