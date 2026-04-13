"""
backtest/backtester.py — Event-driven historical backtesting engine.

Replays bar-by-bar OHLCV data through the same strategy and learning
pipeline used in live trading, ensuring consistency between backtest and
live performance.

Metrics reported:
  - Total return, annualised return
  - Sharpe ratio, Sortino ratio
  - Max drawdown
  - Win rate, average trade P&L
  - Buy-and-hold and MA-crossover baselines for comparison
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from data.features import FeatureEngineer
from models.strategy import Strategy, Action
from portfolio.portfolio import Portfolio
from risk.risk import RiskManager

logger = logging.getLogger(__name__)

_PERIODS_PER_YEAR = 252  # trading days


@dataclass
class BacktestResult:
    """Aggregated metrics from a completed backtest run."""
    strategy_name: str
    total_return_pct: float
    annualised_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_trades: int
    avg_trade_pnl: float
    avg_holding_periods: float
    equity_curve: List[float] = field(default_factory=list)
    trade_log: List[Dict[str, Any]] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"[{self.strategy_name}] "
            f"Return: {self.total_return_pct:.1f}%  "
            f"Ann: {self.annualised_return_pct:.1f}%  "
            f"Sharpe: {self.sharpe_ratio:.2f}  "
            f"MaxDD: {self.max_drawdown_pct:.1f}%  "
            f"WinRate: {self.win_rate_pct:.1f}%  "
            f"Trades: {self.total_trades}"
        )


class Backtester:
    """Event-driven backtester.

    Args:
        strategy: Strategy instance (will use its current model weights).
        feature_engineer: FeatureEngineer for computing features bar-by-bar.
        risk_manager: RiskManager for pre-trade checks.
        initial_cash: Starting portfolio cash.
        slippage_pct: Round-trip slippage per trade.
        commission: Commission per trade in dollars.
        max_positions: Maximum concurrent holdings.
    """

    def __init__(
        self,
        strategy: Strategy,
        feature_engineer: FeatureEngineer,
        risk_manager: RiskManager,
        initial_cash: float = 100_000.0,
        slippage_pct: float = 0.001,
        commission: float = 0.0,
        max_positions: int = 8,
    ) -> None:
        self.strategy = strategy
        self.feature_engineer = feature_engineer
        self.risk_manager = risk_manager
        self.initial_cash = initial_cash
        self.slippage_pct = slippage_pct
        self.commission = commission
        self.max_positions = max_positions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        price_dict: Dict[str, pd.DataFrame],
        benchmark_ticker: str = "SPY",
    ) -> Dict[str, BacktestResult]:
        """Run the backtest and return results for strategy + baselines.

        Args:
            price_dict: {ticker: OHLCV_DataFrame} from DataFetcher.
            benchmark_ticker: Ticker to use as a buy-and-hold benchmark.

        Returns:
            Dict of strategy_name → BacktestResult.
        """
        # Pre-compute features for all tickers
        feature_dict = {
            ticker: self.feature_engineer.compute(df)
            for ticker, df in price_dict.items()
        }

        # Find common date range
        common_dates = self._common_dates(feature_dict)
        if len(common_dates) < 10:
            logger.warning("Too few common dates for backtest", extra={"n": len(common_dates)})
            return {}

        logger.info(
            "Running backtest",
            extra={"bars": len(common_dates), "tickers": list(price_dict.keys())},
        )

        # --- Strategy backtest ---
        strategy_result = self._run_strategy(price_dict, feature_dict, common_dates)

        results = {"strategy": strategy_result}

        # --- Buy and hold baseline ---
        if benchmark_ticker in price_dict:
            bh_result = self._buy_and_hold_baseline(
                price_dict[benchmark_ticker], common_dates
            )
            results["buy_and_hold"] = bh_result

        # --- MA crossover baseline ---
        if benchmark_ticker in price_dict:
            ma_result = self._ma_crossover_baseline(
                price_dict[benchmark_ticker], common_dates
            )
            results["ma_crossover"] = ma_result

        for name, res in results.items():
            logger.info(str(res))

        return results

    # ------------------------------------------------------------------
    # Strategy simulation
    # ------------------------------------------------------------------

    def _run_strategy(
        self,
        price_dict: Dict[str, pd.DataFrame],
        feature_dict: Dict[str, pd.DataFrame],
        dates: pd.DatetimeIndex,
    ) -> BacktestResult:
        portfolio = Portfolio(
            initial_cash=self.initial_cash,
            sizing_method="percent_of_equity",
            default_pct=0.05,
            max_position_pct=0.15,
        )
        equity_curve: List[float] = [self.initial_cash]
        trade_log: List[Dict[str, Any]] = []
        holdings: Dict[str, Dict[str, Any]] = {}  # symbol → {entry_price, entry_date, qty}

        for i, date in enumerate(dates):
            # Update current prices
            current_prices = {}
            for ticker, df in price_dict.items():
                if date in df.index:
                    current_prices[ticker] = float(df.loc[date, "Close"])

            if not current_prices:
                continue

            portfolio.update_prices(current_prices)

            # Check stop-loss / take-profit for held positions
            for ticker in list(holdings.keys()):
                if ticker not in current_prices:
                    continue
                trigger = self.risk_manager.check_stop_loss_take_profit(ticker, portfolio)
                if trigger:
                    price = current_prices[ticker]
                    held = holdings.pop(ticker)
                    pnl = self._close_position(portfolio, ticker, price, held, trigger, date, trade_log)

            # Generate signals using features up to this bar
            ticker_features: Dict[str, pd.DataFrame] = {}
            for ticker, feat_df in feature_dict.items():
                available = feat_df[feat_df.index <= date]
                if len(available) >= 2:
                    ticker_features[ticker] = available

            if not ticker_features:
                equity_curve.append(portfolio.equity)
                continue

            signals = self.strategy.generate_signals(ticker_features, timestamp=str(date)[:10])

            for sig in signals:
                price = current_prices.get(sig.ticker)
                if not price:
                    continue

                if sig.action == Action.BUY and sig.ticker not in holdings:
                    # Risk check: max positions
                    if len(holdings) >= self.max_positions:
                        continue
                    # Risk check: cash
                    qty = portfolio.compute_order_size(sig.ticker, price, sig.confidence)
                    if qty <= 0:
                        continue
                    cost = qty * price * (1 + self.slippage_pct) + self.commission
                    if portfolio.cash < cost:
                        continue

                    portfolio.cash -= cost
                    holdings[sig.ticker] = {
                        "entry_price": price,
                        "entry_date": date,
                        "qty": qty,
                    }

                elif sig.action == Action.SELL and sig.ticker in holdings:
                    held = holdings.pop(sig.ticker)
                    self._close_position(portfolio, sig.ticker, price, held, "signal", date, trade_log)

            equity_curve.append(portfolio.equity)
            self.risk_manager.update_peak_equity(portfolio.equity)

        # Close all open positions at end
        for ticker, held in holdings.items():
            price = current_prices.get(ticker, held["entry_price"])
            self._close_position(portfolio, ticker, price, held, "end_of_backtest", dates[-1], trade_log)

        return self._compute_result("strategy", equity_curve, trade_log)

    def _close_position(
        self,
        portfolio: Portfolio,
        ticker: str,
        price: float,
        held: Dict[str, Any],
        reason: str,
        date: Any,
        trade_log: List[Dict[str, Any]],
    ) -> float:
        qty = held["qty"]
        entry = held["entry_price"]
        proceeds = qty * price * (1 - self.slippage_pct) - self.commission
        portfolio.cash += proceeds
        pnl = (price - entry) * qty - self.commission - qty * entry * self.slippage_pct
        portfolio.realised_pnl += pnl

        holding_days = 0
        if isinstance(date, pd.Timestamp) and isinstance(held.get("entry_date"), pd.Timestamp):
            holding_days = (date - held["entry_date"]).days

        trade_log.append({
            "date": str(date)[:10],
            "symbol": ticker,
            "side": "SELL",
            "qty": qty,
            "entry_price": entry,
            "exit_price": price,
            "pnl": round(pnl, 2),
            "holding_days": holding_days,
            "reason": reason,
        })
        return pnl

    # ------------------------------------------------------------------
    # Baselines
    # ------------------------------------------------------------------

    def _buy_and_hold_baseline(
        self, price_df: pd.DataFrame, dates: pd.DatetimeIndex
    ) -> BacktestResult:
        """Simple buy-and-hold of a single asset."""
        available = price_df.reindex(dates).ffill().dropna()
        if available.empty:
            return BacktestResult("buy_and_hold", 0, 0, 0, 0, 0, 0, 0, 0, 0)

        start_price = float(available["Close"].iloc[0])
        shares = self.initial_cash / start_price
        equity = [shares * float(available["Close"].iloc[i]) for i in range(len(available))]
        return self._compute_result("buy_and_hold", equity, [])

    def _ma_crossover_baseline(
        self, price_df: pd.DataFrame, dates: pd.DatetimeIndex
    ) -> BacktestResult:
        """20/60 day moving-average crossover strategy on a single asset."""
        available = price_df.reindex(dates).ffill().dropna()
        if available.empty:
            return BacktestResult("ma_crossover", 0, 0, 0, 0, 0, 0, 0, 0, 0)

        close = available["Close"]
        ma_fast = close.rolling(20).mean()
        ma_slow = close.rolling(60).mean()
        signal = (ma_fast > ma_slow).astype(int)

        cash = self.initial_cash
        shares = 0.0
        equity_curve = []
        trades: List[Dict[str, Any]] = []
        in_position = False

        for i in range(len(available)):
            price = float(close.iloc[i])
            sig = int(signal.iloc[i]) if not np.isnan(signal.iloc[i]) else 0

            if sig == 1 and not in_position and cash > 0:
                shares = cash / (price * (1 + self.slippage_pct))
                cash = 0.0
                in_position = True
            elif sig == 0 and in_position:
                cash = shares * price * (1 - self.slippage_pct)
                pnl_est = cash - self.initial_cash
                trades.append({"pnl": pnl_est})
                shares = 0.0
                in_position = False

            equity_curve.append(cash + shares * price)

        return self._compute_result("ma_crossover", equity_curve, trades)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _compute_result(
        self,
        name: str,
        equity_curve: List[float],
        trade_log: List[Dict[str, Any]],
    ) -> BacktestResult:
        if not equity_curve:
            return BacktestResult(name, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        eq = np.array(equity_curve)
        total_ret = (eq[-1] - eq[0]) / eq[0] * 100 if eq[0] > 0 else 0
        n = len(eq)
        ann_ret = ((eq[-1] / eq[0]) ** (_PERIODS_PER_YEAR / max(n, 1)) - 1) * 100 if eq[0] > 0 else 0

        returns = np.diff(eq) / eq[:-1]
        sharpe = self._sharpe(returns)
        sortino = self._sortino(returns)
        max_dd = self._max_drawdown(eq)

        pnl_values = [t.get("pnl", 0) for t in trade_log]
        n_trades = len(pnl_values)
        wins = sum(1 for p in pnl_values if p > 0)
        win_rate = wins / n_trades * 100 if n_trades else 0
        avg_pnl = float(np.mean(pnl_values)) if pnl_values else 0

        holding_days = [t.get("holding_days", 0) for t in trade_log]
        avg_hold = float(np.mean(holding_days)) if holding_days else 0

        return BacktestResult(
            strategy_name=name,
            total_return_pct=round(total_ret, 2),
            annualised_return_pct=round(ann_ret, 2),
            sharpe_ratio=round(sharpe, 3),
            sortino_ratio=round(sortino, 3),
            max_drawdown_pct=round(max_dd, 2),
            win_rate_pct=round(win_rate, 1),
            total_trades=n_trades,
            avg_trade_pnl=round(avg_pnl, 2),
            avg_holding_periods=round(avg_hold, 1),
            equity_curve=list(eq),
            trade_log=trade_log,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _common_dates(feature_dict: Dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
        """Return the intersection of dates across all ticker feature DataFrames."""
        if not feature_dict:
            return pd.DatetimeIndex([])
        idx = None
        for df in feature_dict.values():
            idx = df.index if idx is None else idx.intersection(df.index)
        return idx if idx is not None else pd.DatetimeIndex([])

    @staticmethod
    def _sharpe(returns: np.ndarray, rfr: float = 0.04) -> float:
        if len(returns) < 2:
            return 0.0
        excess = returns - rfr / _PERIODS_PER_YEAR
        std = returns.std()
        return float(excess.mean() / std * np.sqrt(_PERIODS_PER_YEAR)) if std > 1e-9 else 0.0

    @staticmethod
    def _sortino(returns: np.ndarray, rfr: float = 0.04) -> float:
        if len(returns) < 2:
            return 0.0
        excess = returns - rfr / _PERIODS_PER_YEAR
        downside = returns[returns < 0]
        dd_std = downside.std() if len(downside) > 1 else 1e-9
        return float(excess.mean() / dd_std * np.sqrt(_PERIODS_PER_YEAR)) if dd_std > 1e-9 else 0.0

    @staticmethod
    def _max_drawdown(equity: np.ndarray) -> float:
        if len(equity) < 2:
            return 0.0
        peak = np.maximum.accumulate(equity)
        dd = (peak - equity) / peak * 100
        return float(dd.max())
