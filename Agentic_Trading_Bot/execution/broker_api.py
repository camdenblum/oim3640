"""
execution/broker_api.py — Abstract broker interface.

All concrete broker adapters (broker_alpaca.py, etc.) must implement BrokerBase.
This lets the rest of the bot be broker-agnostic; swapping brokers is a one-line
config change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Order / fill data structures
# ---------------------------------------------------------------------------

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    DAY = "day"
    GTC = "gtc"    # Good Till Cancelled
    IOC = "ioc"    # Immediate Or Cancel
    FOK = "fok"    # Fill Or Kill


@dataclass
class Order:
    """Represents an order to be placed or already placed."""
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: float = 0.0
    filled_avg_price: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    submitted_at: str = ""
    filled_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
        )

    @property
    def net_cost(self) -> float:
        """Total cost including commission (positive = cash out for buys)."""
        base = self.filled_avg_price * self.filled_qty
        return base + self.commission if self.side == OrderSide.BUY else -(base - self.commission)


@dataclass
class Position:
    """A current holding in the portfolio."""
    symbol: str
    quantity: float          # negative = short
    avg_entry_price: float
    current_price: float = 0.0
    unrealised_pnl: float = 0.0
    market_value: float = 0.0

    def update_price(self, price: float) -> None:
        self.current_price = price
        self.market_value = self.quantity * price
        self.unrealised_pnl = (price - self.avg_entry_price) * self.quantity


@dataclass
class AccountSummary:
    """Snapshot of the brokerage account."""
    cash: float
    portfolio_value: float
    equity: float
    buying_power: float
    positions: List[Position] = field(default_factory=list)
    day_pnl: float = 0.0
    total_pnl: float = 0.0
    currency: str = "USD"


# ---------------------------------------------------------------------------
# Abstract broker interface
# ---------------------------------------------------------------------------

class BrokerBase(ABC):
    """Abstract base class for all broker adapters.

    Concrete implementations must override every @abstractmethod.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> bool:
        """Establish a connection / authenticate with the broker API.

        Returns:
            True if connection succeeded.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Cleanly close the connection."""

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if currently connected."""

    # ------------------------------------------------------------------
    # Account information
    # ------------------------------------------------------------------

    @abstractmethod
    def get_account_summary(self) -> AccountSummary:
        """Return current account balances and positions."""

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """Return the current position for *symbol*, or None if flat."""

    @abstractmethod
    def get_all_positions(self) -> List[Position]:
        """Return all currently open positions."""

    # ------------------------------------------------------------------
    # Market data (lightweight — for last price only)
    # ------------------------------------------------------------------

    @abstractmethod
    def get_last_price(self, symbol: str) -> Optional[float]:
        """Return the most recent trade price for *symbol*."""

    # ------------------------------------------------------------------
    # Order management
    # ------------------------------------------------------------------

    @abstractmethod
    def place_order(self, order: Order) -> Order:
        """Submit *order* to the broker.

        Returns:
            Updated Order with broker-assigned order_id and status.
        """

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Request cancellation of an open order.

        Returns:
            True if the cancellation request was accepted.
        """

    @abstractmethod
    def refresh_order_status(self, order_id: str) -> Order:
        """Poll the broker for the latest status of *order_id*.

        Returns:
            Updated Order object.
        """

    @abstractmethod
    def get_open_orders(self) -> List[Order]:
        """Return all currently open (non-terminal) orders."""

    # ------------------------------------------------------------------
    # Market state helpers
    # ------------------------------------------------------------------

    @abstractmethod
    def is_market_open(self) -> bool:
        """Return True if the primary market is currently open for trading."""

    # ------------------------------------------------------------------
    # Utility (can be overridden)
    # ------------------------------------------------------------------

    def calculate_commission(self, order: Order) -> float:
        """Compute estimated commission for *order*.  Default: zero.
        Override in concrete adapters to match the broker's fee schedule."""
        return 0.0

    def calculate_slippage(self, order: Order, market_price: float) -> float:
        """Estimate slippage cost.  Default: 0.05% of trade value."""
        return abs(order.quantity * market_price) * 0.0005
