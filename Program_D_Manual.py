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
    """強制下載並註冊字體，解決亂碼問題"""
    font_filename = "NotoSansTC.otf"
    if not os.path.exists(font_filename):
        print("📡 正在下載中文字體 (約 12MB)...")
        # 使用 jsDelivr 直連連結
        url = "https://jsdelivr.net"
        try:
            r = requests.get(url, timeout=60, stream=True)
            if r.status_code == 200:
                with open(font_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"✅ 下載完成，檔案大小: {os.path.getsize(font_filename)} bytes")
            else:
                print(f"❌ 下載失敗: HTTP {r.status_code}")
        except Exception as e:
            print(f"❌ 下載過程異常: {e}")
            return "Helvetica"

    try:
        # 註冊為 'Chinese' 字體
        pdfmetrics.registerFont(TTFont('Chinese', font_filename))
        return 'Chinese'
    except Exception as e:
        print(f"❌ 註冊失敗: {e}")
        return "Helvetica"

def enhanced_process(data_list):
    """產出 PDF 分析報表"""
    font_name = setup_chinese_font()
    filename = "Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 1. 頁首
    c.setFillColor(colors.HexColor("#1A237E"))
    c.rect(0, height-100, width, 100, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 26)
    c.drawString(40, height-60, "AI 智慧量化交易監控報告")
    
    # 2. 表格
    y = height - 150
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    
    # 【關鍵修正：座標陣列】
    headers = ["證券名稱", "現價", "建議進場", "停損防線", "預期空間"]
    cols = [45, 160, 260, 360, 460]  # 定義確定的水平座標
    
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(40, y+15, 550, y+15)
    for i, h in enumerate(headers):
        c.drawString(cols[i], y, h)
    c.line(40, y-5, 550, y-5)

    # 3. 填入數據
    y -= 25
    for item in data_list:
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        
        sid = str(item['stock_id'])
        name = STOCK_NAMES.get(sid, "熱門標的")
        
        c.drawString(cols[0], y, f"{sid} {name}")
        c.drawString(cols[1], y, f"{float(item['curr_p']):,.2f}")
        
        c.setFillColor(colors.blue)
        c.drawString(cols[2], y, f"{float(item['entry_p']):,.2f}")
        
        c.setFillColor(colors.red)
        c.drawString(cols[3], y, f"{float(item['exit_p']):,.2f}")
        
        # 預期空間百分比
        try:
            diff_p = ((float(item['pred_high']) - float(item['curr_p'])) / float(item['curr_p'])) * 100
            c.setFillColor(colors.darkgreen if diff_p > 2 else colors.black)
            c.drawString(cols[4], y, f"{diff_p:.1f}%")
        except:
            c.drawString(cols[4], y, "0.0%")
        
        # 畫底線
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.line(40, y-5, 550, y-5)
        
        y -= 25
        if y < 60: # 自動分頁
            c.showPage()
            y = height - 50
            c.setFont(font_name, 10)

    c.save()
    return filename
