import pandas as pd
import numpy as np

def compute_all_indicators(df, params):
    """
    指标计算模块。
    负责计算 VWAP, Rolling Extrema, EMA Trend, ATR 以及 OBI。
    """
    window, ema_period, atr_period = params['window'], params['ema_period'], params['atr_period']
    use_obi, close_col, vol_col = params['use_obi'], params['close_col'], params['vol_col']
    high_col, low_col, bid_col, ask_col = params['high_col'], params['low_col'], params['bid_col'], params['ask_col']

    data = df.copy()

    # 确保关键列存在，如果不存在则填充NaN并发出警告
    required_cols = [high_col, low_col, close_col, vol_col]
    if use_obi:
        required_cols.extend([bid_col, ask_col])
    for col in required_cols:
        if col not in data.columns:
            print(f"Warning: Missing required column '{col}'. Filling with NaN. This may affect strategy performance.")
            data[col] = np.nan

    # ─────────────────────────────
    # 0. VWAP (全局成交量加权均价)
    # VWAP作为市场平均成本的参考，有助于确认突破的有效性。
    cum_vol = data[vol_col].cumsum().replace(0, np.nan)
    data["vwap"] = (data[close_col] * data[vol_col]).cumsum() / (cum_vol + 1e-12)  # 避免除以0

    # 1. Rolling extrema & volume reference (滚动极值和成交量参考)
    # 识别突破点和量能基准。
    data["rolling_high"] = data[high_col].shift(1).rolling(window).max()
    data["rolling_low"] = data[low_col].shift(1).rolling(window).min()
    data["vol_ma"] = data[vol_col].rolling(window).mean()

    # 2. Trend filter (EMA) & EMA Slope (趋势过滤 - 指数移动平均线及斜率)
    # EMA用于判断趋势方向，EMA斜率进一步确认趋势的强度和方向，减少假信号。
    data["ema"] = data[close_col].ewm(span=ema_period, adjust=False).mean()
    data["ema_slope"] = data["ema"].diff().fillna(0)  # 计算EMA的斜率

    # 3. ATR (平均真实波幅)
    # ATR用于动态设置止损止盈水平，适应市场波动。
    high, low, close = data[high_col], data[low_col], data[close_col]
    true_range = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    data["atr"] = true_range.rolling(atr_period).mean().bfill().fillna(0)  # 填充初始NaN

    # 4. Order-book imbalance (optional) (盘口不均衡 - 可选过滤条件)
    # OBI提供微观市场买卖压力信息，辅助判断突破的真实性。
    if use_obi:
        data["obi"] = (data[bid_col] - data[ask_col]) / (
                data[bid_col] + data[ask_col] + 1e-12
        )
        data["obi"].fillna(0.0, inplace=True)  # 填充NaN
    else:
        data["obi"] = 0.0  # dummy

    return data