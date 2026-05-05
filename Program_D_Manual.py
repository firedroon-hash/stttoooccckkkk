import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# --- 中文名稱映射表 ---
STOCK_NAMES = {
    '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2303': '聯電',
    '2603': '長榮', '2609': '陽明', '2615': '萬海', '2382': '廣達',
    '3231': '緯創', '2376': '技嘉', '1513': '中興電', '1504': '東元',
    '3481': '群創', '2409': '友達', '2308': '台達電', '2357': '華碩'
}

def download_font():
    """下載開源字體以支援中文 (如果環境中沒有)"""
    font_path = "msjh.ttc"
    if not os.path.exists(font_path):
        import requests
        # 從公共資源下載微軟正黑體替代品或思源黑體 (此處以下載連結為例)
        url = "https://github.com"
        r = requests.get(url)
        with open("font.otf", "wb") as f: f.write(r.content)
        pdfmetrics.registerFont(TTFont('ChineseFont', 'font.otf'))
    else:
        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))

def enhanced_process(data_list):
    """
    接收 data_list: 包含多檔股票字典的列表
    """
    try:
        download_font()
        font_name = 'ChineseFont'
    except:
        font_name = 'Helvetica' # 萬一字體下載失敗，回退到英文

    filename = f"Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # --- 標題區 ---
    c.setFillColor(colors.dodgerblue)
    c.rect(0, height-80, width, 80, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 24)
    c.drawCentredString(width/2, height-50, f"AI 實戰交易掃描報告")
    
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    c.drawString(450, height-100, f"報告時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # --- 表格標題 ---
    y = height - 130
    c.setFillColor(colors.whitesmoke)
    c.rect(30, y-20, 535, 20, fill=1)
    c.setFillColor(colors.black)
    c.setFont(font_name, 9)
    headers = ["代碼/名稱", "現價", "建議進場", "退場(停損)", "預判高點", "落差%"]
    cols = [40, 130, 200, 280, 360, 440]
    for i, h in enumerate(headers):
        c.drawString(cols[i], y-14, h)

    # --- 畫表格線與填入數據 ---
    y -= 20
    for item in data_list:
        c.setStrokeColor(colors.lightgrey)
        c.line(30, y, 565, y) # 橫線
        
        sid = item['stock_id']
        name = STOCK_NAMES.get(sid, "熱門股")
        curr_p = item['curr_p']
        pred_h = item['pred_high']
        diff_pct = ((pred_h - curr_p) / curr_p) * 100 if curr_p > 0 else 0
        
        c.setFont(font_name, 9)
        c.drawString(40, y-15, f"{sid} {name}")
        c.drawString(130, y-15, f"{curr_p}")
        c.drawString(200, y-15, f"{item['entry_p']}")
        c.setFillColor(colors.red) # 停損用紅色
        c.drawString(280, y-15, f"{item['exit_p']}")
        c.setFillColor(colors.black)
        c.drawString(360, y-15, f"{pred_h}")
        
        # 落差分析顏色判定
        if diff_pct > 2: c.setFillColor(colors.green)
        else: c.setFillColor(colors.black)
        c.drawString(440, y-15, f"{diff_pct:.2f}%")
        c.setFillColor(colors.black)
        
        y -= 25
        if y < 50: # 分頁處理
            c.showPage()
            y = height - 50

    c.save()
    return filename
