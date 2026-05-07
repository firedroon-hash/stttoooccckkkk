# ==============================================================================
# 程式名稱：Program_B_Core.py (AI 實戰中控核心 - v46.7 診斷強化版)
# ==============================================================================

import os, json, time, importlib.util, gc, requests, pandas as pd
import tempfile, shutil, sys, traceback, subprocess
from datetime import datetime

# === [超級強制修復：攔截 A 程式的錯誤路徑設定] ===
try:
    import yfinance as yf
    fix_path = os.path.join(tempfile.gettempdir(), "yf_final_fix")
    if not os.path.exists(fix_path): os.makedirs(fix_path)
    yf.set_tz_cache_location(fix_path)
    yf.set_tz_cache_location = lambda x: print(f"🛡️ [守護者] 已攔截並忽略 A 程式的無效路徑請求")
    print(f"📁 數據快取鎖定路徑: {fix_path}")
except Exception as e:
    print(f"⚠️ 預載入修復失敗: {e}")

import Program_A_Fetcher as A 
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- 從 GitHub Secrets 讀取變數 ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
MY_STRATEGY_KEY = os.environ.get("MY_STRATEGY_KEY", "").strip()
FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "").strip()

class AutoHealer:
    @staticmethod
    def diagnose_and_fix(error_trace):
        err = str(error_trace).lower()
        if "database is locked" in err or "nonetype" in err:
            return "RETRY"
        if "modulenotfounderror" in err:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "pandas", "requests"])
            return "RELOAD"
        return "ABORT"

class CoreSystem:
    def __init__(self):
        print(f"[{datetime.now()}] 🚀 系統初始化 (v46.7)")
        self.data_service = A.get_data_service(FINMIND_TOKEN)
        self.sent_stocks = {} 
        self.capital = 1000000.0 
        self.per_trade = 200000.0 
        self.mod_f = self.load_encrypted_f() 
        self.mod_d = self.load_module("Program_D_Manual.py")
        self.mod_e = self.load_module("Program_E_Evolution.py")
        self.send_to_discord(f"✅ 系統啟動成功！目前正在盤中監控中...")

    def load_encrypted_f(self):
        if not MY_STRATEGY_KEY: return self.load_module("Program_F_Strategy.py")
        key = MY_STRATEGY_KEY.ljust(32)[:32].encode('utf-8')
        iv = b'1234567890123456'
        bin_path = "Program_F_Encrypted.bin"
        if os.path.exists(bin_path):
            try:
                with open(bin_path, "rb") as f: ciphertext = f.read()
                cipher = AES.new(key, AES.MODE_CBC, iv)
                code = unpad(cipher.decrypt(ciphertext), AES.block_size).decode('utf-8')
                local_vars = {}
                exec(code, globals(), local_vars)
                print("🔒 [策略區] F 策略解密載入成功")
                return type('StrategyMod', (object,), {'enhanced_process': local_vars['enhanced_process']})
            except: return None
        return self.load_module("Program_F_Strategy.py")

    def load_module(self, filename):
        if not os.path.exists(filename): return None
        spec = importlib.util.spec_from_file_location("module", filename)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        return mod

    def send_to_discord(self, message, file_path=None):
        if not WEBHOOK_URL: return
        try:
            payload = {"content": message}
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f: requests.post(WEBHOOK_URL, data=payload, files={"file": f})
            else: requests.post(WEBHOOK_URL, json=payload)
        except: pass

    def run_trading_mode(self):
        """盤中監控：整合一秒選股、一鍵試算、一眼監控功能"""
        now_time = datetime.now().strftime('%H:%M:%S')
        print(f"⚡ [監控中] 當前時間: {now_time}")
        try:
            df_all = self.data_service.fetch_market_snapshot()
            market_index = self.data_service.fetch_index_status()
        except: return
        
        if df_all is None or df_all.empty: return

        matched_list = []
        # 篩選成交量前 50 名標的
        for _, row in df_all.sort_values(by='amount', ascending=False).head(50).iterrows():
            sid = row['stock_id']
            if sid in self.sent_stocks and (time.time() - self.sent_stocks[sid]) < 3600: continue
            
            print(f"🔍 檢查標的: {sid}", end=" | ")

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
                    action = decision.get("action", "HOLD")
                    
                    if action == "BUY":
                        print(f"✅ 買入訊號觸發！")
                        self.sent_stocks[sid] = time.time()
                        
                        # 功能 2：自動帶入條件並試算損益
                        real_entry = max(decision['entry'], row.get('ask_p', row['last_price']))
                        shares = int(self.per_trade / (real_entry * 1000))
                        # 試算預期損益金額 (1000股=1張)
                        est_profit = (decision['pred_high'] - real_entry) * shares * 1000
                        
                        if shares > 0:
                            trade_record = {
                                'date': datetime.now().strftime("%Y-%m-%d"), 'time': now_time,
                                'stock_id': sid, 'open_p': row['open_price'], 'curr_p': row['last_price'],
                                'high_p': row['high_price'], 'low_p': row['low_price'],
                                'entry_p': real_entry, 'exit_p': decision['stop_loss'],
                                'pred_high': decision['pred_high'], 'shares': shares, 'status': 'OPEN',
                                'est_profit': est_profit, # [新增] 試算損益
                                'info': decision.get('info', '🚀 策略當沖訊號觸發') # 功能 3：狀態追蹤
                            }
                            matched_list.append(trade_record)
                            pd.DataFrame([trade_record]).to_csv("history_log.csv", mode='a', header=not os.path.exists("history_log.csv"), index=False)
                    else:
                        print(f"💤 條件不符 (HOLD)")
            except Exception as e:
                print(f"❌ 診斷失敗: {e}")

        # 功能 1 & 3：一秒選股與一眼監控傳訊
        if matched_list and self.mod_d:
            try:
                # 取得選股代號列表
                stock_ids = [d['stock_id'] for d in matched_list]
                stock_str = ", ".join(stock_ids)
                
                # 組裝 Discord 訊息：達成「一秒選股」與「快速追蹤即時交易」
                summary_msg = (
                    f"🎯 **【策略當沖股一秒快選】**: `{stock_str}`\n"
                    f"📝 **交易狀態**: `自動追蹤中` | **當前標的數**: `{len(matched_list)}`\n"
                    f"💡 *提示：進出場條件與損益試算請見下方 PDF 報告*"
                )
                
                pdf_path = self.mod_d.enhanced_process(matched_list)
                self.send_to_discord(summary_msg, pdf_path)
                if pdf_path and os.path.exists(pdf_path): os.remove(pdf_path)
            except: pass


    def main_logic(self):
        t_int = int(datetime.now().strftime("%H%M"))
        if 900 <= t_int <= 1330:
            for i in range(2):
                self.run_trading_mode()
                if i < 1: time.sleep(60)
        elif 1331 <= t_int <= 1400:
            if self.mod_e: self.mod_e.run_evolution()
        else:
            print(f"🌙 非交易時段 ({t_int})，系統待命。")

def execution_wrapper():
    try:
        app = CoreSystem()
        app.main_logic()
    except Exception:
        err_trace = traceback.format_exc()
        action = AutoHealer.diagnose_and_fix(err_trace)
        if action == "RETRY": execution_wrapper()
        elif action == "RELOAD": os.execv(sys.executable, ['python'] + sys.argv)
        else:
            dummy = CoreSystem()
            dummy.send_to_discord(f"🚨 **系統致命錯誤報警**\n```{err_trace[-300:]}```")

if __name__ == "__main__":
    os.environ['TZ'] = 'Asia/Taipei'
    if hasattr(time, 'tzset'): time.tzset()
    execution_wrapper()
    gc.collect()
