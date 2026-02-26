import pandas as pd
import numpy as np

def generate_resonance_signals(data, params):
    """
    信号合成模块。
    基于价格突破、量能放大、趋势斜率及盘口压力进行共振判断。
    """
    vol_multiplier, obi_threshold, use_obi = params['vol_multiplier'], params['obi_threshold'], params['use_obi']
    close_col, vol_col = params['close_col'], params['vol_col']

    close = data[close_col]

    # 5. Breakout conditions (突破条件)
    # 综合价格、成交量、VWAP、EMA趋势和OBI，增加EMA斜率确认，提高信号质量。
    # 趋势确认：价格在EMA之上且EMA向上倾斜（做多），或价格在EMA之下且EMA向下倾斜（做空）。
    cond_long = (
            (close > data["rolling_high"]) &  # 价格突破前期高点
            (data[vol_col] > vol_multiplier * data["vol_ma"]) &  # 成交量放大
            (close > data["ema"]) &  # 价格在EMA之上
            (data["ema_slope"] > 0) &  # EMA向上倾斜，确认上升趋势
            (close > data["vwap"]) &  # 价格在VWAP之上
            (~use_obi | (data["obi"] > obi_threshold))  # OBI过滤（如果启用）
    )

    cond_short = (
            (close < data["rolling_low"]) &  # 价格跌破前期低点
            (data[vol_col] > vol_multiplier * data["vol_ma"]) &  # 成交量放大
            (close < data["ema"]) &  # 价格在EMA之下
            (data["ema_slope"] < 0) &  # EMA向下倾斜，确认下降趋势
            (close < data["vwap"]) &  # 价格在VWAP之下
            (~use_obi | (data["obi"] < -obi_threshold))  # OBI过滤（如果启用）
    )

    return cond_long, cond_short