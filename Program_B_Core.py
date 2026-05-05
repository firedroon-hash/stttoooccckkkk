# ==============================================================================
# 程式名稱：Program_B_Core.py (AI 實戰中控核心 - v42.2 全變數隱藏版)
# ------------------------------------------------------------------------------
# 修正紀錄：
# 1. 移除硬編碼的 FINMIND_TOKEN，改由 os.environ 讀取 GitHub Secrets。
# 2. 完美整合 AES-256 解密、多檔彙整 PDF、與重複發送過濾功能。
# ==============================================================================

import os, json, time, importlib.util, gc, requests
from datetime import datetime
import Program_A_Fetcher as A
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- 從 GitHub Secrets 讀取所有關鍵變數 ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "").strip() # ✅ 已修改為環境變數讀取
MY_STRATEGY_KEY = os.environ.get("MY_STRATEGY_KEY", "").strip()

class CoreSystem:
    def __init__(self):
        print(f"[{datetime.now()}] 🚀 系統初始化 (v42.2 全隱藏版)")
        # 確保 A 程式能拿到 Token (儘管雙引擎版 A 程式目前主要用 OpenAPI/yfinance)
        self.data_service = A.get_data_service(FINMIND_TOKEN)
        self.sent_stocks = {} 
        
        # 優先嘗試解密核心策略
        self.mod_f = self.load_encrypted_f() 
        self.mod_d = self.load_module("Program_D_Manual.py")

    def load_encrypted_f(self):
        """【黑盒子關鍵邏輯】AES-256 解密執行"""
        if not MY_STRATEGY_KEY:
            print("⚠️ 警告: 未設定 MY_STRATEGY_KEY，嘗試讀取明碼 F 程式...")
            return self.load_module("Program_F_Strategy.py")

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
                print(f"🔑 [策略區] 解密失敗: {e}")
                return None
        else:
            return self.load_module("Program_F_Strategy.py")

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
                    requests.post(WEBHOOK_URL, data={'content': content}, files={'file': f}, timeout=25)
            else:
                requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
        except Exception as e:
            print(f"傳訊失敗: {e}")

    def run_trading_mode(self):
        """核心掃描、策略判定與 PDF 彙整"""
        print(f"⚡ [監控中] {datetime.now().strftime('%H:%M:%S')}")
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        if df_all.empty: return

        up_ratio = len(df_all[df_all['change_rate'] > 0]) / len(df_all) if len(df_all) > 0 else 0.5
        df_all['amount_rank'] = df_all['amount'].rank(ascending=False)
        targets = df_all.sort_values(by='amount', ascending=False).head(50)

        matched_list = []
        sector_count = {}

        for _, row in targets.iterrows():
            sid = row['stock_id']
            sec = row.get('industry_category', '其他')
            now_ts = time.time()
            
            if sid in self.sent_stocks and (now_ts - self.sent_stocks[sid]) < 3600: continue
            if sector_count.get(sec, 0) >= 2: continue

            tick_details = self.data_service.fetch_tick_details(sid)
            prices = [row['last_price']] * 10
            context = {"up_ratio": up_ratio, "change_rate": row['change_rate'], "market_index": market_index, "tick_details": tick_details}

            if self.mod_f:
                decision = self.mod_f.enhanced_process(prices, context)
                if decision and decision.get("action") == "BUY":
                    self.sent_stocks[sid] = now_ts
                    sector_count[sec] = sector_count.get(sec, 0) + 1
                    matched_list.append({
                        'stock_id': sid, 'open_p': row.get('open_price', 0), 'curr_p': row['last_price'],
                        'high_p': row.get('high_price', 0), 'low_p': row.get('low_price', 0),
                        'entry_p': decision.get('entry', 0), 'exit_p': decision.get('stop_loss', 0),
                        'pred_high': decision.get('pred_high', 0), 'info': decision.get('info', '')
                    })

        if matched_list:
            pdf_file = self.mod_d.enhanced_process(matched_list) if self.mod_d else None
            stock_ids = ", ".join([d['stock_id'] for d in matched_list])
            msg = f"🎯 **AI 買入訊號彙整**: {stock_ids}\n📈 市場上漲比: {up_ratio:.1%}\n📊 詳細分析見 PDF 報表。"
            self.send_to_discord(msg, pdf_file)
            if pdf_file and os.path.exists(pdf_file): os.remove(pdf_file)
        else:
            print("ℹ️ 掃描完畢，未達門檻。")

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        if 900 <= t_int <= 1330:
            # 盤中監控邏輯...
            self.run_trading_mode()
        elif 1331 <= t_int <= 1400:
            print("💾 執行盤後總結與進化分析...")
            try:
                import Program_E_Evolution as E
                E.run_evolution()
            except Exception as e:
                print(f"結算報錯: {e}")


if __name__ == "__main__":
    os.environ['TZ'] = 'Asia/Taipei'
    if hasattr(time, 'tzset'): time.tzset()
    CoreSystem().main()
    gc.collect()
