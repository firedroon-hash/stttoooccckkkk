# ==============================================================================
# 程式名稱：Program_B_Core.py (AI 實戰中控核心 - v46.1 終極版)
# ------------------------------------------------------------------------------
# 實戰功能：
# 1. 100萬本金分配 2. AES-256 解密 3. 盤中 PDF 彙整 4. 盤後 E 程式自動結算
# ==============================================================================

import os, json, time, importlib.util, gc, requests, pandas as pd
from datetime import datetime
import Program_A_Fetcher as A
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- 從 GitHub Secrets 讀取變數 ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
MY_STRATEGY_KEY = os.environ.get("MY_STRATEGY_KEY", "").strip()
FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "").strip()

class CoreSystem:
    def __init__(self):
        print(f"[{datetime.now()}] 🚀 系統初始化 (v46.1)")
        self.data_service = A.get_data_service(FINMIND_TOKEN)
        self.sent_stocks = {} 
        self.capital = 1000000.0 # 100 萬總本金
        self.per_trade = 200000.0 # 每檔限制 20 萬
        
        # 1. 加載核心策略 (優先解密)
        self.mod_f = self.load_encrypted_f() 
        # 2. 加載 PDF 報告官
        self.mod_d = self.load_module("Program_D_Manual.py")
        # 3. 加載結算進化官
        self.mod_e = self.load_module("Program_E_Evolution.py")

    def load_encrypted_f(self):
        """解密黑盒子 F 策略"""
        if not MY_STRATEGY_KEY: return self.load_module("Program_F_Strategy.py")
        key = MY_STRATEGY_KEY.ljust(32)[:32].encode('utf-8')
        iv = b'1234567890123456'
        bin_path = "Program_F_Encrypted.bin"
        if os.path.exists(bin_path):
            try:
                with open(bin_path, "rb") as f:
                    ciphertext = f.read()
                cipher = AES.new(key, AES.MODE_CBC, iv)
                code = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
                local_vars = {}
                exec(code, globals(), local_vars)
                print("🔒 [策略區] 黑盒子解密成功")
                return type('StrategyMod', (object,), {'enhanced_process': local_vars['enhanced_process']})
            except Exception as e:
                print(f"🔑 [策略區] 解密失敗: {e}"); return None
        return self.load_module("Program_F_Strategy.py")

    def load_module(self, filename):
        if not os.path.exists(filename): return None
        spec = importlib.util.spec_from_file_location("module", filename)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod

    def send_to_discord(self, content, file_path=None):
        if not WEBHOOK_URL: return
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    requests.post(WEBHOOK_URL, data={'content': content}, files={'file': f}, timeout=25)
            else:
                requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
        except: pass

    def run_trading_mode(self):
        """盤中監控與真實成交模擬"""
        print(f"⚡ [監控中] {datetime.now().strftime('%H:%M:%S')}")
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        if df_all.empty: return

        matched_list = []
        history_file = "history_log.csv"

        for _, row in df_all.sort_values(by='amount', ascending=False).head(50).iterrows():
            sid = row['stock_id']
            if sid in self.sent_stocks and (time.time() - self.sent_stocks[sid]) < 3600: continue
            if not row.get('is_liquid', True): continue

            # 模擬掛單與數據餵入 F 策略
            tick_details = self.data_service.fetch_tick_details(sid)
            prices = [row['last_price']] * 10
            context = {
                "up_ratio": len(df_all[df_all['change_rate'] > 0]) / len(df_all),
                "change_rate": row['change_rate'], "market_index": market_index,
                "tick_details": tick_details, "ask_p": row.get('ask_p', row['last_price'])
            }

            if self.mod_f:
                decision = self.mod_f.enhanced_process(prices, context)
                if decision and decision.get("action") == "BUY":
                    self.sent_stocks[sid] = time.time()
                    # 模擬成交：強制以賣價(Ask)成交
                    real_entry = max(decision['entry'], row.get('ask_p', row['last_price']))
                    shares = int(self.per_trade / (real_entry * 1000))
                    
                    if shares > 0:
                        trade_record = {
                            'date': datetime.now().strftime("%Y-%m-%d"), 'time': datetime.now().strftime("%H:%M:%S"),
                            'stock_id': sid, 'open_p': row['open_price'], 'curr_p': row['last_price'],
                            'high_p': row['high_price'], 'low_p': row['low_price'],
                            'entry_p': real_entry, 'exit_p': decision['stop_loss'],
                            'pred_high': decision['pred_high'], 'shares': shares, 'status': 'OPEN',
                            'info': decision.get('info', '')
                        }
                        matched_list.append(trade_record)
                        # 紀錄至 CSV
                        pd.DataFrame([trade_record]).to_csv(history_file, mode='a', header=not os.path.exists(history_file), index=False)

        if matched_list and self.mod_d:
            pdf = self.mod_d.enhanced_process(matched_list)
            ids = ", ".join([d['stock_id'] for d in matched_list])
            self.send_to_discord(f"🎯 **AI 買入訊號**: {ids}", pdf)
            if pdf and os.path.exists(pdf): os.remove(pdf)

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        
        # 1. 盤中監控 (09:00 - 13:30)
        if 900 <= t_int <= 1330:
            print(f"⏰ 盤中監控時段 ({t_int})")
            for i in range(2):
                self.run_trading_mode()
                if i == 0: time.sleep(60)
                
        # 2. 盤後結算 (13:31 - 14:00)
        elif 1331 <= t_int <= 1400:
            print(f"💾 執行收盤結算戰報...")
            if self.mod_e:
                try:
                    self.mod_e.run_evolution()
                except Exception as e:
                    print(f"❌ 結算異常: {e}")
            else:
                print("⚠️ 找不到結算模組")
        else:
            print(f"🌙 系統待命 ({t_int})")

if __name__ == "__main__":
    os.environ['TZ'] = 'Asia/Taipei'
    if hasattr(time, 'tzset'): time.tzset()
    CoreSystem().main()
    gc.collect()
