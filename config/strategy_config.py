# config/strategy_config.py
STRATEGY_PARAMS = {
    "window": 7200,
    "ema_period": 1200,
    "atr_period": 240,
    "vol_multiplier": 1.8,
    "obi_threshold": 0.15,
    "use_obi": True,
    "stop_loss_mult": 1.2,
    "take_profit_mult": 3.5,
    "time_stop": 21600,
    "bid_col": "BUYVOLUME01",
    "ask_col": "SELLVOLUME01",
    "high_col": "HIGHPRICE",
    "low_col": "LOWPRICE",
    "close_col": "LASTPRICE",
    "vol_col": "TRADEVOLUME",
}