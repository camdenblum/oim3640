"""
models/learner.py — Model training, offline batch learning, and parameter persistence.

The Learner is responsible for:
  1. Building a labelled training dataset from historical trade logs.
  2. Training (or re-training) the Strategy's scoring model.
  3. Persisting model checkpoints to disk.
  4. Loading a saved checkpoint to resume from.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from models.strategy import Strategy

logger = logging.getLogger(__name__)

# Label thresholds: a trade is "positive" if its forward return exceeds this
_POSITIVE_RETURN_THRESHOLD = 0.005   # 0.5%
_NEGATIVE_RETURN_THRESHOLD = -0.005  # -0.5%


class Learner:
    """Manages offline training and checkpoint save/load for a Strategy.

    Args:
        strategy: The Strategy instance whose scorer will be trained.
        artifacts_dir: Directory for saving/loading model checkpoints.
        learning_rate: Step size for online gradient updates (linear model only).
        validation_window: Number of most-recent samples to hold out for validation.
        regularization: L2 regularisation coefficient.
    """

    def __init__(
        self,
        strategy: Strategy,
        artifacts_dir: str = ".state/learning",
        learning_rate: float = 0.001,
        validation_window: int = 500,
        regularization: float = 0.01,
    ) -> None:
        self.strategy = strategy
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.learning_rate = learning_rate
        self.validation_window = validation_window
        self.regularization = regularization
        self._scaler = StandardScaler()
        self._scaler_fitted = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_dataset(
        self,
        feature_dict: Dict[str, pd.DataFrame],
        price_dict: Dict[str, pd.DataFrame],
        forward_period: int = 5,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Build a supervised learning dataset from features + price data.

        A sample is labelled 1 (bullish) if the *forward_period*-day return
        exceeds _POSITIVE_RETURN_THRESHOLD, and 0 (bearish) if below
        _NEGATIVE_RETURN_THRESHOLD.  Samples in between are excluded.

        Args:
            feature_dict: {ticker: feature_DataFrame} from FeatureEngineer.
            price_dict: {ticker: OHLCV_DataFrame}.
            forward_period: Bars ahead to measure the outcome return.

        Returns:
            (X, y) arrays suitable for sklearn fit().
        """
        X_parts: List[np.ndarray] = []
        y_parts: List[np.ndarray] = []

        for ticker, feat_df in feature_dict.items():
            price_df = price_dict.get(ticker)
            if price_df is None or price_df.empty or feat_df.empty:
                continue

            # Align on common index
            common_idx = feat_df.index.intersection(price_df.index)
            feat_aligned = feat_df.loc[common_idx]
            price_aligned = price_df.loc[common_idx, "Close"]

            # Forward return
            fwd_ret = price_aligned.shift(-forward_period) / price_aligned - 1
            fwd_ret = fwd_ret.dropna()

            # Align features to forward return dates
            feat_aligned = feat_aligned.loc[fwd_ret.index]

            # Label
            positive = (fwd_ret > _POSITIVE_RETURN_THRESHOLD).astype(int)
            negative = (fwd_ret < _NEGATIVE_RETURN_THRESHOLD).astype(int)
            valid_mask = (positive | negative).astype(bool)

            X_ticker = feat_aligned.values[valid_mask]
            y_ticker = positive.values[valid_mask]

            if len(X_ticker) > 0:
                X_parts.append(X_ticker)
                y_parts.append(y_ticker)

        if not X_parts:
            logger.warning("No training samples built — check feature/price data alignment")
            return np.empty((0, 0)), np.empty(0)

        X = np.vstack(X_parts).astype(float)
        y = np.concatenate(y_parts).astype(int)

        # Remove any remaining NaN rows
        valid = ~np.isnan(X).any(axis=1)
        X, y = X[valid], y[valid]

        logger.info(
            "Dataset built",
            extra={"samples": len(X), "positive": int(y.sum()), "negative": int((1 - y).sum())},
        )
        return X, y

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 1,
    ) -> Dict[str, float]:
        """Train (or re-train) the strategy's scorer on labelled data.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Binary labels (n_samples,).
            epochs: Training iterations (used for linear gradient descent).

        Returns:
            Dict with train/val accuracy and loss metrics.
        """
        if len(X) == 0:
            logger.warning("train() called with empty dataset")
            return {}

        # Fit scaler
        self._scaler.fit(X)
        self._scaler_fitted = True
        X_scaled = self._scaler.transform(X)

        # Hold out validation set
        val_size = min(self.validation_window, int(len(X) * 0.15))
        if val_size > 0:
            X_tr, X_val, y_tr, y_val = train_test_split(
                X_scaled, y, test_size=val_size, shuffle=False
            )
        else:
            X_tr, X_val, y_tr, y_val = X_scaled, np.empty(0), y, np.empty(0)

        metrics: Dict[str, float] = {}

        model_name = self.strategy.scoring_model_name

        if model_name == "linear":
            metrics = self._train_linear(X_tr, y_tr, X_val, y_val, epochs)
        elif model_name in ("tree", "neural"):
            self.strategy.fit(X_tr, y_tr)
            train_acc = self._accuracy(self.strategy.score_series(
                pd.DataFrame(X_tr, columns=[f"f{i}" for i in range(X_tr.shape[1])])
            ).values, y_tr)
            metrics["train_accuracy"] = train_acc
            if len(X_val) > 0:
                val_acc = self._accuracy(self.strategy.score_series(
                    pd.DataFrame(X_val, columns=[f"f{i}" for i in range(X_val.shape[1])])
                ).values, y_val)
                metrics["val_accuracy"] = val_acc

        logger.info("Training complete", extra={"metrics": metrics})
        return metrics

    def online_update(self, feature_row: np.ndarray, label: int) -> None:
        """Single-sample online gradient step for the linear scorer.

        Args:
            feature_row: 1-D feature vector for one trade.
            label: 1 (profitable) or 0 (loss).
        """
        if self.strategy.scoring_model_name != "linear":
            return  # Online update only implemented for linear model

        if self._scaler_fitted:
            x = self._scaler.transform(feature_row.reshape(1, -1))[0]
        else:
            x = feature_row

        params = self.strategy.get_scorer_params()
        w = np.array(params["weights"])
        b = float(params.get("bias", 0.0))

        if len(w) != len(x):
            logger.warning("Feature dimension mismatch in online update — skipping")
            return

        # Sigmoid logistic loss gradient
        logit = float(x @ w + b)
        pred = 1.0 / (1.0 + np.exp(-logit))
        error = pred - label
        grad_w = error * x + self.regularization * w
        grad_b = error

        w_new = w - self.learning_rate * grad_w
        b_new = b - self.learning_rate * grad_b
        self.strategy.set_scorer_params({"weights": w_new.tolist(), "bias": b_new})

    def save_checkpoint(self, tag: str = "latest") -> Path:
        """Persist current model params and scaler to disk.

        Args:
            tag: Version label, e.g. "latest", "pre_live_v1".

        Returns:
            Path to the saved checkpoint file.
        """
        checkpoint = {
            "tag": tag,
            "model_name": self.strategy.scoring_model_name,
            "scorer_params": self.strategy.get_scorer_params(),
            "scaler_mean": self._scaler.mean_.tolist() if self._scaler_fitted else [],
            "scaler_scale": self._scaler.scale_.tolist() if self._scaler_fitted else [],
        }
        path = self.artifacts_dir / f"checkpoint_{tag}.json"
        with open(path, "w") as f:
            json.dump(checkpoint, f)
        logger.info("Checkpoint saved", extra={"path": str(path)})
        return path

    def load_checkpoint(self, tag: str = "latest") -> bool:
        """Load model params from a checkpoint file.

        Returns:
            True if successful, False if file not found.
        """
        path = self.artifacts_dir / f"checkpoint_{tag}.json"
        if not path.exists():
            logger.warning("Checkpoint not found", extra={"path": str(path)})
            return False

        with open(path, "r") as f:
            checkpoint = json.load(f)

        self.strategy.set_scorer_params(checkpoint.get("scorer_params", {}))

        mean_ = checkpoint.get("scaler_mean", [])
        scale_ = checkpoint.get("scaler_scale", [])
        if mean_ and scale_:
            self._scaler.mean_ = np.array(mean_)
            self._scaler.scale_ = np.array(scale_)
            self._scaler.var_ = self._scaler.scale_ ** 2
            self._scaler.n_features_in_ = len(mean_)
            self._scaler_fitted = True

        logger.info("Checkpoint loaded", extra={"tag": tag, "path": str(path)})
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _train_linear(
        self,
        X_tr: np.ndarray,
        y_tr: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int,
    ) -> Dict[str, float]:
        """Mini-batch gradient descent for linear scorer."""
        params = self.strategy.get_scorer_params()
        n_features = X_tr.shape[1]
        w = np.array(params.get("weights", np.zeros(n_features)))
        if len(w) != n_features:
            w = np.zeros(n_features)
        b = float(params.get("bias", 0.0))

        batch_size = min(64, len(X_tr))
        rng = np.random.default_rng(42)

        for epoch in range(epochs):
            idx = rng.permutation(len(X_tr))
            for start in range(0, len(X_tr), batch_size):
                batch_idx = idx[start: start + batch_size]
                x_b = X_tr[batch_idx]
                y_b = y_tr[batch_idx]

                logits = x_b @ w + b
                preds = 1.0 / (1.0 + np.exp(-np.clip(logits, -500, 500)))
                errors = preds - y_b
                grad_w = (x_b.T @ errors) / len(x_b) + self.regularization * w
                grad_b = errors.mean()
                w -= self.learning_rate * grad_w
                b -= self.learning_rate * grad_b

        self.strategy.set_scorer_params({"weights": w.tolist(), "bias": b})

        # Compute metrics
        def acc(X: np.ndarray, y: np.ndarray) -> float:
            logits = X @ w + b
            preds = (logits > 0).astype(int)
            return float((preds == y).mean())

        metrics = {"train_accuracy": acc(X_tr, y_tr)}
        if len(X_val) > 0:
            metrics["val_accuracy"] = acc(X_val, y_val)
        return metrics

    @staticmethod
    def _accuracy(scores: np.ndarray, labels: np.ndarray) -> float:
        preds = (scores >= 0.5).astype(int)
        return float((preds == labels).mean())
