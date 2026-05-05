# ==============================================================================
# 程式名稱：Program_D_Manual.py (專業 PDF 分析報告 - 中文強化版)
# ==============================================================================
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

# 中文名稱映射表 (對應 A 程式 hot_list)
STOCK_NAMES = {
    '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2303': '聯電',
    '2603': '長榮', '2609': '陽明', '2615': '萬海', '2382': '廣達',
    '3231': '緯創', '2376': '技嘉', '1513': '中興電', '1504': '東元',
    '3481': '群創', '2409': '友達', '2308': '台達電', '2357': '華碩'
}

def enhanced_process(data):
    sid = data['stock_id']
    name = STOCK_NAMES.get(sid, "熱門強勢股")
    filename = f"Analysis_{sid}.pdf"
    
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, f"AI Analysis Report: {sid} {name}")
    
    c.setFont("Helvetica", 12)
    y = 770
    c.drawString(50, y, f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 價格區塊
    y -= 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "[ Price Info / 價格數據 ]")
    c.setFont("Helvetica", 12)
    c.drawString(70, y-25, f"- Opening Price (今日開盤): {data['open_p']}")
    c.drawString(70, y-45, f"- Current Price (現價): {data['curr_p']}")
    c.drawString(70, y-65, f"- Today High/Low (今日高/低): {data['high_p']} / {data['low_p']}")
    
    # 決策區塊
    y -= 100
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "[ AI Decision / 策略建議 ]")
    c.setFont("Helvetica", 12)
    c.drawString(70, y-25, f"- Entry Target (建議進場): {data['entry_p']}")
    c.drawString(70, y-45, f"- Stop Loss (建議退場/停損): {data['exit_p']}")
    c.drawString(70, y-65, f"- Predicted High (預判本日最高): {data['pred_high']}")
    
    # 落差分析
    y -= 100
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "[ Gap Analysis / 落差分析 ]")
    c.setFont("Helvetica", 12)
    
    diff_val = data['pred_high'] - data['curr_p']
    diff_pct = (diff_val / data['curr_p']) * 100 if data['curr_p'] > 0 else 0
    
    c.drawString(70, y-25, f"- Gap to Pred-High (預判落差%): {diff_pct:.2f}%")
    
    analysis_text = "Analysis: "
    if diff_pct > 2: analysis_text += "Substantial upside potential detected."
    elif diff_pct > 0: analysis_text += "Approaching predicted peak. Monitor closely."
    else: analysis_text += "Price exceeded predicted high. Profit-taking suggested."
    c.drawString(70, y-45, analysis_text)
    
    # 實戰成本
    y -= 80
    cost = data['curr_p'] * 0.00435
    tick = 0.05 if data['curr_p'] < 50 else 0.1 if data['curr_p'] < 100 else 0.5
    needed_ticks = int(cost / tick) + 1
    c.drawString(50, y, f"[ Financial Detail ] Needed Ticks to Break-even: {needed_ticks}")
    
    c.showPage()
    c.save()
    return filename
