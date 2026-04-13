"""
data/fetcher.py — yfinance data fetcher with local disk caching and retry/backoff.

Responsibility:
  - Download OHLCV data for a list of tickers and a date range.
  - Cache results locally so repeated runs don't hammmer the API.
  - Handle missing data gracefully (forward-fill, then drop leading NaNs).
  - Expose a clean DataFrame interface to the rest of the bot.
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Columns we care about from yfinance
_OHLCV_COLS = ["Open", "High", "Low", "Close", "Volume"]


class DataFetcher:
    """Downloads and caches historical OHLCV data via yfinance.

    Args:
        cache_dir: Directory where Parquet cache files are stored.
        max_retries: Number of download attempts before raising.
        retry_backoff: Seconds between retries (doubled each attempt).
    """

    def __init__(
        self,
        cache_dir: str = ".cache/data",
        max_retries: int = 3,
        retry_backoff: float = 2.0,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(
        self,
        ticker: str,
        start: str | date | datetime,
        end: str | date | datetime | None = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Return a cleaned OHLCV DataFrame for *ticker* over [start, end].

        Args:
            ticker: Stock symbol, e.g. "AAPL".
            start: Start date (inclusive), "YYYY-MM-DD" or date object.
            end: End date (exclusive). Defaults to today.
            interval: yfinance interval string ("1d", "60m", etc.).
            use_cache: If True, read from / write to disk cache.

        Returns:
            DataFrame with DatetimeIndex and columns Open/High/Low/Close/Volume.
            Index is UTC-aware for intraday data, tz-naive for daily.
        """
        end = end or date.today()
        start_str = str(start)[:10]
        end_str = str(end)[:10]

        cache_key = self._cache_key(ticker, start_str, end_str, interval)
        cache_path = self.cache_dir / f"{cache_key}.parquet"

        if use_cache and cache_path.exists():
            logger.debug("Cache hit", extra={"ticker": ticker, "path": str(cache_path)})
            return pd.read_parquet(cache_path)

        df = self._download_with_retry(ticker, start_str, end_str, interval)
        df = self._clean(df, ticker)

        if use_cache:
            df.to_parquet(cache_path)
            logger.debug("Cached", extra={"ticker": ticker, "path": str(cache_path)})

        return df

    def fetch_multi(
        self,
        tickers: List[str],
        start: str | date,
        end: str | date | None = None,
        interval: str = "1d",
        use_cache: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple tickers; returns {ticker: DataFrame}."""
        results: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            try:
                results[ticker] = self.fetch(ticker, start, end, interval, use_cache)
            except Exception as exc:
                logger.warning(
                    "Failed to fetch ticker, skipping",
                    extra={"ticker": ticker, "error": str(exc)},
                )
        return results

    def fetch_latest_close(self, ticker: str) -> Optional[float]:
        """Return the most recent closing price (today or last trading day)."""
        try:
            df = self.fetch(
                ticker,
                start=str(date.today() - timedelta(days=7)),
                use_cache=False,
            )
            if df.empty:
                return None
            return float(df["Close"].iloc[-1])
        except Exception as exc:
            logger.warning("Could not fetch latest close", extra={"ticker": ticker, "error": str(exc)})
            return None

    def invalidate_cache(self, ticker: str | None = None) -> None:
        """Delete cached files for *ticker* (or all if None)."""
        pattern = f"{ticker}_*.parquet" if ticker else "*.parquet"
        for p in self.cache_dir.glob(pattern):
            p.unlink()
            logger.info("Invalidated cache", extra={"file": str(p)})

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _download_with_retry(
        self, ticker: str, start: str, end: str, interval: str
    ) -> pd.DataFrame:
        """Call yfinance with exponential backoff on failure."""
        backoff = self.retry_backoff
        last_exc: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "Downloading",
                    extra={"ticker": ticker, "start": start, "end": end,
                           "interval": interval, "attempt": attempt},
                )
                df = yf.download(
                    ticker,
                    start=start,
                    end=end,
                    interval=interval,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )
                if df is not None and not df.empty:
                    return df
                logger.warning("Empty response from yfinance", extra={"ticker": ticker})
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Download error, retrying",
                    extra={"ticker": ticker, "error": str(exc), "attempt": attempt},
                )
            if attempt < self.max_retries:
                time.sleep(backoff)
                backoff *= 2

        raise RuntimeError(
            f"Failed to download {ticker} after {self.max_retries} attempts. "
            f"Last error: {last_exc}"
        )

    def _clean(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Standardise column names, handle NaNs, and validate data quality."""
        # yfinance multi-level columns when downloading one ticker can appear
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Keep only OHLCV columns that exist
        available = [c for c in _OHLCV_COLS if c in df.columns]
        df = df[available].copy()

        if df.empty:
            logger.warning("No OHLCV columns found after cleaning", extra={"ticker": ticker})
            return df

        # Forward-fill small gaps (weekends / holidays already excluded by yfinance)
        df = df.ffill()

        # Drop rows where Close is still NaN after ffill (leading rows)
        df = df.dropna(subset=["Close"])

        # Ensure index is a proper DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        df.sort_index(inplace=True)
        df.index.name = "Date"

        logger.info(
            "Fetched data",
            extra={"ticker": ticker, "rows": len(df),
                   "from": str(df.index[0])[:10], "to": str(df.index[-1])[:10]},
        )
        return df

    @staticmethod
    def _cache_key(ticker: str, start: str, end: str, interval: str) -> str:
        raw = f"{ticker}_{start}_{end}_{interval}"
        return raw.replace("-", "").replace(":", "") + "_" + hashlib.md5(raw.encode()).hexdigest()[:6]
