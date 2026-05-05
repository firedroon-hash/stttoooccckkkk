import os, time, importlib.util, gc, requests
from datetime import datetime
import pandas as pd
import Program_A_Fetcher as A

# 環境變數設定
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

class CoreSystem:
    def __init__(self):
        print(f"--- [系統啟動中] ---")
        print(f"Webhook 狀態: {'✅ OK' if WEBHOOK_URL else '❌ 缺失'}")
        self.data_service = A.get_data_service()
        
        # 預加載 C 與 D 程序，加速迴圈執行
        self.mod_c = self.load_module("Program_C_Enhanced.py")
        self.mod_d = self.load_module("Program_D_Manual.py")

    def load_module(self, filename):
        if not os.path.exists(filename): return None
        spec = importlib.util.spec_from_file_location("module", filename)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def send_to_discord(self, content):
        if not WEBHOOK_URL: return
        try:
            requests.post(WEBHOOK_URL, json={"content": content}, timeout=5)
        except Exception as e:
            print(f"傳訊失敗: {e}")

    def run_trading_mode(self):
        print(f"\n⚡ [極速掃描] {datetime.now().strftime('%H:%M:%S')}")
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        
        if df_all.empty:
            print("⚠️ 無法獲取數據")
            return

        up_ratio = len(df_all[df_all['change_rate'] > 0]) / len(df_all)
        print(f"📊 市場上漲比: {up_ratio:.1%}")

        # 排序主流標的
        targets = df_all.sort_values(by='amount', ascending=False)
        
        match_count = 0
        for _, row in targets.iterrows():
            context = {
                "up_ratio": up_ratio, 
                "change_rate": row['change_rate'], 
                "market_index": market_index, 
                "tick_details": pd.DataFrame() # 預設空，觸發 C 程式 0.5 判定
            }
            
            if self.mod_c:
                decision = self.mod_c.enhanced_process([row['last_price']]*10, context)
                if decision and decision.get("action") == "BUY":
                    match_count += 1
                    msg = f"🎯 **訊號**: {row['stock_id']} | 建議:{decision['entry']} | {decision['info']}"
                    print(f"✅ {msg}")
                    self.send_to_discord(msg)
                    # 產出報表
                    if self.mod_d: self.mod_d.enhanced_process([row['last_price']]*10)

        if match_count == 0: print("ℹ️ 掃描完成，未達進場門檻。")

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        # 判斷盤中時段
        if 900 <= t_int <= 1335:
            print(f"⏰ 進入監控時段 ({t_int})")
            # 每次 Action 跑 2 次掃描，間隔 30 秒，減少 GitHub 負擔
            for i in range(2):
                self.run_trading_mode()
                if i == 0: time.sleep(30)
        else:
            msg = f"🌙 系統待命回報 (時間: {t_int})"
            print(msg)
            self.send_to_discord(msg)

if __name__ == "__main__":
    CoreSystem().main()
    gc.collect()
