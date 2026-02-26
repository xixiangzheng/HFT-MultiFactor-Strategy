import pandas as pd
import numpy as np
import os
import time
import warnings
warnings.filterwarnings('ignore')

from config.strategy_config import STRATEGY_PARAMS
from core.indicators import compute_all_indicators
from core.signals import generate_resonance_signals
from core.position import manage_position_logic

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
test_dir = os.path.abspath(os.path.join(BASE_DIR, '..', 'future_L2', 'test'))
pred_dir = os.path.abspath(os.path.join(BASE_DIR, 'positions'))

def generate_signals(
        df: pd.DataFrame,
) -> pd.Series:
    """
    交易信号生成函数，旨在通过强化趋势确认和参数微调尽可能提高夏普比率。

    核心逻辑：
    1. 计算VWAP。
    2. 计算滚动极值和成交量均值。
    3. 计算EMA趋势过滤，并增加EMA斜率确认。
    4. 计算ATR用于风险管理。
    5. 可选的盘口不均衡（OBI）过滤。
    6. 突破条件：结合价格、成交量、EMA趋势（含斜率）和OBI。
    7. 仓位管理：带追踪止损的ATR动态止损止盈和时间止损。

    Parameters
    ----------
    df : pd.DataFrame
        高频市场数据，包含价格、成交量、买卖盘数据。
    window : int
        用于计算滚动高点/低点和成交量均值的窗口大小。
    ema_period : int
        用于计算EMA趋势过滤的周期。
    atr_period : int
        用于计算ATR的周期。
    vol_multiplier : float
        突破发生时，当前成交量相对于平均成交量的乘数要求。
    obi_threshold : float
        盘口不均衡（OBI）的绝对值阈值。
    use_obi : bool
        是否使用盘口不均衡作为过滤条件。
    stop_loss_mult : float
        止损水平是入场价格偏离ATR的倍数。
    take_profit_mult : float
        止盈水平是入场价格偏离ATR的倍数。
    time_stop : int
        最大持仓bar数，超过此时间则平仓。
    bid_col, ask_col, high_col, low_col, close_col, vol_col : str
        数据框中相应列的名称。

    Returns
    -------
    pd.Series
        与df对齐的仓位序列 (1 = 多头, -1 = 空头, 0 = 平仓)。
    """

    # 指标计算
    data = compute_all_indicators(df, STRATEGY_PARAMS)
    # 信号合成
    data["break_high"], data["break_low"] = generate_resonance_signals(data, STRATEGY_PARAMS)
    # 仓位管理
    return manage_position_logic(data, STRATEGY_PARAMS)


def pred(date):
    print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} start to pred {date}')
    Mfiles = os.listdir(f'{test_dir}/{date}')
    Mfiles = [f for f in Mfiles if '_M' in f]

    result_dict = {}

    for f in Mfiles:
        df = pd.read_parquet(f'{test_dir}/{date}/{f}')
        result = generate_signals(df)
        result_dict[f.split('.')[0]] = result

    os.makedirs(f'{pred_dir}/{date}', exist_ok=True)
    for code, result in result_dict.items():
        result.to_csv(f'{pred_dir}/{date}/{code}.csv')

if __name__ == '__main__':
    test_dates = sorted(os.listdir(test_dir))[1:]
    os.makedirs(pred_dir, exist_ok=True)

    from multiprocessing import Pool
    with Pool(20) as p:
        p.map(pred, test_dates)
