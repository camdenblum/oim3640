# Agentic Stock Trading Bot

An autonomous, modular Python stock trading bot that fetches data via **yfinance**, generates signals using technical indicators and a learned scoring model, manages a portfolio with strict risk controls, and continuously improves through an offline/online learning loop.

---

## Table of Contents
1. [Architecture](#architecture)
2. [Quickstart](#quickstart)
3. [Configuration](#configuration)
4. [Running Modes](#running-modes)
5. [Backtesting](#backtesting)
6. [Broker Setup (Alpaca)](#broker-setup)
7. [Safety Notes](#safety-notes)
8. [Module Overview](#module-overview)
9. [Testing](#testing)

---

## Architecture

```
Agentic_Trading_Bot/
├── data/
│   ├── fetcher.py        # yfinance data fetching & caching
│   └── features.py       # technical indicator feature engineering
├── models/
│   ├── strategy.py       # scoring engine & signal generation
│   └── learner.py        # model training & persistence
├── execution/
│   ├── broker_api.py     # abstract broker interface
│   ├── broker_alpaca.py  # Alpaca concrete adapter
│   └── executor.py       # order lifecycle management
├── risk/
│   └── risk.py           # risk rules, circuit breakers, stop-loss
├── portfolio/
│   └── portfolio.py      # holdings, cash, P&L, rebalancing
├── state/
│   └── trader_state.py   # SQLite persistence, trade logs, metrics
├── learning/
│   ├── learning_loop.py  # offline + online learning orchestration
│   └── reward.py         # risk-adjusted reward / fitness functions
├── backtest/
│   └── backtester.py     # walk-forward backtesting engine
├── tests/
│   └── test_*.py         # unit & integration tests
├── main.py               # CLI entry point
├── utils.py              # logging, config loader, helpers
├── config.yaml           # all tuneable parameters
└── requirements.txt
```

---

## Quickstart

### 1. Install dependencies

```bash
cd Agentic_Trading_Bot
pip install -r requirements.txt
```

### 2. Configure

Edit `config.yaml` — or just run as-is with the safe defaults (paper trading, 3 tickers, daily data).

### 3. Run in paper-trading mode

```bash
python main.py --mode paper
```

### 4. Run a backtest

```bash
python main.py --mode backtest
```

### 5. Enable learning

Set `learning.enable_learning: true` in `config.yaml`, then re-run.

---

## Configuration

All parameters live in `config.yaml`. Key sections:

| Section | Purpose |
|---------|---------|
| `mode` | `paper` (default) or `live` |
| `data` | Tickers, lookback window, granularity |
| `features` | Which indicators to compute and their params |
| `strategy` | Scoring model type, buy/sell thresholds |
| `learning` | Enable/disable learning, learning rate, epochs |
| `risk` | Drawdown limits, position limits, stop-loss |
| `execution` | Broker adapter, order type, retries |
| `portfolio` | Initial cash, currency |
| `backtest` | Date range, walk-forward settings |
| `observability` | Log level, log format, export paths |
| `compliance` | Approval gates, audit logging |

---

## Running Modes

### Paper Trading (default)
Simulates order fills without real money. Safe for strategy development.

```bash
python main.py --mode paper
```

### Live Trading
**Read the safety notes first.** Requires valid broker credentials.

```bash
python main.py --mode live
```

### Backtesting
Replays historical data through the same strategy pipeline.

```bash
python main.py --mode backtest --start 2022-01-01 --end 2024-12-31
```

### Single Ticker Backtest
```bash
python main.py --mode backtest --tickers AAPL,MSFT
```

---

## Broker Setup (Alpaca)

1. Create a free account at [alpaca.markets](https://alpaca.markets).
2. Generate API keys in the Alpaca dashboard.
3. Set environment variables (never put secrets in `config.yaml`):

```bash
export ALPACA_API_KEY="your_key_here"
export ALPACA_SECRET_KEY="your_secret_here"
export ALPACA_BASE_URL="https://paper-api.alpaca.markets"   # paper
# export ALPACA_BASE_URL="https://api.alpaca.markets"       # live
```

Or create a `.env` file (add it to `.gitignore`!):

```
ALPACA_API_KEY=your_key_here
ALPACA_SECRET_KEY=your_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

To use a different broker, implement `execution/broker_api.py`'s `BrokerBase` abstract class and point `execution.broker_module` to your new file.

---

## Safety Notes

> **Start with paper trading.** The default config uses `mode: paper`. Do not flip to `live` without:
> - Testing thoroughly in paper mode for at least 2–4 weeks
> - Understanding the risk parameters and what each circuit breaker does
> - Verifying your broker account has the right permissions
> - Reviewing relevant regulations (PDT rule, Reg T margin, etc.) for your jurisdiction

**Circuit breakers built in:**
- Max total drawdown: halt if portfolio drops more than `risk.max_total_drawdown_pct` from peak
- Max daily loss: halt for the rest of the day if losses exceed `risk.max_daily_loss_pct`
- Per-position stop-loss / take-profit
- Max concurrent positions cap
- Minimum cash reserve

If any unhandled exception occurs in live mode, the bot fails safe into paper mode and alerts via logs.

---

## Module Overview

### `data/fetcher.py`
Downloads OHLCV data from yfinance with local disk caching and retry/backoff. Returns clean `pandas.DataFrame` objects.

### `data/features.py`
Computes RSI, MACD, Bollinger Bands, EMA cross, ATR, Stochastic, Momentum, and Rate-of-Change. Normalises features and handles NaNs.

### `models/strategy.py`
Scores each asset using a configurable model (linear weights, random forest, or neural net). Returns `Signal` objects with action (BUY/SELL/HOLD) and confidence score.

### `models/learner.py`
Trains and persists the scoring model. Supports offline batch training on trade history and incremental online updates.

### `execution/broker_api.py`
Abstract `BrokerBase` with `place_order`, `cancel_order`, `get_position`, etc. Swap brokers by implementing this interface.

### `execution/executor.py`
Manages the full order lifecycle: pre-trade risk check → order placement → fill confirmation → position update → post-trade logging.

### `risk/risk.py`
Enforces all risk rules. Returns `RiskDecision` (ALLOW / BLOCK) with reason. Called before every order placement.

### `portfolio/portfolio.py`
Tracks cash, holdings, unrealised/realised P&L. Computes Sharpe ratio, max drawdown, and win rate on demand.

### `state/trader_state.py`
SQLite-backed persistence for trade history, model checkpoints, and daily performance snapshots.

### `learning/learning_loop.py`
Orchestrates offline learning (batch re-train from trade logs) and online learning (incremental update after every N trades). Reverts if validation performance degrades.

### `backtest/backtester.py`
Event-driven backtester replaying bar-by-bar data. Reports return, Sharpe, max drawdown, win rate, and compares against buy-and-hold / MA crossover baselines.

---

## Testing

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

Individual modules:
```bash
pytest tests/test_data.py -v
pytest tests/test_risk.py -v
pytest tests/test_portfolio.py -v
```
