import os, requests, time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# --- 中文名稱映射 ---
STOCK_NAMES = {
    '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2303': '聯電',
    '2603': '長榮', '2609': '陽明', '3481': '群創', '2409': '友達',
    '2308': '台達電', '2382': '廣達', '3231': '緯創', '1513': '中興電'
}

def setup_chinese_font():
    """終極字體解決方案：使用 TTF 格式並強制嵌入"""
    # 使用 Google Noto Sans TC 的輕量化 TTF 版本
    font_filename = "font.ttf"
    if not os.path.exists(font_filename):
        print("📡 正在嘗試多重路徑下載中文字體...")
        # 這是專門提供給 CSS 用的 TTF 直接鏈結，對 Linux 兼容性最高
        url = "https://github.com"
        try:
            r = requests.get(url, timeout=30)
            with open(font_filename, "wb") as f:
                f.write(r.content)
            print(f"✅ 字體下載成功，大小: {os.path.getsize(font_filename)} bytes")
        except:
            return "Helvetica"

    try:
        # 強制註冊
        pdfmetrics.registerFont(TTFont('Chinese', font_filename))
        print("✅ 字體 'Chinese' 註冊成功")
        return 'Chinese'
    except Exception as e:
        print(f"❌ 字體註冊失敗: {e}")
        return "Helvetica"

def enhanced_process(data_list):
    font_name = setup_chinese_font()
    filename = "Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 1. 頁首
    c.setFillColor(colors.HexColor("#0D1B2A"))
    c.rect(0, height-110, width, 110, fill=1)
    c.setFillColor(colors.white)
    
    # 關鍵：如果在 Helvetica 下，中文會完全消失，所以我們確保字體存在
    c.setFont(font_name, 26)
    c.drawString(40, height-55, "AI 智慧量化交易監控報告")
    
    c.setFont(font_name, 10)
    c.drawString(40, height-85, f"報告日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 2. 表格標題
    y = height - 150
    c.setFillColor(colors.black)
    c.setFont(font_name, 12)
    c.drawString(40, y, f"【 本次掃描標的: {len(data_list)} 檔 】")
    
    y -= 30
    c.setFillColor(colors.HexColor("#F2F2F2"))
    c.rect(35, y-5, 525, 25, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont(font_name, 10)
    headers = ["證券名稱", "現價", "開盤", "建議進場", "停損防線", "預期獲利"]
    cols = [45, 130, 200, 280, 360, 440]
    
    for i, h in enumerate(headers):
        c.drawString(cols[i], y+2, h)

    # 3. 數據列
    y -= 25
    for item in data_list:
        c.setFont(font_name, 10)
        c.setFillColor(colors.black)
        
        name = STOCK_NAMES.get(str(item['stock_id']), "熱門標的")
        
        c.drawString(cols[0], y, f"{item['stock_id']} {name}")
        c.drawString(cols[1], y, f"{float(item['curr_p']):.2f}")
        c.drawString(cols[2], y, f"{float(item['open_p']):.2f}")
        
        c.setFillColor(colors.blue)
        c.drawString(cols[3], y, f"{float(item['entry_p']):.2f}")
        
        c.setFillColor(colors.red)
        c.drawString(cols[4], y, f"{float(item['exit_p']):.2f}")
        
        # 獲利落差
        diff_pct = ((float(item['pred_high']) - float(item['curr_p'])) / float(item['curr_p'])) * 100
        c.setFillColor(colors.green if diff_pct > 0 else colors.black)
        c.drawString(cols[5], y, f"{diff_pct:.1f}%")
        
        c.setStrokeColor(colors.lightgrey)
        c.line(35, y-5, 560, y-5)
        y -= 25

    c.save()
    return filename
