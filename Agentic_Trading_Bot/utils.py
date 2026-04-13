"""
utils.py — Shared helpers: config loading, structured logging, time utilities.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

_config_cache: dict[str, Any] | None = None


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Load and cache config.yaml.  Environment variable overrides are NOT applied
    here — broker credentials are fetched at broker-init time via get_env()."""
    global _config_cache
    if _config_cache is None:
        with open(path, "r") as f:
            _config_cache = yaml.safe_load(f)
    return _config_cache


def reload_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Force-reload config from disk."""
    global _config_cache
    _config_cache = None
    return load_config(path)


def get_env(key: str, default: str | None = None, required: bool = False) -> str | None:
    """Fetch an environment variable with an optional default.

    Args:
        key: Environment variable name.
        default: Fallback value if not set.
        required: Raise if missing and no default.
    """
    val = os.environ.get(key, default)
    if required and val is None:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            "Add it to your shell or .env file."
        )
    return val


# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Attach any extra fields added via logger.info("...", extra={...})
        for key, val in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs", "message",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName", "exc_info", "exc_text",
            ):
                payload[key] = val
        return json.dumps(payload, default=str)


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    log_dir: str = ".logs",
) -> None:
    """Configure root logger.  Call once at startup."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates on re-init
    root.handlers.clear()

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(numeric_level)
    if log_format == "json":
        ch.setFormatter(_JsonFormatter())
    else:
        ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s — %(message)s"))
    root.addHandler(ch)

    # File handler (always JSON for audit trail)
    log_file = Path(log_dir) / "bot.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(numeric_level)
    fh.setFormatter(_JsonFormatter())
    root.addHandler(fh)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (call after setup_logging)."""
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def now_iso() -> str:
    return utcnow().isoformat()


def timestamp_ms() -> int:
    return int(time.time() * 1000)


def trading_day_str(dt: datetime | None = None) -> str:
    """Return YYYY-MM-DD string for the given (or current) datetime."""
    return (dt or utcnow()).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
