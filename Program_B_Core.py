import os, json, time, importlib.util, gc
from datetime import datetime
import pandas as pd
import requests

# 嘗試導入數據引擎
try:
    import Program_A_Fetcher as A
except ImportError:
    print("❌ [錯誤] 找不到 Program_A_Fetcher.py")

# 讀取 Secret 環境變數
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

class CoreSystem:
    def __init__(self):
        print(f"--- [系統初始化] ---")
        print(f"Webhook URL 檢查: {'✅ 已讀取' if WEBHOOK_URL else '❌ 未讀取 (請檢查 GitHub Secrets)'}")
        self.data_service = A.get_data_service()

    def send_to_discord(self, content, file_path=None):
        """【傳訊區段】專責訊息發送與診斷"""
        print(f"📡 [傳訊中] 內容預覽: {content[:30]}...")
        if not WEBHOOK_URL:
            print("⚠️ [傳訊中斷] 原因：WEBHOOK_URL 為空值")
            return

        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    r = requests.post(WEBHOOK_URL, data={'content': content}, files={'file': f}, timeout=10)
            else:
                r = requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
            
            if r.status_code == 204 or r.status_code == 200:
                print(f"✅ [傳訊成功] Discord 回傳狀態碼: {r.status_code}")
            else:
                print(f"❌ [傳訊失敗] Discord 回傳錯誤: {r.status_code}, 內容: {r.text}")
        except Exception as e:
            print(f"❌ [傳訊異常] 發生錯誤: {e}")

    def run_trading_mode(self):
        """【分析區段】專責數據抓取與 AI 決策"""
        print(f"\n🔍 [分析啟動] {datetime.now().strftime('%H:%M:%S')}")
        
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        
        if df_all.empty:
            print("⚠️ [分析中止] 無法從 API 獲取任何市場數據")
            return

        up_ratio = len(df_all[df_all['change_rate'] > 0]) / len(df_all)
        print(f"📈 [數據] 市場上漲比: {up_ratio:.1%}, 掃描股票數: {len(df_all)}")

        # 排序前 50 名
        df_all['amount_rank'] = df_all['amount'].rank(ascending=False)
        targets = df_all.nlargest(50, 'amount')
        
        match_count = 0
        for _, row in targets.iterrows():
            tick = self.data_service.fetch_tick_details(row['stock_id'])
            context = {"up_ratio": up_ratio, "change_rate": row['change_rate'], "market_index": market_index, "tick_details": tick}
            
            # 調用 C 程式 (AI 大腦)
            try:
                spec = importlib.util.spec_from_file_location("C", "Program_C_Enhanced.py")
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                decision = mod.enhanced_process([row['last_price']]*10, context)
            except Exception as e:
                print(f"❌ [分析異常] 執行 Program_C 失敗: {e}")
                continue
            
            if decision and decision.get("action") == "BUY":
                match_count += 1
                msg = f"🎯 [訊號發現] {row['stock_id']} | 建議價: {decision['entry']}"
                print(msg)
                self.send_to_discord(msg)
                
                # 調用 D 程式產出報告
                try:
                    spec_d = importlib.util.spec_from_file_location("D", "Program_D_Manual.py")
                    mod_d = importlib.util.module_from_spec(spec_d)
                    spec_d.loader.exec_module(mod_d)
                    mod_d.enhanced_process([row['last_price']]*10)
                except: pass

        if match_count == 0:
            print("ℹ️ [分析結果] 掃描完畢，目前無符合 AI 買入標準的標的")

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        # 1021 這種格式判斷
        if 905 <= t_int <= 1330:
            print(f"⏰ [時段確認] 目前為盤中監控時段 ({t_int})")
            self.run_trading_mode()
        else:
            print(f"💤 [時段確認] 目前非交易時段 ({t_int})")
            self.send_to_discord(f"🌙 AI 系統待命回報 (目前時間: {t_int})")

if __name__ == "__main__":
    CoreSystem().main()
    gc.collect()
