"""
tests/test_portfolio.py — Unit tests for the Portfolio.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.broker_api import Order, OrderSide, OrderStatus, OrderType
from portfolio.portfolio import Portfolio


def _filled_order(
    symbol: str = "AAPL",
    side: OrderSide = OrderSide.BUY,
    qty: float = 10.0,
    price: float = 150.0,
    commission: float = 0.0,
    slippage: float = 0.0,
) -> Order:
    order = Order(
        symbol=symbol,
        side=side,
        quantity=qty,
        order_type=OrderType.MARKET,
        order_id="test-001",
        status=OrderStatus.FILLED,
        filled_qty=qty,
        filled_avg_price=price,
        commission=commission,
        slippage=slippage,
    )
    return order


class TestPortfolio:
    def test_initial_state(self):
        port = Portfolio(initial_cash=100_000.0)
        assert port.cash == 100_000.0
        assert port.equity == 100_000.0
        assert port.market_value == 0.0
        assert len(port.positions) == 0

    def test_buy_reduces_cash(self):
        port = Portfolio(initial_cash=100_000.0)
        order = _filled_order(qty=10, price=150.0)
        port.apply_fill(order)
        expected_cash = 100_000.0 - 10 * 150.0
        assert abs(port.cash - expected_cash) < 0.01

    def test_buy_creates_position(self):
        port = Portfolio(initial_cash=100_000.0)
        port.apply_fill(_filled_order(symbol="AAPL", qty=10, price=150.0))
        assert "AAPL" in port.positions
        assert port.positions["AAPL"].quantity == 10
        assert port.positions["AAPL"].avg_entry_price == 150.0

    def test_sell_closes_position(self):
        port = Portfolio(initial_cash=100_000.0)
        port.apply_fill(_filled_order(symbol="AAPL", qty=10, price=150.0))
        port.apply_fill(_filled_order(symbol="AAPL", side=OrderSide.SELL, qty=10, price=160.0))
        assert "AAPL" not in port.positions

    def test_sell_realises_pnl(self):
        port = Portfolio(initial_cash=100_000.0)
        port.apply_fill(_filled_order(symbol="AAPL", qty=10, price=150.0))
        port.apply_fill(_filled_order(symbol="AAPL", side=OrderSide.SELL, qty=10, price=160.0))
        assert port.realised_pnl == pytest.approx(10 * (160.0 - 150.0), abs=0.01)

    def test_commission_reduces_pnl(self):
        port = Portfolio(initial_cash=100_000.0)
        port.apply_fill(_filled_order(qty=10, price=150.0, commission=5.0))
        port.apply_fill(_filled_order(side=OrderSide.SELL, qty=10, price=160.0, commission=5.0))
        expected_pnl = 10 * (160 - 150) - 5 - 5
        assert port.realised_pnl == pytest.approx(expected_pnl, abs=0.01)

    def test_weighted_avg_entry_on_double_buy(self):
        port = Portfolio(initial_cash=200_000.0)
        port.apply_fill(_filled_order(qty=10, price=100.0))
        port.apply_fill(_filled_order(qty=10, price=120.0))
        expected_avg = (10 * 100 + 10 * 120) / 20
        assert port.positions["AAPL"].avg_entry_price == pytest.approx(expected_avg, abs=0.01)

    def test_update_prices_changes_market_value(self):
        port = Portfolio(initial_cash=100_000.0)
        port.apply_fill(_filled_order(qty=10, price=150.0))
        port.update_prices({"AAPL": 200.0})
        assert port.market_value == pytest.approx(10 * 200.0, abs=0.01)

    def test_equity_equals_cash_plus_market_value(self):
        port = Portfolio(initial_cash=100_000.0)
        port.apply_fill(_filled_order(qty=10, price=150.0))
        port.update_prices({"AAPL": 170.0})
        assert port.equity == pytest.approx(port.cash + port.market_value, abs=0.01)

    def test_summary_contains_expected_keys(self):
        port = Portfolio(initial_cash=100_000.0)
        summary = port.summary()
        for key in ("equity", "cash", "total_return_pct", "max_drawdown_pct", "sharpe_ratio"):
            assert key in summary

    def test_compute_order_size_percent_of_equity(self):
        port = Portfolio(initial_cash=100_000.0, sizing_method="percent_of_equity", default_pct=0.05)
        qty = port.compute_order_size("AAPL", price=100.0, confidence=0.0)
        # 5% of 100k = $5,000 / $100 = 50 shares
        assert qty == pytest.approx(50.0, abs=5)

    def test_compute_order_size_respects_cash(self):
        port = Portfolio(initial_cash=1_000.0, sizing_method="percent_of_equity", default_pct=0.5)
        qty = port.compute_order_size("AAPL", price=100.0)
        # Can't spend more than available cash
        assert qty * 100 <= port.cash

    def test_zero_quantity_fill_ignored(self):
        port = Portfolio(initial_cash=100_000.0)
        cash_before = port.cash
        order = _filled_order(qty=0, price=150.0)
        port.apply_fill(order)
        assert port.cash == cash_before

    def test_win_rate_calculation(self):
        port = Portfolio(initial_cash=300_000.0)
        # 3 wins, 1 loss
        for price_out in [160, 155, 170, 140]:
            port.apply_fill(_filled_order(qty=10, price=150.0))
            port.apply_fill(_filled_order(side=OrderSide.SELL, qty=10, price=float(price_out)))
        summary = port.summary()
        assert summary["win_rate_pct"] == pytest.approx(75.0, abs=0.1)
