"""
models/strategy.py — Signal generation and scoring engine.

Converts a feature matrix into BUY/SELL/HOLD signals with confidence scores.
Supports three scoring backends: linear weights, random-forest ensemble, and
a simple neural net (sklearn MLP).  The active backend is selected by config.

Output:
    List[Signal] — one Signal per ticker per bar.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signal types
# ---------------------------------------------------------------------------

class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    """A trading signal produced for one ticker at one point in time."""
    ticker: str
    action: Action
    score: float          # raw score in [0, 1]: high → bullish, low → bearish
    confidence: float     # how far from the neutral zone (0.5); in [0, 0.5]
    timestamp: str = ""
    features: Dict[str, float] = field(default_factory=dict)
    reason: str = ""      # human-readable summary of key drivers


# ---------------------------------------------------------------------------
# Scoring model wrappers
# ---------------------------------------------------------------------------

class _LinearScorer:
    """Weighted linear combination of features → score in (0, 1)."""

    def __init__(self, n_features: int, regularization: float = 0.01) -> None:
        rng = np.random.default_rng(42)
        # Initialise weights near zero; learner will update them
        self.weights = rng.normal(0, 0.01, n_features)
        self.bias = 0.0
        self.regularization = regularization

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return score in (0, 1) for each row via sigmoid."""
        logits = X @ self.weights + self.bias
        return _sigmoid(logits)

    def update(self, weights: np.ndarray, bias: float) -> None:
        self.weights = weights.copy()
        self.bias = bias

    def get_params(self) -> Dict[str, Any]:
        return {"weights": self.weights.tolist(), "bias": self.bias}

    def set_params(self, params: Dict[str, Any]) -> None:
        self.weights = np.array(params["weights"])
        self.bias = float(params.get("bias", 0.0))


class _TreeScorer:
    """Random-forest scorer (sklearn)."""

    def __init__(self, n_estimators: int = 100, max_depth: int = 5) -> None:
        from sklearn.ensemble import RandomForestClassifier
        self._clf = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1,
        )
        self._fitted = False

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            # Return neutral 0.5 until we have trained data
            return np.full(len(X), 0.5)
        return self._clf.predict_proba(X)[:, 1]  # P(class=1 = bullish)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._clf.fit(X, y)
        self._fitted = True

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {}
        import joblib, io
        buf = io.BytesIO()
        joblib.dump(self._clf, buf)
        return {"model_bytes": buf.getvalue().hex()}

    def set_params(self, params: Dict[str, Any]) -> None:
        if "model_bytes" not in params:
            return
        import joblib, io
        buf = io.BytesIO(bytes.fromhex(params["model_bytes"]))
        self._clf = joblib.load(buf)
        self._fitted = True


class _NeuralScorer:
    """MLP neural net scorer (sklearn)."""

    def __init__(self, hidden_layers: List[int] = (64, 32), dropout: float = 0.2) -> None:
        from sklearn.neural_network import MLPClassifier
        self._clf = MLPClassifier(
            hidden_layer_sizes=tuple(hidden_layers),
            activation="relu",
            solver="adam",
            alpha=0.001,
            max_iter=500,
            random_state=42,
        )
        self._fitted = False

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            return np.full(len(X), 0.5)
        return self._clf.predict_proba(X)[:, 1]

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self._clf.fit(X, y)
        self._fitted = True

    def get_params(self) -> Dict[str, Any]:
        if not self._fitted:
            return {}
        import joblib, io
        buf = io.BytesIO()
        joblib.dump(self._clf, buf)
        return {"model_bytes": buf.getvalue().hex()}

    def set_params(self, params: Dict[str, Any]) -> None:
        if "model_bytes" not in params:
            return
        import joblib, io
        buf = io.BytesIO(bytes.fromhex(params["model_bytes"]))
        self._clf = joblib.load(buf)
        self._fitted = True


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------

class Strategy:
    """Generates trading signals for a set of tickers from their feature matrices.

    Args:
        scoring_model: "linear" | "tree" | "neural"
        model_params: Dict of model-specific hyperparameters.
        buy_threshold: Score above this → BUY signal.
        sell_threshold: Score below this → SELL signal.
    """

    def __init__(
        self,
        scoring_model: str = "linear",
        model_params: Optional[Dict[str, Any]] = None,
        buy_threshold: float = 0.60,
        sell_threshold: float = 0.40,
    ) -> None:
        self.scoring_model_name = scoring_model
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold
        model_params = model_params or {}
        self._scorer: Any  # typing convenience

        if scoring_model == "linear":
            self._scorer = _LinearScorer(
                n_features=1,  # will be resized on first predict
                regularization=model_params.get("linear", {}).get("regularization", 0.01),
            )
        elif scoring_model == "tree":
            tp = model_params.get("tree", {})
            self._scorer = _TreeScorer(
                n_estimators=tp.get("n_estimators", 100),
                max_depth=tp.get("max_depth", 5),
            )
        elif scoring_model == "neural":
            np_ = model_params.get("neural", {})
            self._scorer = _NeuralScorer(
                hidden_layers=np_.get("hidden_layers", [64, 32]),
                dropout=np_.get("dropout", 0.2),
            )
        else:
            raise ValueError(f"Unknown scoring_model: {scoring_model}")

        logger.info("Strategy initialised", extra={"model": scoring_model})

    def generate_signals(
        self,
        feature_dict: Dict[str, pd.DataFrame],
        timestamp: str = "",
    ) -> List[Signal]:
        """Generate one Signal per ticker using the last row of each feature DF.

        Args:
            feature_dict: {ticker: features_DataFrame}
            timestamp: ISO string for the current bar's timestamp.

        Returns:
            List of Signal objects (one per ticker with valid features).
        """
        signals: List[Signal] = []

        for ticker, feat_df in feature_dict.items():
            if feat_df.empty:
                logger.warning("Empty feature df, skipping", extra={"ticker": ticker})
                continue

            X = feat_df.values[-1:].astype(float)  # shape (1, n_features)

            # Resize linear scorer weights on first call
            if self.scoring_model_name == "linear":
                n = X.shape[1]
                if len(self._scorer.weights) != n:
                    self._scorer = _LinearScorer(n_features=n)

            # Guard against NaN features
            if np.any(np.isnan(X)):
                logger.warning("NaN in features, skipping", extra={"ticker": ticker})
                continue

            score = float(self._scorer.predict_proba(X)[0])
            action, reason = self._classify(score, ticker, feat_df)
            confidence = abs(score - 0.5)

            signals.append(Signal(
                ticker=ticker,
                action=action,
                score=score,
                confidence=confidence,
                timestamp=timestamp,
                features={col: float(feat_df[col].iloc[-1]) for col in feat_df.columns},
                reason=reason,
            ))

        return signals

    def score_series(self, feat_df: pd.DataFrame) -> pd.Series:
        """Score every row of *feat_df*; returns a Series of scores in [0, 1].
        Used by the backtester to evaluate the entire history."""
        X = feat_df.values.astype(float)
        if self.scoring_model_name == "linear":
            n = X.shape[1]
            if len(self._scorer.weights) != n:
                self._scorer = _LinearScorer(n_features=n)
        # Replace NaN rows with 0.5 (neutral)
        row_has_nan = np.isnan(X).any(axis=1)
        scores = np.where(row_has_nan, 0.5, self._scorer.predict_proba(X))
        return pd.Series(scores, index=feat_df.index, name="score")

    def get_scorer_params(self) -> Dict[str, Any]:
        return self._scorer.get_params()

    def set_scorer_params(self, params: Dict[str, Any]) -> None:
        self._scorer.set_params(params)

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train / re-train the underlying model (tree / neural)."""
        if hasattr(self._scorer, "fit"):
            self._scorer.fit(X, y)
        else:
            logger.warning("Linear scorer does not support batch fit — use learner.py")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify(self, score: float, ticker: str, feat_df: pd.DataFrame) -> tuple[Action, str]:
        if score >= self.buy_threshold:
            reason = f"Score {score:.3f} ≥ buy threshold {self.buy_threshold}"
            return Action.BUY, reason
        elif score <= self.sell_threshold:
            reason = f"Score {score:.3f} ≤ sell threshold {self.sell_threshold}"
            return Action.SELL, reason
        else:
            return Action.HOLD, f"Score {score:.3f} in neutral zone"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))
