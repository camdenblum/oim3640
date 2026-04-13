"""
risk/risk.py — Risk management engine and circuit breakers.

Evaluates every proposed order against a suite of configurable risk rules.
If any rule trips, the order is blocked.  Circuit breakers can also halt
all trading for the rest of the day (or until manually reset).

Rules enforced:
  1. Max total portfolio drawdown (halt trading completely if breached)
  2. Max daily loss (circuit breaker: halt for rest of day)
  3. Max concurrent positions
  4. Max position size (as % of equity)
  5. Minimum cash reserve
  6. Per-position stop-loss / take-profit (checked on SELL signals)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from execution.broker_api import Order, OrderSide

logger = logging.getLogger(__name__)


@dataclass
class RiskDecision:
    """Result of a pre-trade risk check."""
    allowed: bool
    reason: str


class RiskManager:
    """Enforces risk limits on orders and monitors portfolio health.

    Args:
        max_total_drawdown_pct: Halt trading if portfolio drops this % from its peak.
        max_daily_loss_pct: Halt for the day if daily loss exceeds this % of equity.
        max_positions: Maximum number of concurrently held symbols.
        max_position_size_pct: Max single position as % of total equity.
        stop_loss_pct: Liquidate a position if it falls this % below entry.
        take_profit_pct: Liquidate a position if it rises this % above entry.
        min_cash_reserve_pct: Keep at least this % of equity in cash.
    """

    def __init__(
        self,
        max_total_drawdown_pct: float = 10.0,
        max_daily_loss_pct: float = 2.0,
        max_positions: int = 8,
        max_position_size_pct: float = 15.0,
        stop_loss_pct: float = 5.0,
        take_profit_pct: float = 15.0,
        min_cash_reserve_pct: float = 5.0,
    ) -> None:
        self.max_total_drawdown_pct = max_total_drawdown_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_positions = max_positions
        self.max_position_size_pct = max_position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.min_cash_reserve_pct = min_cash_reserve_pct

        self._peak_equity: float = 0.0
        self._day_start_equity: float = 0.0
        self._current_day: date = date.today()
        self._trading_halted: bool = False
        self._halt_reason: str = ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_order(self, order: Order, price: float, portfolio: Any) -> RiskDecision:
        """Run all pre-trade risk checks.

        Args:
            order: The proposed order.
            price: Current market price for the symbol.
            portfolio: Portfolio instance with equity, cash, and positions.

        Returns:
            RiskDecision with allowed=True only if all checks pass.
        """
        # Update intraday tracking
        self._update_daily_tracking(portfolio)

        # 1. Global halt check
        if self._trading_halted:
            return RiskDecision(False, f"Trading halted: {self._halt_reason}")

        equity = portfolio.equity

        # 2. Max drawdown circuit breaker
        if equity > 0 and self._peak_equity > 0:
            drawdown_pct = (self._peak_equity - equity) / self._peak_equity * 100
            if drawdown_pct >= self.max_total_drawdown_pct:
                self._halt(f"Max drawdown {drawdown_pct:.1f}% exceeded limit {self.max_total_drawdown_pct}%")
                return RiskDecision(False, self._halt_reason)

        # 3. Daily loss circuit breaker
        if self._day_start_equity > 0 and equity > 0:
            daily_loss_pct = (self._day_start_equity - equity) / self._day_start_equity * 100
            if daily_loss_pct >= self.max_daily_loss_pct:
                self._halt(
                    f"Daily loss {daily_loss_pct:.1f}% exceeded limit {self.max_daily_loss_pct}%",
                    temporary=True,
                )
                return RiskDecision(False, self._halt_reason)

        # BUY-specific checks
        if order.side == OrderSide.BUY:
            # 4. Max position count
            n_positions = len([p for p in portfolio.positions.values() if p.quantity > 0])
            if n_positions >= self.max_positions and order.symbol not in portfolio.positions:
                return RiskDecision(
                    False,
                    f"Max positions ({self.max_positions}) already held — cannot open {order.symbol}",
                )

            # 5. Max position size
            order_value = order.quantity * price
            if equity > 0:
                position_pct = (order_value / equity) * 100
                if position_pct > self.max_position_size_pct:
                    return RiskDecision(
                        False,
                        f"Order value {position_pct:.1f}% of equity exceeds max {self.max_position_size_pct}%",
                    )

            # 6. Cash reserve
            cash_after = portfolio.cash - order_value
            min_cash = equity * self.min_cash_reserve_pct / 100
            if cash_after < min_cash:
                return RiskDecision(
                    False,
                    f"Insufficient cash after order: ${cash_after:.0f} < reserve ${min_cash:.0f}",
                )

        return RiskDecision(True, "All checks passed")

    def check_stop_loss_take_profit(self, symbol: str, portfolio: Any) -> Optional[str]:
        """Check if a held position should be liquidated via SL/TP.

        Args:
            symbol: Ticker to check.
            portfolio: Portfolio with current positions.

        Returns:
            "stop_loss" | "take_profit" | None
        """
        pos = portfolio.get_position(symbol)
        if pos is None or pos.quantity <= 0:
            return None
        if pos.avg_entry_price <= 0:
            return None

        current = pos.current_price
        entry = pos.avg_entry_price
        pct_change = (current - entry) / entry * 100

        if pct_change <= -self.stop_loss_pct:
            logger.warning(
                "Stop-loss triggered",
                extra={"symbol": symbol, "pct_change": round(pct_change, 2),
                       "entry": entry, "current": current},
            )
            return "stop_loss"

        if pct_change >= self.take_profit_pct:
            logger.info(
                "Take-profit triggered",
                extra={"symbol": symbol, "pct_change": round(pct_change, 2),
                       "entry": entry, "current": current},
            )
            return "take_profit"

        return None

    def update_peak_equity(self, equity: float) -> None:
        """Call at start of each bar to track the equity high-water mark."""
        if equity > self._peak_equity:
            self._peak_equity = equity

    def reset_daily_halt(self) -> None:
        """Reset a temporary daily halt (call at market open next day)."""
        if self._trading_halted and "daily loss" in self._halt_reason.lower():
            self._trading_halted = False
            self._halt_reason = ""
            logger.info("Daily halt reset")

    def force_halt(self, reason: str) -> None:
        """Permanently halt trading (requires manual reset)."""
        self._halt(reason, temporary=False)

    def reset_halt(self) -> None:
        """Manually clear a permanent halt."""
        self._trading_halted = False
        self._halt_reason = ""
        logger.info("Trading halt cleared manually")

    @property
    def is_halted(self) -> bool:
        return self._trading_halted

    @property
    def halt_reason(self) -> str:
        return self._halt_reason

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _update_daily_tracking(self, portfolio: Any) -> None:
        today = date.today()
        if today != self._current_day:
            # New trading day — reset daily tracking
            self._current_day = today
            self._day_start_equity = portfolio.equity
            self.reset_daily_halt()
            logger.info("New trading day", extra={"day_start_equity": portfolio.equity})

        # Initialise on first call
        if self._day_start_equity == 0:
            self._day_start_equity = portfolio.equity
        if self._peak_equity == 0:
            self._peak_equity = portfolio.equity

        self.update_peak_equity(portfolio.equity)

    def _halt(self, reason: str, temporary: bool = False) -> None:
        self._trading_halted = True
        self._halt_reason = reason
        tag = "temporary" if temporary else "permanent"
        logger.error(f"TRADING HALTED ({tag})", extra={"reason": reason})
