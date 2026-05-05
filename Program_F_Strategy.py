def enhanced_process(prices, context=None):
    # 強制回傳 BUY，測試 Discord 與 PDF
    return {
        "action": "BUY",
        "entry": prices[-1],
        "stop_loss": prices[-1] * 0.97,
        "pred_high": prices[-1] * 1.05,
        "info": "測試發送中"
    }
