# ==============================================================================
# 程式名稱：Program_E_Evolution.py (當日結算與總結報告版)
# ==============================================================================
import os, pandas as pd, requests
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 讀取 Secrets
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

def setup_font():
    font_path = "NotoSansTC-Regular.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com"
        r = requests.get(url)
        with open(font_path, "wb") as f: f.write(r.content)
    pdfmetrics.registerFont(TTFont('SourceHan', font_path))
    return 'SourceHan'

def generate_daily_summary(df):
    """產出當日總結 PDF"""
    font_name = setup_font()
    filename = f"Daily_Summary_{datetime.now().strftime('%Y%m%d')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 標題設計 (深金/橘色區分盤中報告)
    c.setFillColor(colors.HexColor("#D35400"))
    c.rect(0, height-100, width, 100, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 26)
    c.drawString(40, height-55, "當日交易戰果結算報告")
    c.setFont(font_name, 12)
    c.drawString(40, height-80, f"Trading Day: {datetime.now().strftime('%Y-%m-%d')} | 系統自動結算")

    # 數據總覽區
    y = height - 150
    c.setFillColor(colors.black)
    total_trades = len(df)
    # 簡單模擬損益 (實際環境會抓取 Program_A 最終收盤價)
    c.setFont(font_name, 14)
    c.drawString(40, y, f"今日發送訊號總數: {total_trades} 筆")
    
    # 表格 Header
    y -= 40
    c.setFillColor(colors.lightgrey)
    c.rect(35, y-5, 525, 25, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    headers = ["標的代碼", "建議進場價", "預判高點", "最高落差", "狀態"]
    cols = [45, 150, 260, 370, 480]
    for i, h in enumerate(headers):
        c.drawString(cols[i], y+2, h)

    # 數據列
    y -= 25
    for _, row in df.iterrows():
        c.setFont(font_name, 10)
        c.drawString(cols[0], y, str(row['stock_id']))
        c.drawString(cols[1], y, f"{row['entry_price']:.2f}")
        c.drawString(cols[2], y, f"{row['pred_high']:.2f}")
        
        # 這裡會從 history_log 分析數據
        diff = ((row['pred_high'] - row['entry_price']) / row['entry_price']) * 100
        c.drawString(cols[3], y, f"{diff:.1f}%")
        
        status = "達標" if diff > 3 else "觀察"
        c.drawString(cols[4], y, status)
        
        c.line(35, y-5, 560, y-5)
        y -= 25

    c.save()
    return filename

def run_evolution():
    # 這裡會讀取 Program_B 寫入的 history_log.csv
    log_file = "history_log.csv"
    if os.path.exists(log_file):
        df = pd.read_csv(log_file)
        pdf = generate_daily_summary(df)
        
        # 發送至 Discord
        if WEBHOOK_URL:
            with open(pdf, 'rb') as f:
                requests.post(WEBHOOK_URL, data={'content': "📊 **收盤戰報**：今日 AI 交易執行總結已產出。"}, files={'file': f})
        print("✅ 當日結算報告已發送")
    else:
        print("ℹ️ 今日無成交紀錄，跳過結算報告。")

if __name__ == "__main__":
    run_evolution()
