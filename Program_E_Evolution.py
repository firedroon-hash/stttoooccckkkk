# ==============================================================================
# 程式名稱：Program_E_Evolution.py (AI 實戰結算進化官 - v46.8 強化分析版)
# ==============================================================================

import os, pandas as pd, requests, time, numpy as np
import yfinance as yf
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 基礎設定 ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
# 擴展名稱表，增加更多分析標的
STOCK_NAMES = {
    '2330':'台積電', '2317':'鴻海', '2454':'聯發科', '2303':'聯電', 
    '2603':'長榮', '2609':'陽明', '2382':'廣達', '3231':'緯創',
    '1513':'中興電', '1504':'東元', '3481':'群創', '2409':'友達',
    '2618':'長榮航', '2610':'華航', '2357':'華碩', '1503':'士電'
}

def setup_font():
    """字體設置與自動下載"""
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
    except: return "Helvetica"

def calculate_performance_metrics(results):
    """[新增] 分析計算：勝率、最大回撤與資金效率"""
    if not results: return {}
    df_res = pd.DataFrame(results)
    win_rate = len(df_res[df_res['pl'] > 0]) / len(df_res)
    avg_error = df_res['error'].abs().mean()
    best_trade = df_res.loc[df_res['pl'].idxmax()]['sid']
    worst_trade = df_res.loc[df_res['pl'].idxmin()]['sid']
    return {
        "win_rate": win_rate,
        "avg_error": avg_error,
        "best": best_trade,
        "worst": worst_trade
    }

def generate_summary_pdf(results, total_pl, today_str):
    """產出結算報告 PDF (強化排版與分析細節)"""
    font_name = setup_font()
    metrics = calculate_performance_metrics(results)
    filename = f"Daily_Final_Report_{today_str}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # --- 頁首設計 ---
    c.setFillColor(colors.HexColor("#2C3E50")) # 深藍色調
    c.rect(0, height-120, width, 120, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 28)
    c.drawString(40, height-60, "AI 交易實戰進化結算報告")
    c.setFont(font_name, 12)
    c.drawString(40, height-90, f"日期: {today_str}  |  本金: 1,000,000 TWD  |  系統版本: v46.8")

    # --- 績效總覽卡片 ---
    y = height - 160
    c.setFillColor(colors.whitesmoke)
    c.roundRect(35, y-60, 525, 50, 10, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont(font_name, 14)
    status_color = colors.red if total_pl >= 0 else colors.green
    c.drawString(50, y-35, f"本日總損益: ")
    c.setFillColor(status_color)
    c.drawString(135, y-35, f"{total_pl:,.0f} 元")
    
    c.setFillColor(colors.black)
    c.setFont(font_name, 11)
    c.drawString(250, y-35, f"勝率: {metrics.get('win_rate',0):.1%} | 預判誤差: {metrics.get('avg_error',0):.2%}")
    c.drawString(420, y-35, f"最佳標的: {metrics.get('best','')}")

    # --- 表格區域 ---
    y -= 100
    c.setFillColor(colors.HexColor("#34495E"))
    c.rect(35, y-5, 525, 25, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont(font_name, 10)
    headers = ["股票代號/名稱", "進場價", "結算價", "股數", "淨損益", "預測誤差"]
    cols = [40, 150, 230, 310, 380, 480] 
    for i, h in enumerate(headers): c.drawString(cols[i], y+2, h)

    # 數據迭代
    y -= 25
    for r in results:
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        name = STOCK_NAMES.get(r['sid'], '未知')
        c.drawString(cols[0], y, f"{r['sid']} {name}")
        c.drawString(cols[1], y, f"{r['entry']:,.2f}")
        c.drawString(cols[2], y, f"{r['exit']:,.2f}")
        c.drawString(cols[3], y, f"{r['shares']}")
        
        # 損益顏色
        if r['pl'] >= 0: c.setFillColor(colors.red)
        else: c.setFillColor(colors.green)
        c.drawString(cols[4], y, f"{r['pl']:,.0f}")
        
        # 誤差顏色 (超過 2% 標註灰色)
        c.setFillColor(colors.black if abs(r['error']) < 0.02 else colors.grey)
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
    """執行盤後結算與進化邏輯"""
    if not os.path.exists("history_log.csv"):
        print("ℹ️ 今日無成交紀錄")
        return

    df = pd.read_csv("history_log.csv")
    today_str = datetime.now().strftime("%Y-%m-%d")
    df['stock_id'] = df['stock_id'].astype(str)
    
    # 篩選今日待結算 (OPEN) 的部位
    df_today = df[(df['date'] == today_str) & (df['status'] == 'OPEN')]
    
    if df_today.empty:
        print("ℹ️ 今日無待結算部位")
        return

    print(f"📊 開始結算 {len(df_today)} 筆交易...")
    results = []
    total_pl = 0

    for _, trade in df_today.iterrows():
        try:
            # 獲取最新市價與統計數據
            ticker = yf.Ticker(f"{trade['stock_id']}.TW")
            # 增加錯誤重試機制，避免 yfinance 暫時性失效
            for _ in range(3):
                try:
                    history = ticker.history(period="1d")
                    final_p = history['Close'].iloc[-1]
                    day_high = history['High'].iloc[-1]
                    break
                except: time.sleep(2)
            
            # 滑價模擬：以收盤價再扣除 0.05% 作為平倉摩擦
            final_bid = final_p * 0.9995 
            
            # 成本計算 (手續費 0.1425% 考慮折扣)
            cost = trade['entry_p'] * trade['shares'] * 1000 * 1.001425
            # 營收計算 (扣除證交稅 0.3% 與手續費)
            revenue = final_bid * trade['shares'] * 1000 * 0.996575
            pl = revenue - cost
            total_pl += pl

            # 預測誤差分析：當初 F 策略預估的高點 vs 今日真實高點
            pred = trade['pred_high'] if trade['pred_high'] != 0 else trade['entry_p']
            error_pct = (day_high - pred) / pred

            results.append({
                'sid': str(trade['stock_id']), 'entry': trade['entry_p'],
                'exit': final_bid, 'shares': trade['shares'], 'pl': pl, 'error': error_pct
            })
        except Exception as e: 
            print(f"❌ 標的 {trade['stock_id']} 結算異常: {e}")
            continue

    # 產出強化版 PDF
    pdf_path = generate_summary_pdf(results, total_pl, today_str)
    
    # [更新] 將成交歷史標記為已結算 (CLOSED)
    df.loc[(df['date'] == today_str) & (df['status'] == 'OPEN'), 'status'] = 'CLOSED'
    df.to_csv("history_log.csv", index=False)

    # --- Discord 強化發送邏輯 ---
    if WEBHOOK_URL:
        # 根據盈虧程度選擇 Emoji
        emoji = "🚀" if total_pl > 10000 else "💰" if total_pl >= 0 else "📉"
        msg = (
            f"🏁 **AI 交易系統 - 每日終場結算**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 結算日期：`{today_str}`\n"
            f"{emoji} 當日總損益：**{total_pl:,.0f}** TWD\n"
            f"📈 勝率：`{calculate_performance_metrics(results)['win_rate']:.1%}`\n"
            f"🔍 預判誤差：`{calculate_performance_metrics(results)['avg_error']:.2%}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📢 *詳細各股明細請參閱附件 PDF 報告*"
        )
        
        try:
            with open(pdf_path, 'rb') as f:
                requests.post(WEBHOOK_URL, data={'content': msg}, files={'file': f}, timeout=30)
            print("📡 結算報告已成功傳送至 Discord")
        except Exception as e:
            print(f"❌ Discord 傳送失敗: {e}")
            
        if os.path.exists(pdf_path): os.remove(pdf_path)

if __name__ == "__main__":
    # 強制使用台北時區
    os.environ['TZ'] = 'Asia/Taipei'
    if hasattr(time, 'tzset'): time.tzset()
    run_evolution()
