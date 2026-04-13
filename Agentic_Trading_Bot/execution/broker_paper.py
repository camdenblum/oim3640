"""
execution/broker_paper.py — Simulated paper-trading broker.

Simulates order fills using yfinance close prices.  No real credentials needed.
Used by default when mode=paper and no external broker is configured.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta
from typing import Dict, List, Optional

from execution.broker_api import (
    AccountSummary,
    BrokerBase,
    Order,
    OrderSide,
    OrderStatus,
    Position,
)

logger = logging.getLogger(__name__)


class PaperBroker(BrokerBase):
    """Simulated broker for paper trading.

    All orders are immediately filled at the last known price minus
    a configurable slippage.  No network calls are made.

    Args:
        initial_cash: Starting cash balance.
        slippage_pct: Slippage applied to every fill.
        commission: Flat commission per order.
    """

    def __init__(
        self,
        initial_cash: float = 100_000.0,
        slippage_pct: float = 0.0005,
        commission: float = 0.0,
    ) -> None:
        self._cash = initial_cash
        self._initial_cash = initial_cash
        self._slippage_pct = slippage_pct
        self._commission = commission
        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, Order] = {}
        self._prices: Dict[str, float] = {}
        self._connected = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        self._connected = True
        logger.info("PaperBroker connected", extra={"initial_cash": self._cash})
        return True

    def disconnect(self) -> None:
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Account
    # ------------------------------------------------------------------

    def get_account_summary(self) -> AccountSummary:
        mv = sum(p.market_value for p in self._positions.values())
        return AccountSummary(
            cash=self._cash,
            portfolio_value=self._cash + mv,
            equity=self._cash + mv,
            buying_power=self._cash,
            positions=list(self._positions.values()),
        )

    def get_position(self, symbol: str) -> Optional[Position]:
        return self._positions.get(symbol)

    def get_all_positions(self) -> List[Position]:
        return list(self._positions.values())

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def get_last_price(self, symbol: str) -> Optional[float]:
        """Return the cached price, or fetch from yfinance as a fallback."""
        if symbol in self._prices:
            return self._prices[symbol]
        try:
            import yfinance as yf
            df = yf.download(
                symbol,
                start=str(date.today() - timedelta(days=5)),
                auto_adjust=True,
                progress=False,
                threads=False,
            )
            if not df.empty:
                price = float(df["Close"].iloc[-1])
                self._prices[symbol] = price
                return price
        except Exception as exc:
            logger.warning("Could not fetch price", extra={"symbol": symbol, "error": str(exc)})
        return None

    def update_prices(self, prices: Dict[str, float]) -> None:
        """Inject price updates (called by main loop before generating signals)."""
        self._prices.update(prices)
        for symbol, price in prices.items():
            if symbol in self._positions:
                self._positions[symbol].update_price(price)

    # ------------------------------------------------------------------
    # Orders — instant simulated fills
    # ------------------------------------------------------------------

    def place_order(self, order: Order) -> Order:
        price = self._prices.get(order.symbol)
        if price is None:
            price = self.get_last_price(order.symbol) or 0.0

        if price <= 0:
            order.status = OrderStatus.REJECTED
            logger.warning("No price available, rejecting paper order", extra={"symbol": order.symbol})
            return order

        # Apply slippage
        if order.side == OrderSide.BUY:
            fill_price = price * (1 + self._slippage_pct)
        else:
            fill_price = price * (1 - self._slippage_pct)

        order.order_id = str(uuid.uuid4())[:8]
        order.filled_qty = order.quantity
        order.filled_avg_price = round(fill_price, 4)
        order.commission = self._commission
        order.slippage = abs(order.quantity * price) * self._slippage_pct
        order.status = OrderStatus.FILLED

        self._orders[order.order_id] = order
        logger.info(
            "Paper order filled",
            extra={
                "symbol": order.symbol,
                "side": order.side.value,
                "qty": order.quantity,
                "price": order.filled_avg_price,
            },
        )
        return order

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self._orders:
            self._orders[order_id].status = OrderStatus.CANCELLED
            return True
        return False

    def refresh_order_status(self, order_id: str) -> Order:
        if order_id in self._orders:
            return self._orders[order_id]
        return Order(symbol="", side=OrderSide.BUY, quantity=0, order_id=order_id)

    def get_open_orders(self) -> List[Order]:
        return [o for o in self._orders.values() if not o.is_terminal]

    # ------------------------------------------------------------------
    # Market state
    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        """Always return True for paper trading (we accept all bars)."""
        return True

    # ------------------------------------------------------------------
    # Slippage
    # ------------------------------------------------------------------

    def calculate_slippage(self, order: Order, market_price: float) -> float:
        return abs(order.quantity * market_price) * self._slippage_pct
