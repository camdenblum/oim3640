"""
tests/test_state.py — Unit tests for TraderState (SQLite persistence).
"""
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from state.trader_state import TraderState


@pytest.fixture
def state(tmp_path):
    db = str(tmp_path / "test.db")
    return TraderState(db_path=db, mode="paper")


class TestTraderState:
    def test_log_and_retrieve_trade(self, state):
        state.log_trade(
            symbol="AAPL", side="BUY", quantity=10, filled_price=150.0,
            pnl=0.0, reason="test trade"
        )
        trades = state.get_trades(symbol="AAPL")
        assert len(trades) == 1
        assert trades[0]["symbol"] == "AAPL"
        assert trades[0]["side"] == "BUY"
        assert trades[0]["quantity"] == 10

    def test_multiple_trades(self, state):
        for i in range(5):
            state.log_trade(symbol="MSFT", side="BUY", quantity=float(i + 1), filled_price=300.0)
        trades = state.get_trades(symbol="MSFT")
        assert len(trades) == 5

    def test_filter_by_symbol(self, state):
        state.log_trade(symbol="AAPL", side="BUY", quantity=10, filled_price=150.0)
        state.log_trade(symbol="MSFT", side="BUY", quantity=5, filled_price=300.0)
        aapl_trades = state.get_trades(symbol="AAPL")
        assert all(t["symbol"] == "AAPL" for t in aapl_trades)

    def test_performance_snapshot(self, state):
        metrics = {
            "equity": 110_000.0,
            "cash": 50_000.0,
            "realised_pnl": 5_000.0,
            "unrealised_pnl": 5_000.0,
            "total_return_pct": 10.0,
            "max_drawdown_pct": 2.0,
            "sharpe_ratio": 1.2,
            "win_rate_pct": 60.0,
            "open_positions": 3,
            "total_trades": 10,
        }
        state.save_performance_snapshot(metrics)
        history = state.get_performance_history()
        assert len(history) >= 1
        assert abs(history[-1]["equity"] - 110_000.0) < 0.01

    def test_audit_log(self, state):
        state.audit("bot_start", "Bot started", extra={"mode": "paper"})
        # No error → success

    def test_checkpoint_metadata(self, state):
        state.record_checkpoint(
            tag="test_v1", model_name="linear", path="/tmp/ckpt.json",
            train_accuracy=0.65, val_accuracy=0.60
        )
        tag = state.get_latest_checkpoint_tag()
        assert tag == "test_v1"

    def test_export_trades_csv(self, state, tmp_path):
        state.log_trade(symbol="AAPL", side="BUY", quantity=10, filled_price=150.0)
        csv_path = str(tmp_path / "trades.csv")
        state.export_trades_csv(csv_path)
        assert Path(csv_path).exists()

    def test_limit_on_get_trades(self, state):
        for i in range(20):
            state.log_trade(symbol="AAPL", side="BUY", quantity=1.0, filled_price=100.0)
        trades = state.get_trades(limit=5)
        assert len(trades) <= 5
