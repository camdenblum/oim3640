"""
portfolio/portfolio.py — Holdings, cash, P&L, and position sizing.

The Portfolio is the single source of truth for:
  - Current cash balance
  - Open positions (symbol → Position)
  - Realised and unrealised P&L
  - Performance metrics (Sharpe, max drawdown, win rate)
  - Order size computation based on configured sizing method
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from execution.broker_api import Order, OrderSide, Position

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """Immutable record of a completed trade."""
    timestamp: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    realised_pnl: float
    commission: float
    slippage: float
    holding_periods: int = 0
    reason: str = ""


class Portfolio:
    """Manages cash, positions, and P&L for paper or live trading.

    Args:
        initial_cash: Starting cash balance.
        sizing_method: "percent_of_equity" | "fixed" | "risk_parity"
        default_pct: Fraction of equity per position (for percent_of_equity).
        max_position_pct: Hard cap on any single position as fraction of equity.
        currency: Currency label for reporting.
    """

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        sizing_method: str = "percent_of_equity",
        default_pct: float = 0.05,
        max_position_pct: float = 0.15,
        currency: str = "USD",
    ) -> None:
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.sizing_method = sizing_method
        self.default_pct = default_pct
        self.max_position_pct = max_position_pct
        self.currency = currency

        # {symbol: Position}
        self.positions: Dict[str, Position] = {}

        # Closed trade history
        self.trade_history: List[TradeRecord] = []

        # Equity curve for performance calcs
        self._equity_history: List[float] = [initial_cash]

        # Running P&L
        self.realised_pnl: float = 0.0
        self.total_commissions: float = 0.0
        self.total_slippage: float = 0.0

    # ------------------------------------------------------------------
    # Core properties
    # ------------------------------------------------------------------

    @property
    def market_value(self) -> float:
        """Total market value of all open positions."""
        return sum(p.market_value for p in self.positions.values())

    @property
    def equity(self) -> float:
        """Total portfolio equity = cash + market value of positions."""
        return self.cash + self.market_value

    @property
    def unrealised_pnl(self) -> float:
        return sum(p.unrealised_pnl for p in self.positions.values())

    # ------------------------------------------------------------------
    # Position management
    # ------------------------------------------------------------------

    def get_position(self, symbol: str) -> Optional[Position]:
        """Return current position for *symbol*, or None if flat."""
        pos = self.positions.get(symbol)
        return pos if pos and pos.quantity != 0 else None

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Update market prices for all held positions.

        Args:
            prices: {symbol: current_price}
        """
        for symbol, pos in self.positions.items():
            price = prices.get(symbol)
            if price and price > 0:
                pos.update_price(price)
        self._equity_history.append(self.equity)

    def apply_fill(self, order: Order) -> None:
        """Apply a confirmed fill to cash and positions.

        Args:
            order: Filled Order with filled_qty and filled_avg_price populated.
        """
        from utils import now_iso
        qty = order.filled_qty
        price = order.filled_avg_price
        symbol = order.symbol
        commission = order.commission
        slippage = order.slippage

        if qty <= 0 or price <= 0:
            logger.warning("apply_fill: zero qty or price", extra={"order_id": order.order_id})
            return

        self.total_commissions += commission
        self.total_slippage += slippage

        if order.side == OrderSide.BUY:
            total_cost = qty * price + commission + slippage
            self.cash -= total_cost

            if symbol in self.positions:
                pos = self.positions[symbol]
                # Weighted average entry price
                old_cost = pos.quantity * pos.avg_entry_price
                new_cost = qty * price
                pos.quantity += qty
                pos.avg_entry_price = (old_cost + new_cost) / pos.quantity
            else:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    quantity=qty,
                    avg_entry_price=price,
                    current_price=price,
                    market_value=qty * price,
                )

            logger.info(
                "Position opened/increased",
                extra={"symbol": symbol, "qty": qty, "price": price, "cash_remaining": self.cash},
            )

        else:  # SELL
            pos = self.positions.get(symbol)
            if pos is None:
                logger.warning("Sell fill but no position found", extra={"symbol": symbol})
                return

            sell_qty = min(qty, pos.quantity)
            proceeds = sell_qty * price - commission - slippage
            pnl = (price - pos.avg_entry_price) * sell_qty - commission - slippage
            self.cash += proceeds
            self.realised_pnl += pnl

            self.trade_history.append(TradeRecord(
                timestamp=now_iso(),
                symbol=symbol,
                side="SELL",
                quantity=sell_qty,
                entry_price=pos.avg_entry_price,
                exit_price=price,
                realised_pnl=pnl,
                commission=commission,
                slippage=slippage,
            ))

            pos.quantity -= sell_qty
            if pos.quantity <= 0:
                del self.positions[symbol]
                logger.info("Position closed", extra={"symbol": symbol, "pnl": round(pnl, 2)})
            else:
                logger.info(
                    "Position partially closed",
                    extra={"symbol": symbol, "remaining": pos.quantity, "pnl": round(pnl, 2)},
                )

    # ------------------------------------------------------------------
    # Position sizing
    # ------------------------------------------------------------------

    def compute_order_size(
        self,
        symbol: str,
        price: float,
        confidence: float = 0.5,
    ) -> float:
        """Compute how many shares to buy.

        Args:
            symbol: Ticker to buy.
            price: Current market price.
            confidence: Signal confidence (0–0.5); used to scale position slightly.

        Returns:
            Number of whole shares (floor).
        """
        equity = self.equity
        if equity <= 0 or price <= 0:
            return 0.0

        if self.sizing_method == "percent_of_equity":
            # Scale position by confidence (confidence ∈ [0, 0.5])
            confidence_scalar = 1.0 + confidence  # 1.0x to 1.5x
            target_pct = min(self.default_pct * confidence_scalar, self.max_position_pct)
            dollar_amount = equity * target_pct

        elif self.sizing_method == "fixed":
            dollar_amount = equity * self.default_pct

        elif self.sizing_method == "risk_parity":
            # Allocate equal risk — simplified: equal dollar weight
            n = max(1, len(self.positions) + 1)
            dollar_amount = min(equity / n, equity * self.max_position_pct)

        else:
            dollar_amount = equity * self.default_pct

        # Cap by available cash (leave reserve buffer built into risk.py)
        dollar_amount = min(dollar_amount, self.cash * 0.95)

        shares = math.floor(dollar_amount / price)
        return float(max(0, shares))

    # ------------------------------------------------------------------
    # Performance metrics
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """Return a snapshot of key performance metrics."""
        equity_arr = np.array(self._equity_history)
        total_return = (self.equity - self.initial_cash) / self.initial_cash * 100 if self.initial_cash else 0
        max_dd = self._max_drawdown(equity_arr)
        sharpe = self._sharpe_ratio(equity_arr)
        win_rate = self._win_rate()
        return {
            "equity": round(self.equity, 2),
            "cash": round(self.cash, 2),
            "market_value": round(self.market_value, 2),
            "realised_pnl": round(self.realised_pnl, 2),
            "unrealised_pnl": round(self.unrealised_pnl, 2),
            "total_return_pct": round(total_return, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "sharpe_ratio": round(sharpe, 3),
            "win_rate_pct": round(win_rate, 1),
            "total_trades": len(self.trade_history),
            "open_positions": len(self.positions),
            "total_commissions": round(self.total_commissions, 2),
            "total_slippage": round(self.total_slippage, 2),
        }

    def recent_trade_returns(self, n: int = 50) -> List[float]:
        """Return realised P&L for the last *n* trades."""
        return [t.realised_pnl for t in self.trade_history[-n:]]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _max_drawdown(equity_arr: np.ndarray) -> float:
        if len(equity_arr) < 2:
            return 0.0
        peak = np.maximum.accumulate(equity_arr)
        dd = (peak - equity_arr) / peak * 100
        return float(dd.max())

    @staticmethod
    def _sharpe_ratio(equity_arr: np.ndarray, risk_free: float = 0.04) -> float:
        if len(equity_arr) < 2:
            return 0.0
        returns = np.diff(equity_arr) / equity_arr[:-1]
        excess = returns - risk_free / 252  # daily risk-free rate
        std = returns.std()
        if std < 1e-9:
            return 0.0
        return float(excess.mean() / std * np.sqrt(252))

    def _win_rate(self) -> float:
        if not self.trade_history:
            return 0.0
        wins = sum(1 for t in self.trade_history if t.realised_pnl > 0)
        return wins / len(self.trade_history) * 100
