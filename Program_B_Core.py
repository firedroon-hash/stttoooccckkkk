# ==============================================================================
# 程式名稱：Program_B_Core.py (AI 實戰中控核心 - v38.2 完整版)
# ==============================================================================
import os, time, importlib.util, gc, requests
from datetime import datetime
import Program_A_Fetcher as A

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

class CoreSystem:
    def __init__(self):
        print(f"[{datetime.now()}] 🚀 系統啟動中...")
        self.data_service = A.get_data_service()
        self.sent_stocks = {} # 記錄已發送股票，防止洗板
        
        # 預加載 F (策略) 與 D (報告)
        self.mod_f = self.load_module("Program_F_Strategy.py") 
        self.mod_d = self.load_module("Program_D_Manual.py")

    def load_module(self, filename):
        if not os.path.exists(filename): return None
        spec = importlib.util.spec_from_file_location("module", filename)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def send_to_discord(self, content, file_path=None):
        if not WEBHOOK_URL: return
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    requests.post(WEBHOOK_URL, data={'content': content}, files={'file': f}, timeout=15)
            else:
                requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
        except Exception as e:
            print(f"傳訊異常: {e}")

    def run_trading_mode(self):
        print(f"⚡ [深度監控] {datetime.now().strftime('%H:%M:%S')}")
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        
        if df_all.empty: return

        up_ratio = len(df_all[df_all['change_rate'] > 0]) / len(df_all) if len(df_all) > 0 else 0.5
        # [功能 3] 成交量排序 (保留原功能)
        df_all['amount_rank'] = df_all['amount'].rank(ascending=False)
        targets = df_all.sort_values(by='amount', ascending=False).head(50)

        for _, row in targets.iterrows():
            sid = row['stock_id']
            now_ts = time.time()
            
            # [功能 12] 一小時去重過濾
            if sid in self.sent_stocks and (now_ts - self.sent_stocks[sid]) < 3600:
                continue

            # [功能 4] 內外盤模擬 (從 A 抓取)
            tick_details = self.data_service.fetch_tick_details(sid)
            out_ratio = 0.5 
            if not tick_details.empty:
                out_ratio = len(tick_details[tick_details['tick_type'] == 1]) / len(tick_details)

            prices = [row['last_price']] * 10
            context = {
                "up_ratio": up_ratio, 
                "change_rate": row['change_rate'], 
                "market_index": market_index,
                "tick_details": tick_details
            }

            # [調用 F 核心策略]
            if self.mod_f:
                decision = self.mod_f.enhanced_process(prices, context)
                if decision and decision.get("action") == "BUY":
                    self.sent_stocks[sid] = now_ts
                    
                    # 彙整數據給 D 程式 (加入所有分析維度)
                    report_data = {
                        'stock_id': sid,
                        'open_p': row['open_price'],
                        'curr_p': row['last_price'],
                        'high_p': row['high_price'],
                        'low_p': row['low_price'],
                        'entry_p': decision['entry'],
                        'exit_p': decision.get('stop_loss', 0),
                        'pred_high': decision.get('pred_high', 0),
                        'out_ratio': out_ratio,
                        'info': decision.get('info', '')
                    }
                    
                    # [功能 9] 生成專業 PDF
                    pdf_file = None
                    if self.mod_d:
                        pdf_file = self.mod_d.enhanced_process(report_data)
                    
                    msg = f"🎯 **買入訊號**: {sid} | 預判高點: {decision.get('pred_high')} | 強勢度: {out_ratio:.1%}"
                    self.send_to_discord(msg, pdf_file)
                    
                    # 發送後清理檔案
                    if pdf_file and os.path.exists(pdf_file): os.remove(pdf_file)

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        # 嚴格律定執行時間 09:00 - 14:00
        if 900 <= t_int <= 1400:
            self.run_trading_mode()
        else:
            print(f"🌙 休息時間 ({t_int})")

if __name__ == "__main__":
    CoreSystem().main(); gc.collect()
