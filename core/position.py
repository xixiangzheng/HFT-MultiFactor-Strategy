import pandas as pd
import numpy as np

def manage_position_logic(data, params):
    """
    仓位管理模块。
    实现带追踪止损的 ATR 动态管理及时间平仓机制。
    """
    stop_loss_mult, take_profit_mult, time_stop = params['stop_loss_mult'], params['take_profit_mult'], params['time_stop']
    close_col = params['close_col']

    # 6. Position management with trailing ATR stop (带追踪止损的仓位管理)
    # 逐点迭代进行决策，实现开仓、止损、止盈和时间止损逻辑。
    pos = np.zeros(len(data), dtype=np.int8)
    current_pos, entry_price, entry_idx = 0, 0.0, -1
    peak, trough = 0.0, 0.0  # 用于追踪多头和空头持仓期间的最高价/最低价

    for i in range(len(data)):
        price = data[close_col].iloc[i]
        atr_val = data["atr"].iloc[i]

        # 确保所有用于决策的指标在当前点都是有效的
        if not all(np.isfinite([price, atr_val, data["rolling_high"].iloc[i], data["rolling_low"].iloc[i],
                                data["vol_ma"].iloc[i], data["ema"].iloc[i], data["ema_slope"].iloc[i],
                                data["vwap"].iloc[i], data["obi"].iloc[i]])):
            pos[i] = current_pos
            continue

        if current_pos == 0:  # 空仓状态：寻找开仓机会
            if data["break_high"].iat[i]:  # 满足做多突破条件
                current_pos = 1
                entry_price, entry_idx, peak = price, i, price
            elif data["break_low"].iat[i]:  # 满足做空突破条件
                current_pos = -1
                entry_price, entry_idx, trough = price, i, price

        elif current_pos == 1:  # 持有多仓状态：管理止损止盈
            peak = max(peak, price)  # 更新追踪高点
            # 止损价：取 (入场价 - SL_MULT * ATR) 和 (追踪高点 - SL_MULT * ATR) 中的较大值
            sl = max(entry_price - stop_loss_mult * atr_val, peak - stop_loss_mult * atr_val)
            tp = entry_price + take_profit_mult * atr_val  # 止盈价

            # 平仓条件：价格跌破止损线 或 价格触及止盈线 或 达到最大持仓时间
            if price <= sl or price >= tp or (i - entry_idx >= time_stop):
                current_pos = 0

        elif current_pos == -1:  # 持有空仓状态：管理止损止盈
            trough = min(trough, price)  # 更新追踪低点
            # 止损价：取 (入场价 + SL_MULT * ATR) 和 (追踪低点 - SL_MULT * ATR) 中的较小值
            sl = min(entry_price + stop_loss_mult * atr_val, trough + stop_loss_mult * atr_val)
            tp = entry_price - take_profit_mult * atr_val  # 止盈价

            # 平仓条件：价格涨过止损线 或 价格触及止盈线 或 达到最大持仓时间
            if price >= sl or price <= tp or (i - entry_idx >= time_stop):
                current_pos = 0

        pos[i] = current_pos  # 记录当前 bar 的仓位

    # 对生成的仓位序列进行前向填充，处理可能因数据缺失导致的NaN，并确保最终没有NaN值
    # 这保证了仓位在没有明确变化信号时保持不变。
    return pd.Series(pos, index=data.index, name="position").ffill().fillna(0)