"""
tests/test_strategy.py — Unit tests for the Strategy and Learner.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.strategy import Action, Signal, Strategy


def _make_feature_df(n: int = 100, n_features: int = 8, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data = rng.standard_normal((n, n_features))
    dates = pd.date_range("2022-01-01", periods=n, freq="B")
    cols = [f"feat_{i}" for i in range(n_features)]
    return pd.DataFrame(data, index=dates, columns=cols)


class TestStrategy:
    def test_generate_signals_returns_list(self):
        strat = Strategy(scoring_model="linear")
        feat = {"AAPL": _make_feature_df()}
        signals = strat.generate_signals(feat, timestamp="2024-01-01")
        assert isinstance(signals, list)
        assert len(signals) == 1

    def test_signal_has_valid_action(self):
        strat = Strategy(scoring_model="linear")
        feat = {"AAPL": _make_feature_df()}
        signals = strat.generate_signals(feat)
        assert signals[0].action in Action.__members__.values()

    def test_signal_score_in_range(self):
        strat = Strategy(scoring_model="linear")
        feat = {"AAPL": _make_feature_df()}
        for _ in range(10):
            signals = strat.generate_signals(feat)
            score = signals[0].score
            assert 0.0 <= score <= 1.0

    def test_buy_threshold_respected(self):
        strat = Strategy(scoring_model="linear", buy_threshold=0.99, sell_threshold=0.01)
        # With buy_threshold=0.99, almost all random scores should be HOLD
        feat = {"AAPL": _make_feature_df(seed=1)}
        signals = strat.generate_signals(feat)
        # Allow BUY or HOLD — just not SELL at score > 0.01
        assert signals[0].action in (Action.BUY, Action.HOLD)

    def test_multiple_tickers(self):
        strat = Strategy(scoring_model="linear")
        feat = {t: _make_feature_df(seed=i) for i, t in enumerate(["AAPL", "MSFT", "NVDA"])}
        signals = strat.generate_signals(feat)
        assert len(signals) == 3
        tickers = {s.ticker for s in signals}
        assert tickers == {"AAPL", "MSFT", "NVDA"}

    def test_empty_feature_df_skipped(self):
        strat = Strategy(scoring_model="linear")
        feat = {"AAPL": pd.DataFrame()}
        signals = strat.generate_signals(feat)
        assert len(signals) == 0

    def test_nan_feature_df_skipped(self):
        strat = Strategy(scoring_model="linear")
        df = _make_feature_df()
        df.iloc[:, :] = np.nan
        feat = {"AAPL": df}
        signals = strat.generate_signals(feat)
        assert len(signals) == 0

    def test_score_series_length_matches_input(self):
        strat = Strategy(scoring_model="linear")
        feat_df = _make_feature_df(n=50)
        scores = strat.score_series(feat_df)
        assert len(scores) == len(feat_df)

    def test_get_set_scorer_params_roundtrip(self):
        strat = Strategy(scoring_model="linear")
        feat = {"AAPL": _make_feature_df()}
        strat.generate_signals(feat)  # triggers weight initialisation
        params = strat.get_scorer_params()
        original_weights = list(params["weights"])

        # Modify params
        params["weights"] = [w * 2 for w in params["weights"]]
        strat.set_scorer_params(params)

        new_params = strat.get_scorer_params()
        assert new_params["weights"] != original_weights

    def test_tree_model_returns_signals(self):
        strat = Strategy(scoring_model="tree")
        feat = {"AAPL": _make_feature_df()}
        # Tree model not yet trained — should return neutral 0.5 → HOLD
        signals = strat.generate_signals(feat)
        assert len(signals) == 1
        assert signals[0].action == Action.HOLD  # unfitted tree returns 0.5 → HOLD

    def test_signal_confidence_proportional_to_distance(self):
        strat = Strategy(scoring_model="linear", buy_threshold=0.6, sell_threshold=0.4)
        feat = {"AAPL": _make_feature_df()}
        signals = strat.generate_signals(feat)
        s = signals[0]
        # confidence = |score - 0.5|
        assert abs(s.confidence - abs(s.score - 0.5)) < 1e-6
