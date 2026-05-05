import os, json, time, importlib.util, gc
from datetime import datetime
import pandas as pd
import Program_A_Fetcher as A

FINMIND_TOKEN = "YOUR_TOKEN"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

class CoreSystem:
    def __init__(self):
        self.data_service = A.get_data_service(FINMIND_TOKEN)

    def send_to_discord(self, content, file_path=None):
        if not WEBHOOK_URL: return
        import requests
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                requests.post(WEBHOOK_URL, data={'content': content}, files={'file': f})
        else:
            requests.post(WEBHOOK_URL, json={"content": content})

    def run_trading_mode(self):
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        if df_all.empty: return
        
        up_ratio = len(df_all[df_all['change_rate'] > 0]) / len(df_all)
        targets = df_all.nlargest(50, 'amount')
        
        for _, row in targets.iterrows():
            tick = self.data_service.fetch_tick_details(row['stock_id'])
            context = {"up_ratio": up_ratio, "change_rate": row['change_rate'], "market_index": market_index, "tick_details": tick}
            
            # 動態加載 C
            spec = importlib.util.spec_from_file_location("C", "Program_C_Enhanced.py")
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            decision = mod.enhanced_process([row['last_price']]*10, context)
            
            if decision and decision.get("action") == "BUY":
                self.send_to_discord(f"🎯 訊號: {row['stock_id']} | 建議:{decision['entry']} | {decision['info']}")
                # 動態加載 D 產出 PDF
                spec_d = importlib.util.spec_from_file_location("D", "Program_D_Manual.py")
                mod_d = importlib.util.module_from_spec(spec_d); spec_d.loader.exec_module(mod_d)
                mod_d.enhanced_process([row['last_price']]*10)
                pdf = f"Trade_Report_{datetime.now().strftime('%Y-%m-%d')}.pdf"
                if os.path.exists(pdf): self.send_to_discord(f"📊 {row['stock_id']} 報告", pdf)

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        if 905 <= t_int <= 1330:
            for _ in range(4): self.run_trading_mode(); time.sleep(60)
        else: self.send_to_discord(f"🌙 系統待命 ({t_int})")

if __name__ == "__main__":
    CoreSystem().main(); gc.collect()
