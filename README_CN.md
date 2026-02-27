# 多因子共振驱动的高频趋势突破策略

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

🏆 **荣获 2025 年信弘量化交易大赛全国三等奖 (排名 7/150+)**，由中国科学技术大学与复旦大学联合主办，信弘天禾资产赞助。

> **项目说明**：本项目为 2025 信弘量化交易大赛（团队 zkd047）核心策略的工程化重构版本。
>
> **💡 核心推荐**：强烈建议查阅我们的 **[【项目答辩 PPT】](./docs/Presentation.pdf)**，内含详尽的策略逻辑图解、微观结构分析及难点攻克过程。

## 📖 项目简介

本项目实现了一个针对股指期货的高效高频交易（HFT）系统，基于 **500ms 级别的 Level-2 快照数据**运行。策略深度融合了多因子共振逻辑——结合 VWAP 均值回归、滚动极值（唐奇安通道）、EMA 趋势过滤、ATR 动态风控以及盘口不均衡指标（OBI），旨在找到捕捉确定性机会与屏蔽市场随机噪声之间的最佳平衡点。

## ✨ 核心亮点与难点攻克

* **鲁棒的信号过滤**：构建了多层过滤系统。解决了过滤条件过严导致错过行情，过松导致产生大量假信号频繁交易的痛点，敏锐捕捉高确定性突破。
* **突破交易成本的桎梏**：在高频领域，成本是决定策略生死的隐形杀手。本策略确保单笔捕捉的突破预期收益空间足够大，足以覆盖数个 Tick 的滑点与手续费成本。
* **规避过拟合的陷阱**：拒绝雕刻历史噪声。策略抛弃了高度优化的静态“魔法数字”，转而采用动态自适应参数（如基于 ATR 动态计算止盈止损），确保模型在未来及样本外的有效性。

## 📊 数据准备与格式规范

为遵守赛事保密协议，原始高频行情数据严禁上传至代码仓库。程序将通过绝对路径自动跨平台索引外部数据：
👉 **数据读取路径**: `../future_L2/test/{date}/{contract}_M.parquet`

### 1. 策略实际调用的核心字段
输入的 `.parquet` 文件必须包含以下策略引擎实际运算所需的字段：

| 核心字段                       | 数据类型 | 策略逻辑用途                                           |
| :----------------------------- | :------- | :----------------------------------------------------- |
| `LASTPRICE`                    | double   | 核心价格序列，用于计算 EMA 趋势、斜率以及盯市逻辑。    |
| `HIGHPRICE` / `LOWPRICE`       | double   | 用于计算真实波幅 (ATR) 及识别局部滚动高低点极值。      |
| `TRADEVOLUME`                  | double   | 区间成交量，用于计算策略内部 VWAP 锚点及识别放量突破。 |
| `BUYVOLUME01` / `SELLVOLUME01` | double   | 买 / 卖一档挂单量，用于计算 L1 盘口不均衡指标 (OBI)。  |

### 2. 完整 Parquet 底层 Schema 参考
<details>
<summary>👉 点击展开查看底层 500ms Level-2 完整字段列表 (53列)</summary> 
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

## 📂 系统架构

```text
HFT-Resonance-Strategy/
├── docs/                       
│   └── Presentation.pdf        # 项目答辩与策略逻辑图解 PPT
├── config/
│   └── strategy_config.py      # 策略全局参数（滑点、手续费、因子权重及阈值配置）
├── core/                       # 核心算法模块
│   ├── indicators.py           # 因子工程：VWAP, OBI, EMA, ATR
│   ├── signals.py              # 信号合成：多因子共振突破逻辑
│   └── position.py             # 仓位管理：ATR 动态止盈止损与超时平仓
├── main.py                     # 生产入口：多进程并发执行，生成逐日目标仓位
├── backtest.py                 # 回测引擎：模拟撮合与绩效测算
├── requirements.txt            # 环境依赖配置
└── README.md                   # 项目文档
```

## 🚀 运行指南

**1. 环境配置**

```
pip install -r requirements.txt
```

**2. 并发生成仓位信号**

在终端运行策略脚本。系统将自动前往 `../future_L2/test/` 目录下读取数据，启动多进程池加速计算，并将生成的 `[-1, 0, 1]` 仓位序列保存至 `./positions/` 文件夹。

```
python strategy.py
```

**3. 运行回测与绩效测算**

运行回测引擎。系统将读取生成的仓位序列与真实行情，在严格扣除滑点与手续费后，计算策略的年化收益率、夏普比率及最大回撤等核心指标。

```
python backtest.py
```

## 👥 团队成员

-   **奚项正** (中国科学技术大学，少年班学院) - *系统架构设计、核心算法实现与工程化重构*
-   **魏薇** (中国科学技术大学，数学科学学院) - *赛制规则解析、参数分析与策略逻辑优化*