import os
import requests
import pandas as pd
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials.json"
discord_webhook_url = os.environ.get("DISCORD_URL")

client = bigquery.Client()
db1_table = f"{client.project}.pi_data.stock_raw"
db2_table = f"{client.project}.pi_data.stock_analysis"

print("🧠 正在從資料庫 1 提取數據進行高階均線運算...")

# 📝 SQL 精準度修正：在雲端計算時直接下 ROUND 函數，卡死小數點後 2 位
sql = f"""
    SELECT 
        trade_date, 
        ROUND(close_price, 2) AS close_price, 
        CAST(volume AS INT64) AS volume,
        ROUND(AVG(close_price) OVER(ORDER BY trade_date ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 2) AS ma5_price,
        ROUND((close_price - LAG(close_price) OVER(ORDER BY trade_date)) / LAG(close_price) OVER(ORDER BY trade_date) * 100, 2) AS daily_return
    FROM `{db1_table}`
    ORDER BY trade_date DESC
"""
query_job = client.query(sql)
df_analysis = query_job.to_dataframe()

if not df_analysis.empty:
    # 1. 提煉最新的一天資料（第 0 筆）
    df_latest = df_analysis.head(1).copy()
    
    # 再次確保 DataFrame 資料型態絕對乾淨
    df_latest['close_price'] = df_latest['close_price'].astype(float).round(2)
    df_latest['ma5_price'] = df_latest['ma5_price'].astype(float).round(2)
    df_latest['daily_return'] = df_latest['daily_return'].astype(float).round(2)
    df_latest['volume'] = df_latest['volume'].astype(int)

    # 寫入資料庫 2
    job_config = bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_APPEND, autodetect=True)
    job = client.load_table_from_dataframe(df_latest, db2_table, job_config=job_config)
    job.result()
    print("🏁 精準分析數據已附加存入資料庫 2！")

    # 2. 漂亮排版秒發 Discord
    today_data = df_latest.iloc[0]
    
    # 根據漲跌自動切換燈號
    daily_ret = today_data['daily_return']
    status_emoji = "🔴" if daily_ret > 0 else ("🟢" if daily_ret < 0 else "⚪")
    ret_prefix = "+" if daily_ret > 0 else ""

    message = {
        "content": f"🤖 **【AI 核心 ❌ 策略中心】每日收盤分析報告**\n"
                   f"📈 標的物：`華立 3010.TW`\n"
                   f"📅 交易日期：`{today_data['trade_date']}`\n"
                   f"💰 今日收盤：`{today_data['close_price']:.2f}` 元\n"
                   f"📊 5日均線 (MA5)：`{today_data['ma5_price']:.2f}` 元\n"
                   f"{status_emoji} 今日漲跌幅：`{ret_prefix}{daily_ret:.2f}%`\n"
                   f"📦 成交量：`{int(today_data['volume']):,}` 股\n\n"
                   f"⚡ *數據精準度校正完畢，已無縫同步備份至 GCP 雲端保險箱。*"
    }
    
    response = requests.post(discord_webhook_url, json=message)
    if response.status_code == 204:
        print("🚀 Discord 漂亮格式報告發送成功！")
    else:
        print(f"❌ Discord 發送失敗，狀態碼: {response.status_code}")
else:
    print("⚠️ 沒有可供分析的數據。")
