import os, pandas as pd, requests, time
import yfinance as yf
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 基礎設定 ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
STOCK_NAMES = {
    '2330':'台積電', '2317':'鴻海', '2454':'聯發科', '2303':'聯電', 
    '2603':'長榮', '2609':'陽明', '2382':'廣達', '3231':'緯創',
    '1513':'中興電', '1504':'東元', '3481':'群創', '2409':'友達'
}

def setup_font():
    font_filename = "NotoSansTC-Regular.ttf"
    if not os.path.exists(font_filename):
        print("📡 下載中文字體中...")
        url = "https://github.com"
        try:
            r = requests.get(url, timeout=30)
            with open(font_filename, "wb") as f: f.write(r.content)
        except: return "Helvetica"
    
    try:
        pdfmetrics.registerFont(TTFont('SourceHan', font_filename))
        return 'SourceHan'
    except:
        return "Helvetica"

def generate_summary_pdf(results, total_pl, today_str):
    """產出當日結算總結 PDF (修正座標語法)"""
    font_name = setup_font()
    filename = f"Daily_Final_Report_{today_str}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 標題區
    c.setFillColor(colors.HexColor("#E67E22"))
    c.rect(0, height-100, width, 100, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 26)
    c.drawString(40, height-55, "當日實戰模擬結算報告")
    c.setFont(font_name, 12)
    c.drawString(40, height-80, f"Trading Date: {today_str} | 100萬本金驗證模組")

    # 損益總覽
    y = height - 150
    c.setFillColor(colors.black)
    c.setFont(font_name, 16)
    status_text = "獲利" if total_pl >= 0 else "虧損"
    c.drawString(40, y, f"本日總損益: {total_pl:,.0f} 元 ({status_text})")

    # 表格 Header
    y -= 40
    c.setFillColor(colors.whitesmoke)
    c.rect(35, y-5, 525, 25, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    headers = ["股票", "成交價", "平倉價(Bid)", "股數", "盈虧", "預判誤差"]
    # 修正處：定義正確的座標
    cols = [40, 130, 220, 310, 380, 470] 
    
    for i, h in enumerate(headers): 
        c.drawString(cols[i], y+2, h)

    # 數據列
    y -= 25
    for r in results:
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        c.drawString(cols[0], y, f"{r['sid']} {STOCK_NAMES.get(r['sid'],'')}")
        c.drawString(cols[1], y, f"{r['entry']:.2f}")
        c.drawString(cols[2], y, f"{r['exit']:.2f}")
        c.drawString(cols[3], y, f"{r['shares']}")
        
        # 盈虧顏色判定
        if r['pl'] >= 0: c.setFillColor(colors.red)
        else: c.setFillColor(colors.green)
        c.drawString(cols[4], y, f"{r['pl']:,.0f}")
        
        c.setFillColor(colors.black)
        c.drawString(cols[5], y, f"{r['error']:.1%}")
        
        c.setStrokeColor(colors.lightgrey)
        c.line(35, y-5, 560, y-5)
        y -= 25
        if y < 50: 
            c.showPage()
            y = height - 50

    c.save()
    return filename

def run_evolution():
    if not os.path.exists("history_log.csv"):
        print("ℹ️ 今日無成交紀錄")
        return

    df = pd.read_csv("history_log.csv")
    today_str = datetime.now().strftime("%Y-%m-%d")
    # 修正：確保 stock_id 讀取為字串
    df['stock_id'] = df['stock_id'].astype(str)
    df_today = df[(df['date'] == today_str) & (df['status'] == 'OPEN')]
    
    if df_today.empty:
        print("ℹ️ 今日無待結算部位")
        return

    results = []
    total_pl = 0

    for _, trade in df_today.iterrows():
        try:
            ticker = yf.Ticker(f"{trade['stock_id']}.TW")
            final_p = ticker.fast_info['last_price']
            final_bid = final_p * 0.9995 
            
            cost = trade['entry_p'] * trade['shares'] * 1000 * 1.001425
            revenue = final_bid * trade['shares'] * 1000 * 0.997075
            pl = revenue - cost
            total_pl += pl

            day_high = ticker.fast_info.get('day_high', final_p)
            # 避免除以零
            pred = trade['pred_high'] if trade['pred_high'] != 0 else trade['entry_p']
            error_pct = (day_high - pred) / pred

            results.append({
                'sid': str(trade['stock_id']), 'entry': trade['entry_p'],
                'exit': final_bid, 'shares': trade['shares'], 'pl': pl, 'error': error_pct
            })
        except Exception as e: 
            print(f"結算單檔異常 {trade['stock_id']}: {e}")
            continue

    pdf_path = generate_summary_pdf(results, total_pl, today_str)
    
    # 更新狀態
    df.loc[(df['date'] == today_str) & (df['status'] == 'OPEN'), 'status'] = 'CLOSED'
    df.to_csv("history_log.csv", index=False)

    if WEBHOOK_URL:
        msg = f"🏁 **今日交易最終結算**\n💰 總損益：**{total_pl:,.0f}** 元"
        with open(pdf_path, 'rb') as f:
            requests.post(WEBHOOK_URL, data={'content': msg}, files={'file': f})
        os.remove(pdf_path)

if __name__ == "__main__":
    run_evolution()
