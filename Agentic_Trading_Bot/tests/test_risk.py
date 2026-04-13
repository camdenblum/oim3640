"""
tests/test_risk.py — Unit tests for the RiskManager.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.broker_api import Order, OrderSide, OrderType
from risk.risk import RiskManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_portfolio(
    equity: float = 100_000.0,
    cash: float = 80_000.0,
    positions: dict | None = None,
) -> MagicMock:
    port = MagicMock()
    port.equity = equity
    port.cash = cash
    port.positions = positions or {}
    return port


def _make_order(
    symbol: str = "AAPL",
    side: OrderSide = OrderSide.BUY,
    quantity: float = 10.0,
) -> Order:
    return Order(symbol=symbol, side=side, quantity=quantity, order_type=OrderType.MARKET)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRiskManager:
    def test_basic_allow(self):
        rm = RiskManager()
        order = _make_order()
        port = _make_portfolio()
        decision = rm.check_order(order, price=150.0, portfolio=port)
        assert decision.allowed

    def test_max_positions_blocks_new_buy(self):
        rm = RiskManager(max_positions=2)
        # Simulate 2 positions already held
        positions = {"AAPL": MagicMock(quantity=10), "MSFT": MagicMock(quantity=5)}
        port = _make_portfolio(positions=positions)
        # Try to buy a new ticker — should be blocked
        order = _make_order(symbol="NVDA", side=OrderSide.BUY)
        decision = rm.check_order(order, price=100.0, portfolio=port)
        assert not decision.allowed
        assert "positions" in decision.reason.lower()

    def test_max_positions_allows_adding_to_existing(self):
        """Adding to an existing position should be allowed even at max positions."""
        rm = RiskManager(max_positions=1)
        positions = {"AAPL": MagicMock(quantity=10)}
        port = _make_portfolio(positions=positions)
        order = _make_order(symbol="AAPL", side=OrderSide.BUY)
        decision = rm.check_order(order, price=150.0, portfolio=port)
        # AAPL is already in positions, so it's not opening a new slot
        assert decision.allowed

    def test_max_drawdown_blocks_trading(self):
        rm = RiskManager(max_total_drawdown_pct=10.0)
        # Set peak at 100k, current at 88k → 12% drawdown
        rm._peak_equity = 100_000.0
        port = _make_portfolio(equity=88_000.0, cash=80_000.0)
        order = _make_order()
        decision = rm.check_order(order, price=100.0, portfolio=port)
        assert not decision.allowed
        assert rm.is_halted

    def test_daily_loss_circuit_breaker(self):
        rm = RiskManager(max_daily_loss_pct=2.0)
        rm._day_start_equity = 100_000.0
        rm._current_day = __import__("datetime").date.today()
        port = _make_portfolio(equity=97_500.0, cash=80_000.0)
        order = _make_order()
        decision = rm.check_order(order, price=100.0, portfolio=port)
        assert not decision.allowed

    def test_insufficient_cash_blocks_buy(self):
        rm = RiskManager(min_cash_reserve_pct=5.0)
        port = _make_portfolio(equity=100_000.0, cash=100.0)  # very little cash
        order = _make_order(quantity=100)  # 100 shares @ $150 = $15,000
        decision = rm.check_order(order, price=150.0, portfolio=port)
        assert not decision.allowed

    def test_sell_order_allowed_even_at_max_positions(self):
        rm = RiskManager(max_positions=1)
        positions = {"AAPL": MagicMock(quantity=10)}
        port = _make_portfolio(positions=positions)
        order = _make_order(symbol="AAPL", side=OrderSide.SELL)
        decision = rm.check_order(order, price=150.0, portfolio=port)
        assert decision.allowed

    def test_stop_loss_triggered(self):
        rm = RiskManager(stop_loss_pct=5.0)
        pos = MagicMock()
        pos.quantity = 10
        pos.avg_entry_price = 100.0
        pos.current_price = 93.0  # -7% → trigger
        port = MagicMock()
        port.get_position.return_value = pos
        trigger = rm.check_stop_loss_take_profit("AAPL", port)
        assert trigger == "stop_loss"

    def test_take_profit_triggered(self):
        rm = RiskManager(take_profit_pct=15.0)
        pos = MagicMock()
        pos.quantity = 10
        pos.avg_entry_price = 100.0
        pos.current_price = 120.0  # +20% → trigger
        port = MagicMock()
        port.get_position.return_value = pos
        trigger = rm.check_stop_loss_take_profit("AAPL", port)
        assert trigger == "take_profit"

    def test_no_trigger_in_normal_range(self):
        rm = RiskManager(stop_loss_pct=5.0, take_profit_pct=15.0)
        pos = MagicMock()
        pos.quantity = 10
        pos.avg_entry_price = 100.0
        pos.current_price = 105.0  # +5% — within range
        port = MagicMock()
        port.get_position.return_value = pos
        trigger = rm.check_stop_loss_take_profit("AAPL", port)
        assert trigger is None

    def test_halted_trading_blocks_all_orders(self):
        rm = RiskManager()
        rm.force_halt("manual test halt")
        port = _make_portfolio()
        order = _make_order()
        decision = rm.check_order(order, price=100.0, portfolio=port)
        assert not decision.allowed

    def test_reset_halt(self):
        rm = RiskManager()
        rm.force_halt("test")
        assert rm.is_halted
        rm.reset_halt()
        assert not rm.is_halted
        port = _make_portfolio()
        decision = rm.check_order(_make_order(), price=100.0, portfolio=port)
        assert decision.allowed
