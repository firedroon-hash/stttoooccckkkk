def enhanced_process(prices, context=None):
    curr_p = prices[-1]
    up_ratio = context.get('up_ratio', 0.5)
    change_rate = context.get('change_rate', 0)
    market_index = context.get('market_index', {})
    tick = context.get('tick_details', [])
    
    # 邏輯 1: 門檻
    threshold = 2.5 if up_ratio > 0.4 else 3.5
    # 邏輯 2: 大盤攔截
    if market_index and market_index.get('change_rate', 0) < -0.7: return {"action": "HOLD"}
    # 邏輯 3: 外盤偵測
    out_ratio = len(tick[tick['tick_type']==1])/len(tick) if len(tick)>0 else 0.5
    
    if change_rate >= threshold and out_ratio >= 0.5:
        entry = round(curr_p * 1.005, 2)
        return {"action": "BUY", "entry": entry, "shares": int(200000/(entry*1000)), "info": f"強勢(外盤:{out_ratio:.1%})"}
    return {"action": "HOLD"}
