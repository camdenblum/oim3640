"""
execution/broker_alpaca.py — Alpaca Markets broker adapter.

Implements BrokerBase using the alpaca-py SDK.
Credentials are read from environment variables — never hardcoded.

Required environment variables (set in shell or .env):
    ALPACA_API_KEY       — your Alpaca API key ID
    ALPACA_SECRET_KEY    — your Alpaca secret key
    ALPACA_BASE_URL      — e.g. https://paper-api.alpaca.markets (paper)
                                    or https://api.alpaca.markets (live)

Install: pip install alpaca-py
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional

from execution.broker_api import (
    AccountSummary,
    BrokerBase,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    TimeInForce,
)

logger = logging.getLogger(__name__)

# Alpaca SDK imports — guarded so the rest of the bot can still load
# even if alpaca-py is not installed (e.g. during unit testing)
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import (
        MarketOrderRequest,
        LimitOrderRequest,
        GetAssetsRequest,
    )
    from alpaca.trading.enums import (
        OrderSide as AlpacaOrderSide,
        TimeInForce as AlpacaTIF,
        OrderType as AlpacaOrderType,
    )
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestQuoteRequest
    _ALPACA_AVAILABLE = True
except ImportError:
    _ALPACA_AVAILABLE = False
    logger.warning("alpaca-py not installed — AlpacaBroker will not function")


class AlpacaBroker(BrokerBase):
    """Alpaca Markets broker adapter.

    Args:
        api_key: Alpaca API key (defaults to ALPACA_API_KEY env var).
        secret_key: Alpaca secret key (defaults to ALPACA_SECRET_KEY env var).
        base_url: Alpaca base URL (defaults to ALPACA_BASE_URL env var).
        paper: If True, always point to paper-trading endpoint.
        slippage_pct: Assumed slippage percentage for cost estimation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        paper: bool = True,
        slippage_pct: float = 0.0005,
    ) -> None:
        if not _ALPACA_AVAILABLE:
            raise ImportError(
                "alpaca-py is required for AlpacaBroker. Install it with: pip install alpaca-py"
            )

        self._api_key = api_key or os.environ.get("ALPACA_API_KEY", "")
        self._secret_key = secret_key or os.environ.get("ALPACA_SECRET_KEY", "")
        self._base_url = base_url or os.environ.get(
            "ALPACA_BASE_URL",
            "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets",
        )
        self._paper = paper
        self._slippage_pct = slippage_pct
        self._client: Optional[TradingClient] = None
        self._data_client: Optional[StockHistoricalDataClient] = None
        self._connected = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        if not self._api_key or not self._secret_key:
            raise EnvironmentError(
                "ALPACA_API_KEY and ALPACA_SECRET_KEY must be set in the environment."
            )
        try:
            self._client = TradingClient(
                api_key=self._api_key,
                secret_key=self._secret_key,
                paper=self._paper,
            )
            self._data_client = StockHistoricalDataClient(
                api_key=self._api_key,
                secret_key=self._secret_key,
            )
            # Verify connection
            acct = self._client.get_account()
            self._connected = True
            logger.info(
                "Alpaca connected",
                extra={"account_id": str(acct.id)[:8] + "...", "paper": self._paper},
            )
            return True
        except Exception as exc:
            logger.error("Alpaca connection failed", extra={"error": str(exc)})
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._connected = False
        self._client = None
        logger.info("Alpaca disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ------------------------------------------------------------------
    # Account information
    # ------------------------------------------------------------------

    def get_account_summary(self) -> AccountSummary:
        self._require_connected()
        acct = self._client.get_account()  # type: ignore[union-attr]
        positions = self.get_all_positions()
        return AccountSummary(
            cash=float(acct.cash),
            portfolio_value=float(acct.portfolio_value),
            equity=float(acct.equity),
            buying_power=float(acct.buying_power),
            positions=positions,
            day_pnl=float(getattr(acct, "unrealized_pl", 0) or 0),
        )

    def get_position(self, symbol: str) -> Optional[Position]:
        self._require_connected()
        try:
            pos = self._client.get_open_position(symbol)  # type: ignore[union-attr]
            return self._alpaca_pos_to_position(pos)
        except Exception:
            return None  # No position found

    def get_all_positions(self) -> List[Position]:
        self._require_connected()
        try:
            alpaca_positions = self._client.get_all_positions()  # type: ignore[union-attr]
            return [self._alpaca_pos_to_position(p) for p in alpaca_positions]
        except Exception as exc:
            logger.warning("Could not fetch positions", extra={"error": str(exc)})
            return []

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def get_last_price(self, symbol: str) -> Optional[float]:
        if not self._data_client:
            return None
        try:
            req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self._data_client.get_stock_latest_quote(req)
            q = quote.get(symbol)
            if q:
                return float((q.ask_price + q.bid_price) / 2)
        except Exception as exc:
            logger.warning("Could not get price", extra={"symbol": symbol, "error": str(exc)})
        return None

    # ------------------------------------------------------------------
    # Order management
    # ------------------------------------------------------------------

    def place_order(self, order: Order) -> Order:
        self._require_connected()
        logger.info(
            "Placing order",
            extra={"symbol": order.symbol, "side": order.side, "qty": order.quantity,
                   "type": order.order_type},
        )
        try:
            alpaca_side = (
                AlpacaOrderSide.BUY if order.side == OrderSide.BUY else AlpacaOrderSide.SELL
            )
            tif = self._map_tif(order.time_in_force)

            if order.order_type == OrderType.MARKET:
                req = MarketOrderRequest(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                )
            else:
                req = LimitOrderRequest(
                    symbol=order.symbol,
                    qty=order.quantity,
                    side=alpaca_side,
                    time_in_force=tif,
                    limit_price=order.limit_price,
                )

            alpaca_order = self._client.submit_order(req)  # type: ignore[union-attr]
            order.order_id = str(alpaca_order.id)
            order.status = self._map_status(alpaca_order.status.value)
            order.submitted_at = str(alpaca_order.submitted_at or "")
            logger.info(
                "Order submitted",
                extra={"order_id": order.order_id, "status": order.status},
            )
        except Exception as exc:
            order.status = OrderStatus.REJECTED
            logger.error("Order rejected", extra={"symbol": order.symbol, "error": str(exc)})

        return order

    def cancel_order(self, order_id: str) -> bool:
        self._require_connected()
        try:
            self._client.cancel_order_by_id(order_id)  # type: ignore[union-attr]
            logger.info("Order cancelled", extra={"order_id": order_id})
            return True
        except Exception as exc:
            logger.warning("Cancel failed", extra={"order_id": order_id, "error": str(exc)})
            return False

    def refresh_order_status(self, order_id: str) -> Order:
        self._require_connected()
        try:
            alpaca_order = self._client.get_order_by_id(order_id)  # type: ignore[union-attr]
            order = Order(
                symbol=str(alpaca_order.symbol),
                side=OrderSide.BUY if alpaca_order.side.value == "buy" else OrderSide.SELL,
                quantity=float(alpaca_order.qty or 0),
                order_id=order_id,
                status=self._map_status(alpaca_order.status.value),
                filled_qty=float(alpaca_order.filled_qty or 0),
                filled_avg_price=float(alpaca_order.filled_avg_price or 0),
                filled_at=str(alpaca_order.filled_at or ""),
            )
            return order
        except Exception as exc:
            logger.error("Could not refresh order", extra={"order_id": order_id, "error": str(exc)})
            # Return a stub with PENDING status
            return Order(symbol="", side=OrderSide.BUY, quantity=0, order_id=order_id)

    def get_open_orders(self) -> List[Order]:
        self._require_connected()
        try:
            alpaca_orders = self._client.get_orders()  # type: ignore[union-attr]
            return [
                Order(
                    symbol=str(o.symbol),
                    side=OrderSide.BUY if str(o.side) == "buy" else OrderSide.SELL,
                    quantity=float(o.qty or 0),
                    order_id=str(o.id),
                    status=self._map_status(str(o.status)),
                )
                for o in alpaca_orders
            ]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Market state
    # ------------------------------------------------------------------

    def is_market_open(self) -> bool:
        try:
            clock = self._client.get_clock()  # type: ignore[union-attr]
            return bool(clock.is_open)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def calculate_slippage(self, order: Order, market_price: float) -> float:
        return abs(order.quantity * market_price) * self._slippage_pct

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_connected(self) -> None:
        if not self._connected or self._client is None:
            raise RuntimeError("Broker not connected — call connect() first.")

    @staticmethod
    def _alpaca_pos_to_position(pos: Any) -> Position:
        return Position(
            symbol=str(pos.symbol),
            quantity=float(pos.qty),
            avg_entry_price=float(pos.avg_entry_price),
            current_price=float(pos.current_price or 0),
            unrealised_pnl=float(pos.unrealized_pl or 0),
            market_value=float(pos.market_value or 0),
        )

    @staticmethod
    def _map_status(raw: str) -> OrderStatus:
        mapping = {
            "new": OrderStatus.SUBMITTED,
            "accepted": OrderStatus.SUBMITTED,
            "pending_new": OrderStatus.SUBMITTED,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "done_for_day": OrderStatus.CANCELLED,
            "canceled": OrderStatus.CANCELLED,
            "expired": OrderStatus.EXPIRED,
            "replaced": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }
        return mapping.get(raw.lower(), OrderStatus.PENDING)

    @staticmethod
    def _map_tif(tif: TimeInForce) -> "AlpacaTIF":
        mapping = {
            TimeInForce.DAY: AlpacaTIF.DAY,
            TimeInForce.GTC: AlpacaTIF.GTC,
            TimeInForce.IOC: AlpacaTIF.IOC,
            TimeInForce.FOK: AlpacaTIF.FOK,
        }
        return mapping.get(tif, AlpacaTIF.DAY)
