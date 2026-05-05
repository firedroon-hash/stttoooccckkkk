import os
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# --- 完整中文名稱對照表 (依據 A 程式 hot_list) ---
STOCK_NAMES = {
    '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2303': '聯電',
    '2603': '長榮', '2609': '陽明', '2615': '萬海', '2382': '廣達',
    '3231': '緯創', '2376': '技嘉', '1513': '中興電', '1504': '東元',
    '3481': '群創', '2409': '友達', '2308': '台達電', '2357': '華碩',
    '1519': '華城', '1514': '亞力', '1605': '華新', '2618': '長榮航'
}

def setup_chinese_font():
    """下載並註冊思源黑體，解決 Linux 環境中文問題"""
    font_filename = "NotoSansTC-Regular.ttf"
    if not os.path.exists(font_filename):
        print("📡 正在加載專業中文字體...")
        url = "https://github.com"
        try:
            r = requests.get(url, timeout=30)
            with open(font_filename, "wb") as f: f.write(r.content)
        except: return "Helvetica"
    pdfmetrics.registerFont(TTFont('SourceHan', font_filename))
    return 'SourceHan'

def enhanced_process(data_list):
    font_name = setup_chinese_font()
    filename = "Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 1. 頁首設計 (深藍色專業感)
    c.setFillColor(colors.HexColor("#1A315E"))
    c.rect(0, height-100, width, 100, fill=1)
    
    c.setFillColor(colors.white)
    c.setFont(font_name, 26)
    c.drawString(40, height-50, "AI 智慧量化交易監控報告")
    
    c.setFont(font_name, 12)
    c.drawString(40, height-75, f"Market Analysis Report | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 2. 市場情緒儀表 (簡易視覺化)
    y = height - 130
    c.setFillColor(colors.black)
    c.setFont(font_name, 11)
    c.drawString(40, y, "【 本輪掃描重點標的摘要 】")
    
    # 3. 表格 Header (灰色背景)
    y -= 30
    c.setFillColor(colors.HexColor("#F2F2F2"))
    c.rect(35, y-5, 525, 25, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor("#444444"))
    c.setFont(font_name, 10)
    headers = ["證券名稱", "當前價格", "開盤價", "建議進場", "停損防線", "目標高點", "預判空間"]
    cols = [45, 120, 190, 260, 330, 410, 485]
    for i, h in enumerate(headers):
        c.drawString(cols[i], y+2, h)

    # 4. 數據列填充
    y -= 25
    for i, item in enumerate(data_list):
        # 隔行變色增加閱讀性
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#FFFFFF"))
        else:
            c.setFillColor(colors.HexColor("#FAFAFA"))
        c.rect(35, y-5, 525, 25, fill=1, stroke=0)
        
        # 提取與計算
        sid = item['stock_id']
        name = STOCK_NAMES.get(sid, "熱門股")
        curr_p = item['curr_p']
        pred_h = item['pred_high']
        diff_pct = ((pred_h - curr_p) / curr_p) * 100 if curr_p > 0 else 0
        
        # 繪製文字
        c.setFillColor(colors.black)
        c.setFont(font_name, 10)
        c.drawString(cols[0], y+2, f"{sid} {name}")
        c.drawString(cols[1], y+2, f"{curr_p:,.2f}")
        c.drawString(cols[2], y+2, f"{item['open_p']:,.2f}")
        
        # 建議進場用藍色加粗
        c.setFillColor(colors.blue)
        c.setFont(f"{font_name}", 10)
        c.drawString(cols[3], y+2, f"{item['entry_p']:,.2f}")
        
        # 停損價用紅色
        c.setFillColor(colors.red)
        c.drawString(cols[4], y+2, f"{item['exit_p']:,.2f}")
        
        # 預判空間
        c.setFillColor(colors.black)
        c.drawString(cols[5], y+2, f"{pred_h:,.2f}")
        
        # 空間百分比顏色判定 (大於 2.5% 亮綠色)
        if diff_pct > 2.5:
            c.setFillColor(colors.green)
            label = "★ " + f"{diff_pct:.1f}%"
        else:
            c.setFillColor(colors.black)
            label = f"{diff_pct:.1f}%"
        c.drawString(cols[6], y+2, label)
        
        # 畫底線
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.line(35, y-5, 560, y-5)
        
        y -= 25
        if y < 80: # 自動分頁
            c.showPage()
            y = height - 50

    # 5. 頁尾免責聲明
    c.setFont(font_name, 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, 30, "本報告由 AI 自動生成，僅供數據參考，不代表投資建議。交易風險請自行評估。")

    c.save()
    return filename
