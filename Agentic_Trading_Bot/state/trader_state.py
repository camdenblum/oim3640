"""
state/trader_state.py — Persistent state management using SQLite.

Stores:
  - Full trade history (for compliance and learning)
  - Daily performance snapshots
  - Model checkpoint metadata
  - Audit log entries

All writes are append-only for auditability.  Use export_trades() to dump
to CSV/Parquet for external analysis.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    side        TEXT NOT NULL,
    quantity    REAL NOT NULL,
    entry_price REAL,
    exit_price  REAL,
    filled_price REAL,
    pnl         REAL,
    commission  REAL,
    slippage    REAL,
    signal_score REAL,
    reason      TEXT,
    order_id    TEXT,
    mode        TEXT DEFAULT 'paper',
    extra_json  TEXT
);

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    date        TEXT NOT NULL,
    equity      REAL,
    cash        REAL,
    realised_pnl REAL,
    unrealised_pnl REAL,
    total_return_pct REAL,
    max_drawdown_pct REAL,
    sharpe_ratio REAL,
    win_rate_pct REAL,
    open_positions INTEGER,
    total_trades INTEGER,
    extra_json  TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    symbol      TEXT,
    description TEXT,
    extra_json  TEXT
);

CREATE TABLE IF NOT EXISTS model_checkpoints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    tag         TEXT NOT NULL UNIQUE,
    model_name  TEXT,
    train_accuracy REAL,
    val_accuracy REAL,
    path        TEXT,
    extra_json  TEXT
);
"""


class TraderState:
    """SQLite-backed persistent state store for the trading bot.

    Args:
        db_path: Path to the SQLite database file.
        mode: "paper" or "live" — recorded on each trade.
    """

    def __init__(self, db_path: str = ".state/trader.db", mode: str = "paper") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self._init_db()

    # ------------------------------------------------------------------
    # Context manager for connections
    # ------------------------------------------------------------------

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _init_db(self) -> None:
        with self._conn() as con:
            con.executescript(_SCHEMA)
        logger.debug("Database initialised", extra={"path": str(self.db_path)})

    # ------------------------------------------------------------------
    # Trade logging
    # ------------------------------------------------------------------

    def log_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        filled_price: float,
        pnl: float = 0.0,
        commission: float = 0.0,
        slippage: float = 0.0,
        signal_score: float = 0.0,
        reason: str = "",
        order_id: str = "",
        entry_price: float = 0.0,
        exit_price: float = 0.0,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        ts = _utcnow()
        with self._conn() as con:
            con.execute(
                """INSERT INTO trades
                   (timestamp, symbol, side, quantity, entry_price, exit_price,
                    filled_price, pnl, commission, slippage, signal_score,
                    reason, order_id, mode, extra_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    ts, symbol, side, quantity, entry_price, exit_price,
                    filled_price, pnl, commission, slippage, signal_score,
                    reason, order_id, self.mode,
                    json.dumps(extra or {}),
                ),
            )
        logger.debug("Trade logged", extra={"symbol": symbol, "side": side, "qty": quantity})

    def get_trades(
        self,
        symbol: Optional[str] = None,
        limit: int = 1000,
        since: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve trade records from the database.

        Args:
            symbol: Filter by ticker (None = all).
            limit: Maximum number of rows.
            since: ISO timestamp lower bound.
        """
        clauses = []
        params: List[Any] = []
        if symbol:
            clauses.append("symbol = ?")
            params.append(symbol)
        if since:
            clauses.append("timestamp >= ?")
            params.append(since)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit)
        with self._conn() as con:
            rows = con.execute(
                f"SELECT * FROM trades {where} ORDER BY id DESC LIMIT ?", params
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Performance snapshots
    # ------------------------------------------------------------------

    def save_performance_snapshot(self, metrics: Dict[str, Any]) -> None:
        ts = _utcnow()
        with self._conn() as con:
            con.execute(
                """INSERT INTO performance_snapshots
                   (timestamp, date, equity, cash, realised_pnl, unrealised_pnl,
                    total_return_pct, max_drawdown_pct, sharpe_ratio, win_rate_pct,
                    open_positions, total_trades, extra_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    ts, ts[:10],
                    metrics.get("equity"),
                    metrics.get("cash"),
                    metrics.get("realised_pnl"),
                    metrics.get("unrealised_pnl"),
                    metrics.get("total_return_pct"),
                    metrics.get("max_drawdown_pct"),
                    metrics.get("sharpe_ratio"),
                    metrics.get("win_rate_pct"),
                    metrics.get("open_positions"),
                    metrics.get("total_trades"),
                    json.dumps({k: v for k, v in metrics.items()
                                if k not in ("equity", "cash", "realised_pnl",
                                             "unrealised_pnl", "total_return_pct",
                                             "max_drawdown_pct", "sharpe_ratio",
                                             "win_rate_pct", "open_positions",
                                             "total_trades")}),
                ),
            )

    def get_performance_history(self, days: int = 30) -> List[Dict[str, Any]]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT * FROM performance_snapshots ORDER BY id DESC LIMIT ?", (days,)
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    # ------------------------------------------------------------------
    # Audit logging
    # ------------------------------------------------------------------

    def audit(
        self,
        event_type: str,
        description: str,
        symbol: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        ts = _utcnow()
        with self._conn() as con:
            con.execute(
                """INSERT INTO audit_log (timestamp, event_type, symbol, description, extra_json)
                   VALUES (?,?,?,?,?)""",
                (ts, event_type, symbol, description, json.dumps(extra or {})),
            )

    # ------------------------------------------------------------------
    # Model checkpoint metadata
    # ------------------------------------------------------------------

    def record_checkpoint(
        self,
        tag: str,
        model_name: str,
        path: str,
        train_accuracy: float = 0.0,
        val_accuracy: float = 0.0,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        ts = _utcnow()
        with self._conn() as con:
            con.execute(
                """INSERT OR REPLACE INTO model_checkpoints
                   (timestamp, tag, model_name, train_accuracy, val_accuracy, path, extra_json)
                   VALUES (?,?,?,?,?,?,?)""",
                (ts, tag, model_name, train_accuracy, val_accuracy, path, json.dumps(extra or {})),
            )
        logger.info("Checkpoint recorded", extra={"tag": tag, "path": path})

    def get_latest_checkpoint_tag(self) -> Optional[str]:
        with self._conn() as con:
            row = con.execute(
                "SELECT tag FROM model_checkpoints ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row["tag"] if row else None

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_trades_csv(self, path: str) -> None:
        """Export all trades to a CSV file."""
        try:
            import pandas as pd
            trades = self.get_trades(limit=100_000)
            if trades:
                pd.DataFrame(trades).to_csv(path, index=False)
                logger.info("Trades exported", extra={"path": path, "rows": len(trades)})
        except ImportError:
            import csv
            trades = self.get_trades(limit=100_000)
            if trades:
                with open(path, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=trades[0].keys())
                    writer.writeheader()
                    writer.writerows(trades)
                logger.info("Trades exported (csv)", extra={"path": path})

    def prune_old_data(self, retention_days: int = 180) -> None:
        """Delete records older than *retention_days* days."""
        cutoff = datetime.now(tz=timezone.utc)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        with self._conn() as con:
            for table in ("trades", "performance_snapshots", "audit_log"):
                con.execute(
                    f"DELETE FROM {table} WHERE date(timestamp) < date(?, '-{retention_days} days')",
                    (cutoff_str,),
                )
        logger.info("Old data pruned", extra={"retention_days": retention_days})


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()
