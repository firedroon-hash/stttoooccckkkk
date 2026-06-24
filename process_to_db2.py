import os
import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
discord_webhook_url = os.environ.get("DISCORD_URL")

client = bigquery.Client()
db1_table = f"{client.project}.pi_data.stock_raw"
db2_table = f"{client.project}.pi_data.stock_analysis"

print("🧠 正在從資料庫 1 提取數據進行運算分析...")

# 撰寫 BigQuery 雲端 SQL：直接在雲端計算 5日均線(MA5) 與 今日漲跌幅
sql = f"""
    SELECT 
        trade_date, close_price, volume,
        ROUND(AVG(close_price) OVER(ORDER BY trade_date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS ma5_price,
        ROUND((close_price - LAG(close_price) OVER(ORDER BY trade_date)) / LAG(close_price) OVER(ORDER BY trade_date) * 100, 2) AS daily_return
    FROM `{db1_table}`
    ORDER BY trade_date DESC
"""
query_job = client.query(sql)
df_analysis = query_job.to_dataframe()

if not df_analysis.empty:
    # 1. 將最新的分析成果（第 0 筆）附加存入資料庫 2
    df_latest = df_analysis.head(1).copy()
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND, autodetect=True)
    job = client.load_table_from_dataframe(df_latest, db2_table, job_config=job_config)
    job.result()
    print("🏁 分析結果成功存入資料庫 2！")

    # 2. 提煉數據，精美包裝發送到 Discord
    today_row = df_latest.iloc[0]
    status_emoji = "📈" if today_row['daily_return'] >= 0 else "📉"
    
    message = {
        "content": f"🤖 **【AI 核心 ❌ 策略中心】每日收盤分析報告**\n"
                   f"📅 交易日期：`{today_row['trade_date']}`\n"
                   f"💰 今日收盤：`{today_row['close_price']}` 元\n"
                   f"📊 5日均線 (MA5)：`{today_row['ma5_price']}` 元\n"
                   f"{status_emoji} 今日漲跌幅：`{today_row['daily_return']}%`\n"
                   f"📦 交易量：`{today_row['volume']:,}` 股\n"
                   f"⚡ *核心流水線運算完畢，數據已同步備份至 GCP 雲端保險箱。*"
    }
    
    # 透過網路請求秒發到 Discord
    response = requests.post(discord_webhook_url, json=message)
    if response.status_code == 204:
        print("🚀 Discord 報告發送成功！")
    else:
        print(f"❌ Discord 發送失敗，狀態碼: {response.status_code}")
