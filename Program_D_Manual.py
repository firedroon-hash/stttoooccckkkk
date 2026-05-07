# ==============================================================================
# 程式名稱：Program_D_Manual.py (AI 智慧視覺報告官 - v46.9 專業分析增強版)
# ==============================================================================

import os, requests, time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# --- 完整中文名稱對照表 (同步 A 程式最新清單) ---
STOCK_NAMES = {
    '2330': '台積電', '2317': '鴻海', '2454': '聯發科', '2303': '聯電',
    '2603': '長榮', '2609': '陽明', '2615': '萬海', '2382': '廣達',
    '3231': '緯創', '2376': '技嘉', '1513': '中興電', '1504': '東元',
    '3481': '群創', '2409': '友達', '2308': '台達電', '2357': '華碩',
    '1519': '華城', '1514': '亞力', '1605': '華新', '2618': '長榮航',
    '2610': '華航', '1503': '士電', '2353': '宏碁', '2449': '京元電'
}

def setup_chinese_font():
    """下載並註冊思源黑體，解決雲端環境中文亂碼"""
    font_filename = "NotoSansTC-Regular.ttf"
    if not os.path.exists(font_filename):
        print("📡 正在加載專業中文字體...")
        # 使用 Google Fonts 的直接鏈結確保下載成功
        url = "https://github.com"
        try:
            r = requests.get(url, timeout=30)
            with open(font_filename, "wb") as f: f.write(r.content)
        except: return "Helvetica"
    try:
        pdfmetrics.registerFont(TTFont('SourceHan', font_filename))
        return 'SourceHan'
    except: return "Helvetica"

def enhanced_process(data_list):
    """生成專業級 PDF 報告"""
    font_name = setup_chinese_font()
    filename = "Daily_Analysis_Report.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # 1. 頁首專業化設計
    c.setFillColor(colors.HexColor("#0D1B2A")) # 更深邃的商務藍
    c.rect(0, height-110, width, 110, fill=1)
    
    c.setFillColor(colors.white)
    c.setFont(font_name, 28)
    c.drawString(40, height-55, "AI 智慧量化交易監控報告")
    
    c.setFont(font_name, 11)
    c.drawString(40, height-85, f"報告編號: {datetime.now().strftime('%Y%m%d%H%M')} | 實戰模擬環境 (v46.9)")
    c.drawRightString(width-40, height-85, f"生成時間: {datetime.now().strftime('%H:%M:%S')}")

    # 2. [新增] 快速摘要資訊區
    y = height - 140
    c.setFillColor(colors.black)
    c.setFont(font_name, 12)
    c.drawString(40, y, f"【 本次掃描標的數: {len(data_list)} 檔 】")
    
    # 畫一條分隔線
    c.setStrokeColor(colors.HexColor("#E0E0E0"))
    c.setLineWidth(1)
    c.line(35, y-10, 560, y-10)

    # 3. 表格標題 (精緻化欄位)
    y -= 45
    c.setFillColor(colors.HexColor("#F8F9FA"))
    c.rect(35, y-5, 525, 28, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor("#2C3E50"))
    c.setFont(font_name, 10)
    # [優化] 欄位重新分配，加入風報比 (R/R)
    headers = ["證券名稱", "現價/開盤", "建議進場", "防線(停損)", "目標高點", "預期空間", "風報比"]
    cols = [45, 125, 205, 285, 365, 435, 505]
    for i, h in enumerate(headers):
        c.drawString(cols[i], y+4, h)

    # 4. 數據填充
    y -= 30
    for i, item in enumerate(data_list):
        # 隔行著色
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#FFFFFF"))
        else:
            c.setFillColor(colors.HexColor("#FDFDFD"))
        c.rect(35, y-5, 525, 25, fill=1, stroke=0)
        
        # 數據提取
        sid = item['stock_id']
        name = STOCK_NAMES.get(sid, "熱門標的")
        curr_p = item['curr_p']
        entry_p = item['entry_p']
        exit_p = item['exit_p']
        pred_h = item['pred_high']
        
        # [計算] 獲利空間與風報比 (獲利空間 / 承擔風險)
        reward = pred_h - entry_p
        risk = entry_p - exit_p if entry_p > exit_p else 0.01
        rr_ratio = reward / risk if risk > 0 else 0
        diff_pct = (reward / curr_p) * 100 if curr_p > 0 else 0
        
        # A. 名稱與價格
        c.setFillColor(colors.black)
        c.setFont(font_name, 10)
        c.drawString(cols[0], y+2, f"{sid} {name}")
        c.setFont(font_name, 9)
        c.drawString(cols[1], y+2, f"{curr_p:,.1f}/{item['open_p']:,.1f}")
        
        # B. 建議進場用深藍加粗
        c.setFillColor(colors.HexColor("#0056B3"))
        c.setFont(font_name, 10)
        c.drawString(cols[2], y+2, f"{entry_p:,.2f}")
        
        # C. 停損用亮紅
        c.setFillColor(colors.HexColor("#D90429"))
        c.drawString(cols[3], y+2, f"{exit_p:,.2f}")
        
        # D. 目標價與空間
        c.setFillColor(colors.black)
        c.drawString(cols[4], y+2, f"{pred_h:,.2f}")
        
        # 亮色空間標註
        if diff_pct > 3.0:
            c.setFillColor(colors.red) # 空間大於 3% 顯示紅色提醒
            label = f"↑ {diff_pct:.1f}%"
        else:
            c.setFillColor(colors.black)
            label = f"{diff_pct:.1f}%"
        c.drawString(cols[5], y+2, label)
        
        # E. 風報比視覺化 (大於 2 代表不錯的交易)
        if rr_ratio >= 2.5:
            c.setFillColor(colors.green)
            rr_label = f"{rr_ratio:.1f} ★"
        else:
            c.setFillColor(colors.grey)
            rr_label = f"{rr_ratio:.1f}"
        c.drawString(cols[6], y+2, rr_label)
        
        # 分隔線
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.3)
        c.line(35, y-5, 560, y-5)
        
        y -= 25
        if y < 70: # 自動分頁
            c.showPage()
            y = height - 50
            # 換頁補標題... (簡化處理)

    # 5. 免責聲明與浮水印
    c.setFont(font_name, 8)
    c.setFillColor(colors.grey)
    c.drawCentredString(width/2, 25, "警語：本報表為量化模型回測結果，不構成邀約投資。交易者應自行負責損益風險。")
    
    # 加上淡淡的浮水印
    c.rotate(45)
    c.setFillColorRGB(0.9, 0.9, 0.9, 0.1)
    c.setFont(font_name, 40)
    c.drawCentredString(width/1.5, 0, "AI REAL-TIME ANALYSIS")

    c.save()
    return filename
