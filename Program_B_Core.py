import os, time, importlib.util, gc, requests
from datetime import datetime
import pandas as pd
import Program_A_Fetcher as A

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

class CoreSystem:
    def __init__(self):
        self.data_service = A.get_data_service()
        self.sent_stocks = {} # 格式: {'2317': timestamp}
        # 預加載 F (核心策略) 與 D (報告官)
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
                    requests.post(WEBHOOK_URL, data={'content': content}, files={'file': f}, timeout=10)
            else:
                requests.post(WEBHOOK_URL, json={"content": content}, timeout=5)
        except: pass

    def run_trading_mode(self):
        print(f"⚡ [監控中] {datetime.now().strftime('%H:%M:%S')}")
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        if df_all.empty: return

        up_ratio = len(df_all[df_all['change_rate'] > 0]) / len(df_all)
        targets = df_all.sort_values(by='amount', ascending=False)
        
        for _, row in targets.iterrows():
            sid = row['stock_id']
            now_ts = time.time()
            
            # 去重：1 小時內發送過的不再重複
            if sid in self.sent_stocks and (now_ts - self.sent_stocks[sid]) < 3600:
                continue

            context = {"up_ratio": up_ratio, "change_rate": row['change_rate'], "market_index": market_index}
            
            # 調用 F 程式 (核心策略)
            if self.mod_f:
                decision = self.mod_f.enhanced_process([row['last_price']]*10, context)
                if decision and decision.get("action") == "BUY":
                    self.sent_stocks[sid] = now_ts
                    msg = f"🎯 **買入訊號**: {sid} | 建議:{decision['entry']} | {decision['info']}"
                    
                    # 調用 D 程式 (報告官) 產出 PDF
                    pdf_path = None
                    if self.mod_d:
                        self.mod_d.enhanced_process([row['last_price']]*10, sid)
                        pdf_path = f"Trade_Report_{sid}.pdf"
                    
                    self.send_to_discord(msg, pdf_path)
                    if pdf_path and os.path.exists(pdf_path): os.remove(pdf_path)

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        if 905 <= t_int <= 1330:
            for i in range(2):
                self.run_trading_mode()
                if i == 0: time.sleep(45)
        elif 1331 <= t_int <= 1400:
            print("💾 盤後結算時間...")
            # 這裡可以呼叫 Program_E
        else:
            print(f"🌙 系統待命 ({t_int})")

if __name__ == "__main__":
    CoreSystem().main(); gc.collect()
