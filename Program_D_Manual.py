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
    """強制使用穩定 CDN 下載，避開 GitHub 網頁跳轉陷阱"""
    font_filename = "NotoSansTC.otf"
    if not os.path.exists(font_filename):
        print("📡 啟動終極修復：正在從 jsDelivr CDN 下載 10MB+ 中文字體...")
        # 改用 jsDelivr 加速連結，這是真正的原始檔案路徑
        url = "https://jsdelivr.net"
        try:
            r = requests.get(url, timeout=60, stream=True)
            if r.status_code == 200:
                with open(font_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: f.write(chunk)
                file_size = os.path.getsize(font_filename)
                print(f"✅ 下載完畢，真實大小: {file_size} bytes")
                if file_size < 1000000:
                    print("❌ 下載異常：檔案大小過小，可能仍抓到無效數據")
            else:
                print(f"❌ CDN 請求失敗狀態碼: {r.status_code}")
        except Exception as e:
            print(f"❌ 下載過程異常: {e}")
            return "Helvetica"

    try:
        # 註冊字體
        pdfmetrics.registerFont(TTFont('Chinese', font_filename))
        print("✅ 字體 'Chinese' 註冊成功")
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
    
    # 2. 數據表 Header
    y = height - 150
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    
    headers = ["證券名稱", "現價", "建議進場", "停損防線", "預期空間"]
    cols = 
    
    c.setStrokeColor(colors.black)
    c.line(40, y+15, 550, y+15)
    for i, h in enumerate(headers):
        c.drawString(cols[i], y, h)
    c.line(40, y-5, 550, y-5)

    # 3. 數據填入
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
        
        diff_p = ((float(item['pred_high']) - float(item['curr_p'])) / float(item['curr_p'])) * 100
        c.setFillColor(colors.darkgreen if diff_p > 2 else colors.black)
        c.drawString(cols[4], y, f"{diff_p:.1f}%")
        
        y -= 25
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    return filename
