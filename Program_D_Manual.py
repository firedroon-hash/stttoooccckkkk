import os, requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# --- 完整中文名稱對照表 ---
STOCK_NAMES = {
    '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2303': '聯電',
    '2603': '長榮', '2609': '陽明', '3481': '群創', '2409': '友達',
    '2308': '台達電', '2382': '廣達', '3231': '緯創', '1513': '中興電'
}

def setup_chinese_font():
    """修正：使用絕對正確的 Raw 連結下載 TrueType 字體"""
    font_filename = "NotoSansTC.ttf"
    if not os.path.exists(font_filename):
        print("📡 正在從備援 CDN 下載真正有效的 TTF 字體...")
        # 改用 jsDelivr 提供的 Noto Sans TC 直接路徑，確保抓到的是 Binary
        url = "https://jsdelivr.net"
        try:
            r = requests.get(url, timeout=30)
            with open(font_filename, "wb") as f:
                f.write(r.content)
            file_size = os.path.getsize(font_filename)
            print(f"✅ 字體下載完成，檔案大小: {file_size} bytes")
            # 偵測檔案是否為 HTML (小於 500kb 基本上就是抓錯了)
            if file_size < 1000000:
                 print("⚠️ 警告：字體檔案過小，可能抓到錯誤網頁。")
        except:
            return "Helvetica"

    try:
        pdfmetrics.registerFont(TTFont('Chinese', font_filename))
        return 'Chinese'
    except Exception as e:
        print(f"❌ 註冊失敗: {e}")
        return "Helvetica"

def enhanced_process(data_list):
    font_name = setup_chinese_font()
    filename = "Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 1. 專業標題區
    c.setFillColor(colors.HexColor("#1A237E"))
    c.rect(0, height-100, width, 100, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 26)
    c.drawString(40, height-60, "AI 智慧量化交易監控報告")
    
    # 2. 數據表
    y = height - 150
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    
    # 表格標題
    headers = ["證券名稱", "現價", "建議進場", "停損防線", "預期空間"]
    cols = 
    c.setStrokeColor(colors.black)
    c.line(40, y+15, 550, y+15)
    for i, h in enumerate(headers):
        c.drawString(cols[i], y, h)
    c.line(40, y-5, 550, y-5)

    # 3. 填入內容
    y -= 25
    for item in data_list:
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        
        sid = str(item['stock_id'])
        name = STOCK_NAMES.get(sid, "熱門標的")
        
        c.drawString(cols[0], y, f"{sid} {name}")
        c.drawString(cols[1], y, f"{float(item['curr_p']):.2f}")
        
        c.setFillColor(colors.blue)
        c.drawString(cols[2], y, f"{float(item['entry_p']):.2f}")
        
        c.setFillColor(colors.red)
        c.drawString(cols[3], y, f"{float(item['exit_p']):.2f}")
        
        diff_pct = ((float(item['pred_high']) - float(item['curr_p'])) / float(item['curr_p'])) * 100
        c.setFillColor(colors.green if diff_pct > 0 else colors.black)
        c.drawString(cols[4], y, f"{diff_pct:.1f}%")
        
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    return filename
