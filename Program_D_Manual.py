from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

def enhanced_process(prices, stock_id="None"):
    curr_p = prices[-1]
    filename = f"Trade_Report_{stock_id}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    
    # 繪製報表內容
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, f"STOCK ANALYSIS: {stock_id}")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 750, f"Current Price: {curr_p}")
    
    # 成本與跳動精算
    cost = curr_p * 0.00435
    tick = 0.05 if curr_p < 50 else 0.1 if curr_p < 100 else 0.5
    needed_ticks = int(cost / tick) + 1
    
    c.drawString(50, 720, f"Transaction Cost Estimate: {cost:.2f}")
    c.drawString(50, 700, f"Required Ticks to Break-even: {needed_ticks} ticks")
    
    c.setLineWidth(1)
    c.line(50, 680, 550, 680)
    c.drawString(50, 660, "Note: This is an AI generated report. Trade with caution.")
    
    c.save()
    return filename
