import os, requests, time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# --- 完整中文名稱對照表 ---
STOCK_NAMES = {
    '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2303': '聯電',
    '2603': '長榮', '2609': '陽明', '2615': '萬海', '2382': '廣達',
    '3231': '緯創', '2376': '技嘉', '1513': '中興電', '1504': '東元',
    '3481': '群創', '2409': '友達', '2308': '台達電', '2357': '華碩',
    '1519': '華城', '1514': '亞力', '1605': '華新', '2618': '長榮航',
    '2610': '華航', '1503': '士電', '2353': '宏碁', '2449': '京元電'
}

def setup_chinese_font():
    """修正版：使用可靠 CDN 下載字體，確保中文不亂碼"""
    font_filename = "NotoSansTC-Regular.ttf"
    if not os.path.exists(font_filename):
        print("📡 正在加載專業中文字體...")
        # 修正為正確的下載路徑
        url = "https://jsdelivr.net"
        try:
            r = requests.get(url, timeout=30)
            with open(font_filename, "wb") as f: f.write(r.content)
            print("✅ 字體下載成功")
        except: return "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont('SourceHan', font_filename))
        return 'SourceHan'
    except: return "Helvetica"

def enhanced_process(data_list):
    font_name = setup_chinese_font()
    filename = "Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 1. 專業頁首
    c.setFillColor(colors.HexColor("#0D1B2A"))
    c.rect(0, height-110, width, 110, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 26)
    c.drawString(40, height-55, "AI 智慧量化交易監控報告")
    c.setFont(font_name, 10)
    c.drawString(40, height-85, f"報告編號: {datetime.now().strftime('%Y%m%d%H%M')} | 實戰模擬 (v47.0)")
    c.drawRightString(width-40, height-85, f"生成時間: {datetime.now().strftime('%H:%M:%S')}")

    # 2. 數據摘要
    y = height - 140
    c.setFillColor(colors.black)
    c.setFont(font_name, 12)
    c.drawString(40, y, f"【 本次掃描訊號彙整: {len(data_list)} 檔 】")
    c.setStrokeColor(colors.lightgrey)
    c.line(35, y-10, 560, y-10)

    # 3. 表格標題
    y -= 45
    c.setFillColor(colors.HexColor("#F2F2F2"))
    c.rect(35, y-5, 525, 28, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    headers = ["證券名稱", "現價/開盤", "建議進場", "停損防線", "目標高點", "預期空間", "風報比"]
    cols = [40, 120, 200, 280, 360, 440, 510]
    for i, h in enumerate(headers):
        c.drawString(cols[i], y+5, h)

    # 4. 數據填充
    y -= 30
    for i, item in enumerate(data_list):
        if i % 2 == 1: # 隔行變色
            c.setFillColor(colors.HexColor("#F9F9F9"))
            c.rect(35, y-5, 525, 25, fill=1, stroke=0)
        
        sid = item['stock_id']
        name = STOCK_NAMES.get(sid, "熱門標的")
        
        # 提取數據
        curr_p = float(item['curr_p'])
        entry_p = float(item['entry_p'])
        exit_p = float(item['exit_p'])
        pred_h = float(item['pred_high'])
        diff_pct = ((pred_h - curr_p) / curr_p) * 100
        
        # 風報比計算
        reward = pred_h - entry_p
        risk = entry_p - exit_p if entry_p > exit_p else 0.1
        rr_ratio = reward / risk

        c.setFillColor(colors.black)
        c.setFont(font_name, 9)
        c.drawString(cols[0], y+2, f"{sid} {name}")
        c.drawString(cols[1], y+2, f"{curr_p:,.1f} / {item['open_p']:,.1f}")
        
        c.setFillColor(colors.blue)
        c.drawString(cols[2], y+2, f"{entry_p:,.2f}")
        
        c.setFillColor(colors.red)
        c.drawString(cols[3], y+2, f"{exit_p:,.2f}")
        
        c.setFillColor(colors.black)
        c.drawString(cols[4], y+2, f"{pred_h:,.2f}")
        
        # 空間分析標註
        if diff_pct > 3.0:
            c.setFillColor(colors.red)
            c.drawString(cols[5], y+2, f"↑ {diff_pct:.1f}%")
        else:
            c.drawString(cols[5], y+2, f"{diff_pct:.1f}%")

        # 風報比標註
        if rr_ratio >= 2.0:
            c.setFillColor(colors.darkgreen)
            c.drawString(cols[6], y+2, f"{rr_ratio:.1f} ★")
        else:
            c.setFillColor(colors.grey)
            c.drawString(cols[6], y+2, f"{rr_ratio:.1f}")

        y -= 25
        if y < 70: # 分頁
            c.showPage()
            y = height - 50

    # 5. 浮水印與頁尾
    c.rotate(30)
    c.setFillColorRGB(0.9, 0.9, 0.9, 0.2)
    c.setFont(font_name, 40)
    c.drawCentredString(width/2, 0, "AI QUANT ANALYSIS")
    c.rotate(-30)

    c.save()
    return filename
