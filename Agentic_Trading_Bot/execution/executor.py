"""
execution/executor.py — Order lifecycle management engine.

Responsibilities:
  - Accept signals from the strategy and decide which orders to place.
  - Run pre-trade risk checks (via risk.py).
  - Submit orders through the broker adapter.
  - Track order fills with retry / backoff logic.
  - Update the portfolio after confirmed fills.
  - Log all trade events in a structured format.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from execution.broker_api import (
    BrokerBase,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    TimeInForce,
)
from models.strategy import Action, Signal

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Outcome of an attempt to execute a signal."""
    signal: Signal
    order: Optional[Order]
    success: bool
    reason: str
    pnl_estimate: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Executor:
    """Manages the full order lifecycle: signal → order → fill → portfolio update.

    Args:
        broker: Connected BrokerBase adapter.
        portfolio: Portfolio instance (updated after fills).
        risk_manager: RiskManager instance (pre-trade checks).
        order_type: Default order type ("market" or "limit").
        order_timeout_secs: Seconds to wait for an order to fill before cancelling.
        max_retries: Number of submission retries on transient failures.
        retry_backoff: Initial backoff in seconds (doubles each retry).
        slippage_pct: Slippage rate for paper/cost estimation.
        commission_per_trade: Flat commission per order.
    """

    def __init__(
        self,
        broker: BrokerBase,
        portfolio: Any,  # portfolio.Portfolio — imported at runtime to avoid circular imports
        risk_manager: Any,  # risk.RiskManager
        order_type: str = "market",
        order_timeout_secs: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 2.0,
        slippage_pct: float = 0.0005,
        commission_per_trade: float = 0.0,
    ) -> None:
        self.broker = broker
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.order_type = OrderType.MARKET if order_type == "market" else OrderType.LIMIT
        self.order_timeout_secs = order_timeout_secs
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.slippage_pct = slippage_pct
        self.commission_per_trade = commission_per_trade

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_signals(self, signals: List[Signal]) -> List[ExecutionResult]:
        """Process a batch of signals, executing eligible trades.

        Args:
            signals: Output from Strategy.generate_signals().

        Returns:
            List of ExecutionResult (one per signal, whether executed or skipped).
        """
        results: List[ExecutionResult] = []
        for signal in signals:
            result = self._process_signal(signal)
            results.append(result)
        return results

    def execute_single(self, signal: Signal) -> ExecutionResult:
        """Execute a single signal."""
        return self._process_signal(signal)

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    def _process_signal(self, signal: Signal) -> ExecutionResult:
        """Pipeline: risk check → size → submit → wait for fill → update portfolio."""
        # Skip HOLD signals
        if signal.action == Action.HOLD:
            return ExecutionResult(signal=signal, order=None, success=False, reason="HOLD signal")

        # Get current market price
        price = self.broker.get_last_price(signal.ticker)
        if price is None or price <= 0:
            return ExecutionResult(
                signal=signal, order=None, success=False,
                reason=f"Could not get price for {signal.ticker}",
            )

        # Determine quantity
        quantity = self._compute_quantity(signal, price)
        if quantity <= 0:
            return ExecutionResult(
                signal=signal, order=None, success=False,
                reason="Quantity calculated as 0 — insufficient buying power or already at max position",
            )

        # Build order
        side = OrderSide.BUY if signal.action == Action.BUY else OrderSide.SELL
        order = Order(
            symbol=signal.ticker,
            side=side,
            quantity=quantity,
            order_type=self.order_type,
            limit_price=round(price * (0.999 if side == OrderSide.BUY else 1.001), 2)
                if self.order_type == OrderType.LIMIT else None,
            time_in_force=TimeInForce.DAY,
            metadata={"signal_score": signal.score, "reason": signal.reason},
        )

        # Pre-trade risk check
        risk_decision = self.risk_manager.check_order(order, price, self.portfolio)
        if not risk_decision.allowed:
            logger.info(
                "Order blocked by risk",
                extra={"ticker": signal.ticker, "reason": risk_decision.reason},
            )
            return ExecutionResult(
                signal=signal, order=order, success=False,
                reason=f"Risk blocked: {risk_decision.reason}",
            )

        # Submit with retry
        filled_order = self._submit_with_retry(order)

        if filled_order.status == OrderStatus.FILLED:
            # Update portfolio
            self.portfolio.apply_fill(filled_order)
            logger.info(
                "Trade executed",
                extra={
                    "ticker": signal.ticker,
                    "side": side.value,
                    "qty": filled_order.filled_qty,
                    "price": filled_order.filled_avg_price,
                    "commission": filled_order.commission,
                    "signal_score": signal.score,
                },
            )
            return ExecutionResult(
                signal=signal, order=filled_order, success=True,
                reason="Filled",
            )
        else:
            return ExecutionResult(
                signal=signal, order=filled_order, success=False,
                reason=f"Order not filled — status: {filled_order.status}",
            )

    def _submit_with_retry(self, order: Order) -> Order:
        """Submit an order with exponential backoff retries."""
        backoff = self.retry_backoff
        for attempt in range(1, self.max_retries + 1):
            try:
                submitted = self.broker.place_order(order)
                if submitted.status in (OrderStatus.REJECTED,):
                    logger.warning(
                        "Order rejected on attempt",
                        extra={"attempt": attempt, "symbol": order.symbol},
                    )
                    return submitted  # No point retrying a rejection

                # Wait for fill
                filled = self._wait_for_fill(submitted)
                if filled.is_terminal:
                    # Add estimated slippage & commission
                    if filled.status == OrderStatus.FILLED:
                        filled.slippage = abs(filled.filled_qty * filled.filled_avg_price) * self.slippage_pct
                        filled.commission = self.commission_per_trade
                    return filled

            except Exception as exc:
                logger.warning(
                    "Submission error",
                    extra={"attempt": attempt, "symbol": order.symbol, "error": str(exc)},
                )
                if attempt < self.max_retries:
                    time.sleep(backoff)
                    backoff *= 2

        # All retries exhausted — cancel if we have an order id
        if order.order_id:
            self.broker.cancel_order(order.order_id)
        order.status = OrderStatus.CANCELLED
        return order

    def _wait_for_fill(self, order: Order) -> Order:
        """Poll broker until order is terminal or timeout expires."""
        if order.order_id is None:
            return order

        deadline = time.time() + self.order_timeout_secs
        poll_interval = 1.0

        while time.time() < deadline:
            refreshed = self.broker.refresh_order_status(order.order_id)
            if refreshed.is_terminal:
                return refreshed
            time.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.5, 5.0)

        # Timeout — cancel the order
        logger.warning(
            "Order fill timeout, cancelling",
            extra={"order_id": order.order_id, "symbol": order.symbol},
        )
        self.broker.cancel_order(order.order_id)
        order.status = OrderStatus.CANCELLED
        return order

    def _compute_quantity(self, signal: Signal, price: float) -> float:
        """Determine how many shares to trade.

        Delegates sizing to portfolio.compute_order_size() which respects
        the configured sizing method (percent_of_equity, fixed, risk_parity).
        """
        if signal.action == Action.SELL:
            # Sell entire position
            pos = self.portfolio.get_position(signal.ticker)
            return pos.quantity if pos else 0.0

        return self.portfolio.compute_order_size(signal.ticker, price, signal.confidence)
