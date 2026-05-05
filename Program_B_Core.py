# ==============================================================================
# 程式名稱：Program_B_Core.py (AI 實戰中控核心 - v39.2 彙整定稿版)
# ------------------------------------------------------------------------------
# 實戰功能查核 (100% 在位)：
# 1.心跳/時間管理 2.Token認證接口 3.前50名排序 4.4/24讓價邏輯 
# 5.20萬本金精算 6.產業上限過濾 7.成本精算回本點 8.PDF專業單一報告 
# 9.去重機制(1hr) 10.黑盒子加密接口
# ==============================================================================

import os, json, time, importlib.util, gc, requests
from datetime import datetime
import Program_A_Fetcher as A

# 環境變數設定
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
# 雖然主要使用免費引擎，但保留 FinMind 接口以相容認證流程
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoia2F4bHoiLCJlbWFpbCI6ImZpcmVkcm9vbkBnbWFpbC5jb20ifQ.unKH4dRwL9qcJXB8Wlqo5bIaTQhZWxwwfW3Ym94Y4wE"

class CoreSystem:
    def __init__(self):
        print(f"[{datetime.now()}] 🚀 系統初始化 (v39.2 彙整版)")
        self.data_service = A.get_data_service(FINMIND_TOKEN)
        self.sent_stocks = {} # 格式: {'2330': timestamp}
        
        # 預加載 F (策略) 與 D (報告) 以提升效能
        self.mod_f = self.load_module("Program_F_Strategy.py") 
        self.mod_d = self.load_module("Program_D_Manual.py")

    def load_module(self, filename):
        if not os.path.exists(filename): 
            print(f"⚠️ 缺失模組: {filename}")
            return None
        spec = importlib.util.spec_from_file_location("module", filename)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def send_to_discord(self, content, file_path=None):
        if not WEBHOOK_URL: return
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    # 增加超時設定，確保大檔案上傳穩定
                    requests.post(WEBHOOK_URL, data={'content': content}, files={'file': f}, timeout=20)
            else:
                requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
        except Exception as e:
            print(f"傳訊失敗: {e}")

    def run_trading_mode(self):
        """執行掃描、AI 判斷、並將多檔訊號彙整至單一 PDF"""
        print(f"⚡ [深度掃描] {datetime.now().strftime('%H:%M:%S')}")
        
        df_all = self.data_service.fetch_market_snapshot()
        market_index = self.data_service.fetch_index_status()
        
        if df_all.empty: 
            print("⚠️ 無法獲取數據")
            return

        up_ratio = len(df_all[df_all['change_rate'] > 0]) / len(df_all) if len(df_all) > 0 else 0.5
        
        # [功能 3] 前 50 名主流股排序
        df_all['amount_rank'] = df_all['amount'].rank(ascending=False)
        targets = df_all.sort_values(by='amount', ascending=False).head(50)

        matched_list = []
        sector_count = {} # [功能 6] 產業上限

        for _, row in targets.iterrows():
            sid = row['stock_id']
            sec = row.get('industry_category', '其他')
            now_ts = time.time()
            
            # [功能 9] 一小時去重過濾
            if sid in self.sent_stocks and (now_ts - self.sent_stocks[sid]) < 3600:
                continue
            
            # [功能 6] 產業上限 (同一產業單次最多 2 檔)
            if sector_count.get(sec, 0) >= 2:
                continue

            # 準備 AI 分析環境 (包含 A 程式模擬的 Tick 與大盤數據)
            tick_details = self.data_service.fetch_tick_details(sid)
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
                    sector_count[sec] = sector_count.get(sec, 0) + 1
                    
                    # 彙整數據 (補齊開盤、現價、建議價、預判價等所有 D 所需欄位)
                    matched_list.append({
                        'stock_id': sid,
                        'open_p': row.get('open_price', 0),
                        'curr_p': row['last_price'],
                        'high_p': row.get('high_price', 0),
                        'low_p': row.get('low_price', 0),
                        'entry_p': decision.get('entry', 0),
                        'exit_p': decision.get('stop_loss', 0),
                        'pred_high': decision.get('pred_high', 0),
                        'info': decision.get('info', '')
                    })

        # [功能 8] 產出彙整報告
        if matched_list:
            print(f"🎯 發現 {len(matched_list)} 檔符合標的，產出彙整報告...")
            pdf_file = None
            if self.mod_d:
                # 調用 D 程序產出單一 PDF
                pdf_file = self.mod_d.enhanced_process(matched_list)
            
            stock_ids = ", ".join([d['stock_id'] for d in matched_list])
            msg = f"🎯 **AI 買入訊號彙整**: {stock_ids}\n📈 市場上漲比: {up_ratio:.1%}\n📊 詳細分析與落差分析請見下方專業 PDF 報表。"
            
            self.send_to_discord(msg, pdf_file)
            
            # 清理檔案
            if pdf_file and os.path.exists(pdf_file): os.remove(pdf_file)
        else:
            print("ℹ️ 掃描完畢，未達進場門檻。")

    def main(self):
        t_int = int(datetime.now().strftime("%H%M"))
        # 設定執行時間 09:00 - 14:00
        if 900 <= t_int <= 1400:
            print(f"⏰ 進入監控時段 ({t_int})")
            # 每一輪 GitHub 觸發跑 2 次掃描，間隔 60 秒
            for i in range(2):
                self.run_trading_mode()
                if i == 0: time.sleep(60)
        else:
            self.send_to_discord(f"🌙 系統待命回報 (時間: {t_int})")

if __name__ == "__main__":
    os.environ['TZ'] = 'Asia/Taipei'
    if hasattr(time, 'tzset'): time.tzset()
    CoreSystem().main()
    gc.collect()
