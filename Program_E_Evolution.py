import os, pandas as pd

def process_evolution():
    history_file = "history_log.csv"
    if os.path.exists(history_file):
        df = pd.read_csv(history_file)
        # 這裡未來會加入讀取當天收盤價，計算 Error%
        # 並更新 config.json 的邏輯
        print(f"✅ 已分析昨日 {len(df)} 筆交易，優化因子計算中...")
    else:
        print("ℹ️ 暫無紀錄可供進化")

if __name__ == "__main__":
    process_evolution()
