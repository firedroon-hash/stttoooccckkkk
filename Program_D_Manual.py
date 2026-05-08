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
    """強制從 CDN 下載真正有效的二進位字體檔"""
    font_filename = "NotoSansTC.otf"
    if not os.path.exists(font_filename):
        print("📡 正在從 jsDelivr 下載中文字體 (約 12MB)...")
        # 使用真正指向檔案的 jsDelivr 連結，避開 GitHub 網頁
        url = "https://jsdelivr.net"
        try:
            r = requests.get(url, timeout=60, stream=True)
            if r.status_code == 200:
                with open(font_filename, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                file_size = os.path.getsize(font_filename)
                print(f"✅ 下載完成，檔案大小: {file_size} bytes")
                if file_size < 1000000:
                    print("⚠️ 警告：檔案大小異常，可能下載失敗")
            else:
                print(f"❌ CDN 請求失敗: {r.status_code}")
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
    font_name = setup_chinese_font()
    filename = "Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 1. 專業標題區 (深藍色)
    c.setFillColor(colors.HexColor("#1A237E"))
    c.rect(0, height-100, width, 100, fill=1)
    c.setFillColor(colors.white)
    c.setFont(font_name, 26)
    c.drawString(40, height-60, "AI 智慧量化交易監控報告")
    
    # 2. 數據表 Header
    y = height - 150
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    
    # [修正] 座標列表與標題，確保欄位不重疊
    headers = ["證券名稱", "現價", "建議進場", "停損防線", "預期空間"]
    cols = # 定義正確的水平座標
    
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.line(40, y+15, 550, y+15)
    for i, h in enumerate(headers):
        c.drawString(cols[i], y, h)
    c.line(40, y-5, 550, y-5)

    # 3. 數據循環
    y -= 25
    for item in data_list:
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        
        sid = str(item['stock_id'])
        name = STOCK_NAMES.get(sid, "熱門標的")
        
        # 繪製各欄位
        c.drawString(cols, y, f"{sid} {name}")
        c.drawString(cols, y, f"{float(item['curr_p']):,.2f}")
        
        c.setFillColor(colors.blue)
        c.drawString(cols, y, f"{float(item['entry_p']):,.2f}")
        
        c.setFillColor(colors.red)
        c.drawString(cols, y, f"{float(item['exit_p']):,.2f}")
        
        # 計算落差並標色
        try:
            diff_p = ((float(item['pred_high']) - float(item['curr_p'])) / float(item['curr_p'])) * 100
            if diff_p > 2.0:
                c.setFillColor(colors.darkgreen)
                text = f"★ {diff_p:.1f}%"
            else:
                c.setFillColor(colors.black)
                text = f"{diff_p:.1f}%"
            c.drawString(cols, y, text)
        except:
            c.drawString(cols, y, "0.0%")
        
        # 畫底線
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.line(40, y-5, 550, y-5)
        
        y -= 25
        if y < 50: # 分頁處理
            c.showPage()
            y = height - 50
            c.setFont(font_name, 10)

    c.save()
    return filename
