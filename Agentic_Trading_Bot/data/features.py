"""
data/features.py — Technical indicator feature engineering.

Computes a fixed set of indicators from raw OHLCV DataFrames and returns a
feature matrix ready for the strategy scoring model.

All computations are pure pandas/numpy — no TA-Lib dependency required.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Compute technical indicator features from OHLCV data.

    Args:
        indicators: List of indicator names to compute, e.g. ["RSI", "MACD"].
        feature_params: Dict of per-indicator parameter overrides.
        normalize: If True, z-score normalise each feature column.
    """

    def __init__(
        self,
        indicators: List[str] | None = None,
        feature_params: Dict[str, Any] | None = None,
        normalize: bool = True,
    ) -> None:
        self.indicators = indicators or ["RSI", "MACD", "BBands", "EMA_cross", "ATR", "MOM", "ROC"]
        self.feature_params = feature_params or {}
        self.normalize = normalize

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a DataFrame of features aligned to *df*'s index.

        NaN rows at the start (due to lookback periods) are dropped.

        Args:
            df: OHLCV DataFrame with columns Open/High/Low/Close/Volume.

        Returns:
            Feature DataFrame with one row per bar; leading NaN rows removed.
        """
        if df.empty or "Close" not in df.columns:
            logger.warning("Empty or missing Close column — returning empty features")
            return pd.DataFrame(index=df.index)

        feat = pd.DataFrame(index=df.index)

        dispatch = {
            "RSI": self._rsi,
            "MACD": self._macd,
            "BBands": self._bbands,
            "EMA_cross": self._ema_cross,
            "ATR": self._atr,
            "Stochastic": self._stochastic,
            "MOM": self._mom,
            "ROC": self._roc,
        }

        for ind in self.indicators:
            if ind not in dispatch:
                logger.warning("Unknown indicator, skipping", extra={"indicator": ind})
                continue
            try:
                result = dispatch[ind](df)
                if isinstance(result, pd.Series):
                    feat[ind] = result
                else:
                    feat = pd.concat([feat, result], axis=1)
            except Exception as exc:
                logger.warning("Error computing indicator", extra={"indicator": ind, "error": str(exc)})

        # Add price-derived features always
        feat = pd.concat([feat, self._price_features(df)], axis=1)

        # Add volume feature
        if "Volume" in df.columns:
            feat["Vol_zscore"] = self._zscore(df["Volume"])

        # Drop leading NaN rows (from lookback periods)
        feat = feat.dropna()

        if self.normalize:
            feat = self._normalize_df(feat)

        logger.debug("Features computed", extra={"shape": str(feat.shape)})
        return feat

    def feature_names(self) -> List[str]:
        """Return expected feature column names (approximate — call compute for exact list)."""
        names: List[str] = []
        for ind in self.indicators:
            if ind == "MACD":
                names += ["MACD_line", "MACD_signal", "MACD_hist"]
            elif ind == "BBands":
                names += ["BB_upper", "BB_mid", "BB_lower", "BB_pct_b"]
            elif ind == "EMA_cross":
                names += ["EMA_fast", "EMA_slow", "EMA_diff"]
            elif ind == "Stochastic":
                names += ["Stoch_K", "Stoch_D"]
            else:
                names.append(ind)
        names += ["Returns_1d", "Returns_5d", "Volatility_20d", "Vol_zscore"]
        return names

    # ------------------------------------------------------------------
    # Indicator implementations
    # ------------------------------------------------------------------

    def _rsi(self, df: pd.DataFrame) -> pd.Series:
        period = self.feature_params.get("RSI", {}).get("period", 14)
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
        avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)
        return rsi.rename("RSI")

    def _macd(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.feature_params.get("MACD", {})
        fast = p.get("fast", 12)
        slow = p.get("slow", 26)
        sig = p.get("signal", 9)
        ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=sig, adjust=False).mean()
        hist = macd_line - signal_line
        return pd.DataFrame(
            {"MACD_line": macd_line, "MACD_signal": signal_line, "MACD_hist": hist},
            index=df.index,
        )

    def _bbands(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.feature_params.get("BBands", {})
        period = p.get("period", 20)
        std_dev = p.get("std_dev", 2.0)
        mid = df["Close"].rolling(window=period).mean()
        std = df["Close"].rolling(window=period).std()
        upper = mid + std_dev * std
        lower = mid - std_dev * std
        band_width = upper - lower
        pct_b = (df["Close"] - lower) / band_width.replace(0, np.nan)
        return pd.DataFrame(
            {"BB_upper": upper, "BB_mid": mid, "BB_lower": lower, "BB_pct_b": pct_b},
            index=df.index,
        )

    def _ema_cross(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.feature_params.get("EMA_cross", {})
        fast = p.get("fast", 9)
        slow = p.get("slow", 21)
        ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
        diff = (ema_fast - ema_slow) / ema_slow.replace(0, np.nan)
        return pd.DataFrame(
            {"EMA_fast": ema_fast, "EMA_slow": ema_slow, "EMA_diff": diff},
            index=df.index,
        )

    def _atr(self, df: pd.DataFrame) -> pd.Series:
        period = self.feature_params.get("ATR", {}).get("period", 14)
        high = df.get("High", df["Close"])
        low = df.get("Low", df["Close"])
        prev_close = df["Close"].shift(1)
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
        ).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()
        # Normalise ATR as % of close
        return (atr / df["Close"]).rename("ATR")

    def _stochastic(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.feature_params.get("Stochastic", {})
        k_period = p.get("k_period", 14)
        d_period = p.get("d_period", 3)
        high = df.get("High", df["Close"])
        low = df.get("Low", df["Close"])
        low_min = low.rolling(window=k_period).min()
        high_max = high.rolling(window=k_period).max()
        denom = (high_max - low_min).replace(0, np.nan)
        k = 100 * (df["Close"] - low_min) / denom
        d = k.rolling(window=d_period).mean()
        return pd.DataFrame({"Stoch_K": k, "Stoch_D": d}, index=df.index)

    def _mom(self, df: pd.DataFrame) -> pd.Series:
        period = self.feature_params.get("MOM", {}).get("period", 10)
        mom = df["Close"].diff(period)
        return mom.rename("MOM")

    def _roc(self, df: pd.DataFrame) -> pd.Series:
        period = self.feature_params.get("ROC", {}).get("period", 10)
        roc = df["Close"].pct_change(periods=period) * 100
        return roc.rename("ROC")

    def _price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        ret_1 = df["Close"].pct_change(1).rename("Returns_1d")
        ret_5 = df["Close"].pct_change(5).rename("Returns_5d")
        vol_20 = df["Close"].pct_change().rolling(20).std().rename("Volatility_20d")
        return pd.concat([ret_1, ret_5, vol_20], axis=1)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _zscore(series: pd.Series, window: int = 20) -> pd.Series:
        """Rolling z-score normalisation."""
        mean = series.rolling(window).mean()
        std = series.rolling(window).std()
        return (series - mean) / std.replace(0, np.nan)

    @staticmethod
    def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
        """Z-score normalise all columns using their own mean/std (in-sample).
        For live use this should be replaced with rolling stats from training data."""
        means = df.mean()
        stds = df.std().replace(0, 1)
        return (df - means) / stds
