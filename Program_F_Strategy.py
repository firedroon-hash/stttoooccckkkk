def enhanced_process(prices, context=None):
    curr_p = prices[-1]
    up_ratio = context.get('up_ratio', 0.5)
    change_rate = context.get('change_rate', 0)
    market_index = context.get('market_index', {})
    
    # 這裡放真正的核心決策參數
    threshold = 2.0 if up_ratio > 0.5 else 3.5
    
    if change_rate >= threshold:
        entry = round(curr_p * 1.005, 2)
        return {
            "action": "BUY",
            "entry": entry,
            "info": f"市場轉強({change_rate:.1%})",
            "shares": int(200000 / (entry * 1000))
        }
    return {"action": "HOLD"}
