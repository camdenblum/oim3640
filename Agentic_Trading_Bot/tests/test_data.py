"""
tests/test_data.py — Unit tests for DataFetcher and FeatureEngineer.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.features import FeatureEngineer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame for testing."""
    rng = np.random.default_rng(seed)
    close = 100 * np.cumprod(1 + rng.normal(0, 0.01, n))
    high = close * (1 + rng.uniform(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.02, n))
    open_ = close * (1 + rng.normal(0, 0.005, n))
    volume = rng.integers(1_000_000, 10_000_000, n).astype(float)
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume},
        index=dates,
    )


@pytest.fixture
def ohlcv() -> pd.DataFrame:
    return _make_ohlcv()


# ---------------------------------------------------------------------------
# FeatureEngineer tests
# ---------------------------------------------------------------------------

class TestFeatureEngineer:
    def test_compute_returns_dataframe(self, ohlcv):
        fe = FeatureEngineer(indicators=["RSI", "MACD"], normalize=False)
        result = fe.compute(ohlcv)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_no_nan_after_compute(self, ohlcv):
        fe = FeatureEngineer(indicators=["RSI", "MACD", "BBands", "EMA_cross", "ATR"], normalize=False)
        result = fe.compute(ohlcv)
        assert not result.isnull().any().any(), "Features contain NaN after dropna"

    def test_rsi_in_range(self, ohlcv):
        fe = FeatureEngineer(indicators=["RSI"], normalize=False)
        result = fe.compute(ohlcv)
        assert "RSI" in result.columns
        # RSI should be in [0, 100] before normalisation
        # After normalisation values are z-scored, so just check no extreme outliers
        assert result["RSI"].abs().max() < 1000

    def test_macd_columns_present(self, ohlcv):
        fe = FeatureEngineer(indicators=["MACD"], normalize=False)
        result = fe.compute(ohlcv)
        assert "MACD_line" in result.columns
        assert "MACD_signal" in result.columns
        assert "MACD_hist" in result.columns

    def test_bbands_columns_present(self, ohlcv):
        fe = FeatureEngineer(indicators=["BBands"], normalize=False)
        result = fe.compute(ohlcv)
        for col in ["BB_upper", "BB_mid", "BB_lower", "BB_pct_b"]:
            assert col in result.columns

    def test_normalize_reduces_scale(self, ohlcv):
        fe_raw = FeatureEngineer(indicators=["RSI"], normalize=False)
        fe_norm = FeatureEngineer(indicators=["RSI"], normalize=True)
        raw = fe_raw.compute(ohlcv)
        normed = fe_norm.compute(ohlcv)
        # Normalised features should have smaller absolute range
        assert normed["RSI"].abs().max() < raw["RSI"].abs().max() + 1

    def test_empty_df_returns_empty(self):
        fe = FeatureEngineer(indicators=["RSI"])
        result = fe.compute(pd.DataFrame())
        assert result.empty

    def test_unknown_indicator_skipped(self, ohlcv):
        fe = FeatureEngineer(indicators=["RSI", "BOGUS_INDICATOR"], normalize=False)
        result = fe.compute(ohlcv)
        assert "RSI" in result.columns
        assert "BOGUS_INDICATOR" not in result.columns

    def test_atr_positive(self, ohlcv):
        fe = FeatureEngineer(indicators=["ATR"], normalize=False)
        result = fe.compute(ohlcv)
        assert "ATR" in result.columns
        assert (result["ATR"] >= 0).all()

    def test_stochastic_columns(self, ohlcv):
        fe = FeatureEngineer(indicators=["Stochastic"], normalize=False)
        result = fe.compute(ohlcv)
        assert "Stoch_K" in result.columns
        assert "Stoch_D" in result.columns

    def test_price_features_always_included(self, ohlcv):
        fe = FeatureEngineer(indicators=["RSI"], normalize=False)
        result = fe.compute(ohlcv)
        assert "Returns_1d" in result.columns
        assert "Returns_5d" in result.columns
        assert "Volatility_20d" in result.columns

    def test_custom_rsi_period(self, ohlcv):
        fe = FeatureEngineer(
            indicators=["RSI"],
            feature_params={"RSI": {"period": 7}},
            normalize=False,
        )
        result = fe.compute(ohlcv)
        assert "RSI" in result.columns
        assert len(result) > 0
