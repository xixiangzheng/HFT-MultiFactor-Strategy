from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Configuration constants
# -----------------------------------------------------------------------------
FEE_RATE: float = 0.000023  # symmetric taker fee
BASE_DIR = Path(__file__).resolve().parent
TEST_DIR = (BASE_DIR / ".." / "future_L2" / "test").resolve()
SIG_DIR = (BASE_DIR / "positions").resolve()
BACKTEST_RESULT_DIR = (BASE_DIR / "backtest").resolve()

# -----------------------------------------------------------------------------
# Core back‑test routine
# -----------------------------------------------------------------------------

def backtest(date: str, m_ind: str) -> pd.DataFrame:
    """Run a single‑contract intraday back‑test.

    Parameters
    ----------
    date : str
        Trading date directory under ``TEST_DIR`` (e.g. ``"20250102"``).
    m_ind : str
        Contract file stem including version suffix (e.g. ``"RB2405_M"``).

    Returns
    -------
    pd.DataFrame
        Trade blotter with price, PnL, and cumulative return columns.  An empty
        DataFrame with the correct columns is returned if any exception occurs.
    """

    try:
        # ------------------------------------------------------------------
        # Market quotes (best bid/ask) & raw signal positions
        # ------------------------------------------------------------------
        market_path = TEST_DIR / date / f"{m_ind}.parquet"
        market = pd.read_parquet(market_path, columns=["BUYPRICE01", "SELLPRICE01"])

        pos_path = SIG_DIR / date / f"{m_ind}.csv"
        positions = pd.read_csv(pos_path)

        positions["TRADINGTIME"] = pd.to_datetime(positions["TRADINGTIME"])
        positions.set_index("TRADINGTIME", inplace=True)

        # Sanity‑check: position must be ‑1 / 0 / 1
        assert positions["position"].isin([0, 1, -1]).all(), "仓位异常"

        # Force flat at both the first bar on file and the last two bars
        positions.iloc[0] = 0
        positions.iloc[-2:] = 0

        if positions["position"].abs().sum() == 0:
            return pd.DataFrame(columns=[
                "time_o", "action_o", "price_o",
                "time_c", "action_c", "price_c",
                "sign", "pnl", "fee", "net_pnl", "return", "cum_return"])
    
        # Align with market timestamps (right‑join + forward‑fill)
        df = positions.join(market, how="right").ffill()
        time_idx = list(df.index)

        # ------------------------------------------------------------------
        # Detect transitions & construct trade list
        # ------------------------------------------------------------------
        df["preposition"] = df["position"].shift(1)
        df["position_diff"] = df["position"].diff().fillna(0)
        change_points = df[df["position_diff"] != 0].index

        transactions: List[tuple] = []
        for idx in change_points:
            next_idx = time_idx[time_idx.index(idx) + 1]  # use next tick price

            prev_pos = df.loc[idx, "preposition"]
            curr_pos = df.loc[idx, "position"]
            buy_price = df.loc[next_idx, "BUYPRICE01"]
            sell_price = df.loc[next_idx, "SELLPRICE01"]

            # Six possible state transitions
            # BTO: 买入开仓
            # BTC: 买入平仓
            # STO: 卖出开仓
            # STC: 卖出平仓
            if (prev_pos, curr_pos) == (0, 1):
                transactions.append((idx, "BTO", sell_price))
            elif (prev_pos, curr_pos) == (1, 0):
                transactions.append((idx, "BTC", buy_price))
            elif (prev_pos, curr_pos) == (0, -1):
                transactions.append((idx, "STO", buy_price))
            elif (prev_pos, curr_pos) == (-1, 0):
                transactions.append((idx, "STC", sell_price))
            elif (prev_pos, curr_pos) == (1, -1):
                transactions.extend([(idx, "BTC", buy_price), (idx, "STO", buy_price)])
            elif (prev_pos, curr_pos) == (-1, 1):
                transactions.extend([(idx, "STC", sell_price), (idx, "BTO", sell_price)])

        # ------------------------------------------------------------------
        # Assemble trade DataFrame
        # ------------------------------------------------------------------
        trades = pd.concat([
            pd.DataFrame(transactions[::2]),
            pd.DataFrame(transactions[1::2])
        ], axis=1)
        trades.columns = [
            "time_o", "action_o", "price_o",
            "time_c", "action_c", "price_c",
        ]
        trades["sign"] = np.where(trades["action_o"] == "BTO", 1, -1)
        trades["pnl"] = (trades["price_c"] - trades["price_o"]) * trades["sign"]
        trades["fee"] = trades["price_o"] * FEE_RATE + trades["price_c"] * FEE_RATE
        trades["net_pnl"] = trades["pnl"] - trades["fee"]
        trades["return"] = trades["net_pnl"] / trades["price_o"]
        trades["cum_return"] = trades["return"].cumsum()
        return trades

    except Exception as exc:  # noqa: BLE001
        # Return empty frame with the correct columns on failure
        cols = [
            "time_o", "action_o", "price_o",
            "time_c", "action_c", "price_c",
            "sign", "pnl", "fee", "net_pnl", "return", "cum_return",
        ]
        print(f"Error backtesting {date}-{m_ind}: {exc}")
        return pd.DataFrame(columns=cols)

# -----------------------------------------------------------------------------
# Batch runner
# -----------------------------------------------------------------------------

def main() -> None:  
    """Batch‑run the back‑test across all dates and main contracts."""
    # Clean output directory
    if BACKTEST_RESULT_DIR.exists():
        shutil.rmtree(BACKTEST_RESULT_DIR)
    BACKTEST_RESULT_DIR.mkdir(parents=True, exist_ok=True)

    # Skip index [0] because of hidden/system entries in some file systems
    test_dates = sorted(p.name for p in TEST_DIR.iterdir() if p.is_dir())[1:]

    all_rets: List[Dict[str, float]] = []
    for date in test_dates:
        daily_rets: Dict[str, float] = {}
        (BACKTEST_RESULT_DIR / date).mkdir(parents=True, exist_ok=True)

        m_files = [p.name for p in (TEST_DIR / date).iterdir() if "_M" in p.name]
        assert len(m_files) == 4, f"{date} 没有主力合约"

        for m_file in m_files:
            m_ind = m_file.split(".")[0]
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"{timestamp} start to backtest {date} {m_ind}")

            trades = backtest(date, m_ind)
            trades.to_csv(BACKTEST_RESULT_DIR / date / f"{m_ind}.csv", index=False)

            daily_rets[m_ind.split("_")[0]] = trades["return"].sum()

        all_rets.append(daily_rets)

    # Aggregate & persist results
    all_rets_df = pd.DataFrame(all_rets)
    all_rets_df.index = test_dates
    all_rets_df["mean"] = all_rets_df.mean(axis=1)

    all_rets_df.to_csv(BACKTEST_RESULT_DIR / "all_rets.csv")

    ## 年化收益率
    annual_ret = all_rets_df['mean'].mean() * 252
    sharpe = all_rets_df["mean"].mean() / all_rets_df['mean'].std() * np.sqrt(252)
    all_rets_df.to_csv(BACKTEST_RESULT_DIR / "all_rets.csv")
    

    print(all_rets_df)
    print('\n')
    print('Backtest Result:')
    print(f'annual_ret: {annual_ret}')
    print(f'sharpe: {sharpe}')


if __name__ == "__main__":
    main()
