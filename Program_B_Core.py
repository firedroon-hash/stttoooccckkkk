# ==============================================================================
# 程式名稱：Program_B_Core.py (AI 實戰中控核心 - v46.5 自我修復守護者版)
# ==============================================================================

import os, json, time, importlib.util, gc, requests, pandas as pd
import tempfile, shutil, sys, traceback, subprocess
from datetime import datetime
import Program_A_Fetcher as A
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- 從 GitHub Secrets 讀取變數 ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
MY_STRATEGY_KEY = os.environ.get("MY_STRATEGY_KEY", "").strip()
FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "").strip()

class AutoHealer:
    """自我修復中控：負責診斷錯誤並執行修復策略"""
    @staticmethod
    def diagnose_and_fix(error_trace):
        err = str(error_trace).lower()
        print(f"🛠️ [守護者] 正在診斷錯誤...")
        
        # 1. 處理 yfinance 資料庫鎖定或路徑錯誤
        if "database is locked" in err or "noneType" in err or "stat: path" in err:
            print("💡 診斷結果: yfinance 數據庫鎖定。執行修復: 強制重置快取環境。")
            tmp_dir = os.path.join(tempfile.gettempdir(), f"yf_repair_{int(time.time())}")
            os.makedirs(tmp_dir, exist_ok=True)
            try:
                import yfinance as yf
                yf.set_tz_cache_location(tmp_dir)
            except: pass
            return "RETRY"

        # 2. 處理套件遺失
        if "modulenotfounderror" in err:
            missing = err.split("'")[1] if "'" in err else "yfinance"
            print(f"💡 診斷結果: 缺少套件 {missing}。執行修復: 自動安裝。")
            subprocess.check_call([sys.executable, "-m", "pip", "install", missing])
            return "RELOAD"

        # 3. 處理 Discord 網路超時
        if "connection" in err or "timeout" in err:
            print("💡 診斷結果: 網路連線異常。執行修復: 等待 30 秒後重試。")
            time.sleep(30)
            return "RETRY"

        return "ABORT"

class CoreSystem:
    def __init__(self):
        print(f"[{datetime.now()}] 🚀 系統初始化 (v46.5)")
        self.data_service = A.get_data_service(FINMIND_TOKEN)
        self.sent_stocks = {} 
        self.capital = 1000000.0 
        self.per_trade = 200000.0 
        
        # 1. 策略與報表模組載入
        self.mod_f = self.load_encrypted_f() 
        self.mod_d = self.load_module("Program_D_Manual.py")
        self.mod_e = self.load_module("Program_E_Evolution.py")
        
        self.send_to_discord(f"✅ 系統初始化成功 (時間: {datetime.now().strftime('%H:%M:%S')})")

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

    def send_to_discord(self, message, file_path=None):
        url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not url: return
        payload = {"content": message}
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    response = requests.post(url, data=payload, files={"file": f})
            else:
                response = requests.post(url, json=payload)
            if response.status_code in [200, 204]:
                print(f"📡 Discord 發送成功")
        except: pass

    def run_trading_mode(self):
        """盤中監控核心邏輯 (原封不動保留)"""
        print(f"⚡ [監控中] {datetime.now().strftime('%H:%M:%S')}")
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        
        if df_all is None or df_all.empty:
            print("⚠️ 目前無法獲取快照數據")
            return

        matched_list = []
        history_file = "history_log.csv"

        for _, row in df_all.sort_values(by='amount', ascending=False).head(50).iterrows():
            sid = row['stock_id']
            if sid in self.sent_stocks and (time.time() - self.sent_stocks[sid]) < 3600: continue
            if not row.get('is_liquid', True): continue

            try:
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
                        print(f"🎯 [觸發] {sid}")
                        self.sent_stocks[sid] = time.time()
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
                            pd.DataFrame([trade_record]).to_csv(history_file, mode='a', header=not os.path.exists(history_file), index=False)
            except Exception as e:
                print(f"🔍 標的 {sid} 處理跳過: {e}")

        if matched_list and self.mod_d:
            try:
                pdf_path = self.mod_d.enhanced_process(matched_list)
                ids = ", ".join([d['stock_id'] for d in matched_list])
                self.send_to_discord(f"🎯 AI 買入訊號: {ids}", pdf_path)
                if pdf_path and os.path.exists(pdf_path): os.remove(pdf_path)
            except Exception as e:
                print(f"❌ 報表生成失敗: {e}")

    def main_logic(self):
        """核心排程邏輯"""
        t_int = int(datetime.now().strftime("%H%M"))
        if 900 <= t_int <= 1330:
            print(f"⏰ 盤中監控時段 ({t_int})")
            for i in range(2):
                self.run_trading_mode()
                if i < 1: time.sleep(60)
        elif 1331 <= t_int <= 1400:
            if self.mod_e: self.mod_e.run_evolution()
        else:
            print(f"🌙 系統待命 ({t_int})")

def execution_wrapper():
    """自我修復外殼：監控 main_logic 並在失敗時重啟"""
    try:
        app = CoreSystem()
        app.main_logic()
    except Exception:
        err_trace = traceback.format_exc()
        print(f"🆘 偵測到程式崩潰:\n{err_trace}")
        
        # 執行診斷與修復
        action = AutoHealer.diagnose_and_fix(err_trace)
        
        if action == "RETRY":
            print("🔄 嘗試重新執行...")
            execution_wrapper()
        elif action == "RELOAD":
            print("♻️ 重載進程...")
            os.execv(sys.executable, ['python'] + sys.argv)
        else:
            # 無法修復則回報 Discord
            dummy = CoreSystem()
            dummy.send_to_discord(f"🚨 **系統致命崩潰**\n```{err_trace[-500:]}```")

if __name__ == "__main__":
    os.environ['TZ'] = 'Asia/Taipei'
    if hasattr(time, 'tzset'): time.tzset()
    
    # 啟動帶有守護者的外殼
    execution_wrapper()
    gc.collect()
