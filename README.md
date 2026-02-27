# High-Frequency Trend Breakout Strategy Driven by Multi-Factor Resonance

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🏆 **Awarded Third Prize (Rank 7/150+) in the 2025 Quantitative Trading Research Competition**, co-hosted by USTC & Fudan University, sponsored by Xinhong Tianhe Capital.

> **Note**: This repository contains the core strategy and engineering framework for our submission to the 2025 Xinhong Quantitative Trading Competition (Team: zkd047).
>
> **💡 Highlight**: For a comprehensive visual explanation of our multi-factor methodology, microstructure insights, and defense presentation, please refer to our **[Project Defense Deck (PDF)](./docs/Presentation.pdf)**.

## 📖 Overview

This project implements a robust high-frequency trading (HFT) strategy for Stock Index Futures, operating on **500ms Level-2 snapshot data**. By leveraging multi-factor resonance—integrating VWAP, rolling extremums (Donchian Channels), EMA trend filtering, dynamic ATR risk control, and Order Book Imbalance (OBI)—the strategy effectively captures high-certainty breakout opportunities in a highly noisy microstructure environment.

## ✨ Research Highlights & Innovations

* **Robust Signal Filtering**: Balances signal sensitivity and noise reduction. It utilizes a multi-layered filtering system to capture deterministic trading opportunities while shielding against random market noise and avoiding frequent, unprofitable trades.
* **Overcoming Transaction Cost Constraints**: In HFT, costs are the invisible killers. This strategy ensures that the expected profitability of each captured signal is large enough to cover the cumulative slippage and tick fees, strictly guaranteeing a positive expected value.
* **Avoiding the Overfitting Trap**: Rejects static, curve-fitted "magic numbers." Instead, it utilizes dynamic, self-adaptive parameters (e.g., dynamic ATR for Stop-Loss/Take-Profit limits) ensuring the out-of-sample validity of the financial logic.

## 📊 Data Preparation & Schema Specifications

To comply with the competition's Non-Disclosure Agreement, raw high-frequency market data is strictly prohibited from being uploaded to the repository. The program will automatically index external data cross-platform via absolute paths:
👉 **Data Read Path**: `../future_L2/test/{date}/{contract}_M.parquet`

### 1. Core Columns Utilized by the Strategy

The input `.parquet` files must contain the following essential fields required for the strategy engine's actual computations:

| Core Column                    | Data Type | Strategy Logic / Usage                                       |
| :----------------------------- | :-------- | :----------------------------------------------------------- |
| `LASTPRICE`                    | double    | Core price series; used to calculate EMA trend, EMA slope, and mark-to-market PnL. |
| `HIGHPRICE` / `LOWPRICE`       | double    | Used to calculate True Range (ATR) and identify local rolling high/low extremums. |
| `TRADEVOLUME`                  | double    | Interval volume; used to calculate the internal VWAP anchor and identify volume-confirmed breakouts. |
| `BUYVOLUME01` / `SELLVOLUME01` | double    | Level 1 Bid / Ask volume; used to compute the L1 Order Book Imbalance (OBI) indicator. |

### 2. Complete Parquet Underlying Schema Reference

<details>
<summary>👉 Click to expand the full 500ms Level-2 field list (53 columns)</summary>
SYMBOL: large_string
OPENPRICE: double
LASTPRICE: double
HIGHPRICE: double
LOWPRICE: double
SETTLEPRICE: double
PRESETTLEPRICE: double
CLOSEPRICE: double
PRECLOSEPRICE: double
TRADEVOLUME: double
TOTALVOLUME: double
TRADEAMOUNT: double
TOTALAMOUNT: double
PRETOTALPOSITION: double
TOTALPOSITION: double
PREPOSITIONCHANGE: double
PRICEUPLIMIT: double
PRICEDOWNLIMIT: double
BUYORSELL: large_string
OPENCLOSE: large_string
BUYPRICE01 - 05: double
SELLPRICE01 - 05: double
BUYVOLUME01 - 05: double
SELLVOLUME01 - 05: double
SETTLEGROUPID: large_string
SETTLEID: int64
CHANGE: double
CHANGERATIO: double
CONTINUESIGN: large_string
POSITIONCHANGE: double
AVERAGEPRICE: double
ORDERRATE: double
ORDERDIFF: double
AMPLITUDE: double
VOLRATE: double
SELLVOL: double
BUYVOL: double
TRADINGTIME: timestamp[ns] (Index)
</details>


## 📂 Project Architecture

```text
HFT-Resonance-Strategy/
├── docs/                       
│   └── Presentation.pdf        # Project defense deck & quantitative logic visual guide
├── config/
│   └── strategy_config.py      # Global parameters, slippage/fee models, and factor weights
├── core/                       # Core Algorithm Modules
│   ├── indicators.py           # Feature Engineering: VWAP, OBI, EMA, ATR
│   ├── signals.py              # Signal Synthesis: Multi-factor breakout logic
│   └── position.py             # Portfolio Management: ATR dynamic SL/TP & Time-stops
├── main.py                     # Production Entry: Multi-processing signal generation
├── backtest.py                 # Backtesting Engine: Performance evaluation metrics
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

## 🚀 Quick Start

**1. Environment Setup**

```
pip install -r requirements.txt
```

**2. Generate Trading Signals**

Run the core strategy script. The system will automatically process historical tick data via multi-processing and generate standardized daily `.csv` position arrays in the `./positions/` directory.

```
python strategy.py
```

**3. Evaluate Performance**

Run the backtest engine to calculate strategy PnL, Sharpe Ratio, and Maximum Drawdown (incorporating strict transaction costs and slippage models).

```
python backtest.py
```

## 👥 Authors

-   **Xiangzheng Xi** (School of the Gifted Young, USTC) - *Architecture Design, Core Algorithm & Engineering*
-   **Wei Wei** (School of Mathematical Sciences, USTC) - *Quantitative Rule Analysis & Logic Optimization*
