"""
learning/learning_loop.py — Offline and online learning orchestration.

Two phases:
  1. Offline: batch-train the scoring model from historical trade logs and
     price data before the bot starts trading.
  2. Online: after every N live trades, run a lightweight gradient update
     using recent trade outcomes.  If performance degrades, revert to the
     last known-good checkpoint.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from data.features import FeatureEngineer
from learning.reward import composite_reward, sharpe_reward
from models.learner import Learner
from models.strategy import Strategy
from state.trader_state import TraderState

logger = logging.getLogger(__name__)


class LearningLoop:
    """Manages both offline batch training and online incremental updates.

    Args:
        strategy: The Strategy whose scorer will be trained.
        learner: The Learner that wraps the training logic.
        state: TraderState for reading trade history.
        feature_engineer: FeatureEngineer instance (for online feature extraction).
        enable_learning: Master toggle.
        offline_epochs: How many gradient passes over the historical dataset.
        online_update_interval: Number of live trades between online updates.
        revert_threshold: If validation Sharpe drops by this fraction after an
            online update, revert to the previous checkpoint.
    """

    def __init__(
        self,
        strategy: Strategy,
        learner: Learner,
        state: TraderState,
        feature_engineer: FeatureEngineer,
        enable_learning: bool = True,
        offline_epochs: int = 20,
        online_update_interval: int = 10,
        revert_threshold: float = 0.05,
    ) -> None:
        self.strategy = strategy
        self.learner = learner
        self.state = state
        self.feature_engineer = feature_engineer
        self.enable_learning = enable_learning
        self.offline_epochs = offline_epochs
        self.online_update_interval = online_update_interval
        self.revert_threshold = revert_threshold

        self._trades_since_last_update: int = 0
        self._last_val_sharpe: Optional[float] = None
        self._baseline_checkpoint_tag = "baseline"

    # ------------------------------------------------------------------
    # Offline learning
    # ------------------------------------------------------------------

    def run_offline_learning(
        self,
        feature_dict: Dict[str, Any],   # {ticker: pd.DataFrame}
        price_dict: Dict[str, Any],      # {ticker: pd.DataFrame}
    ) -> Dict[str, float]:
        """Run offline batch training over historical data.

        Builds a labelled dataset from features + forward returns, trains the
        scoring model for *offline_epochs* passes, saves a checkpoint.

        Args:
            feature_dict: Pre-computed features per ticker.
            price_dict: Raw OHLCV data per ticker.

        Returns:
            Training metrics dict.
        """
        if not self.enable_learning:
            logger.info("Learning disabled — skipping offline training")
            return {}

        logger.info("Starting offline learning", extra={"epochs": self.offline_epochs})

        X, y = self.learner.build_dataset(feature_dict, price_dict)
        if len(X) == 0:
            logger.warning("No training data available for offline learning")
            return {}

        metrics = self.learner.train(X, y, epochs=self.offline_epochs)

        # Save baseline checkpoint
        path = self.learner.save_checkpoint(tag=self._baseline_checkpoint_tag)
        self.state.record_checkpoint(
            tag=self._baseline_checkpoint_tag,
            model_name=self.strategy.scoring_model_name,
            path=str(path),
            train_accuracy=metrics.get("train_accuracy", 0.0),
            val_accuracy=metrics.get("val_accuracy", 0.0),
        )

        # Also save as "latest"
        self.learner.save_checkpoint(tag="latest")

        logger.info("Offline learning complete", extra={"metrics": metrics})
        return metrics

    # ------------------------------------------------------------------
    # Online learning
    # ------------------------------------------------------------------

    def record_trade_outcome(
        self,
        feature_row: np.ndarray,
        label: int,
        pnl: float,
        portfolio_returns: List[float],
    ) -> None:
        """Record one completed trade and trigger online update if due.

        Args:
            feature_row: Feature vector at the time the trade was opened.
            label: 1 if the trade was profitable, 0 otherwise.
            pnl: Realised P&L of the trade.
            portfolio_returns: Recent portfolio daily returns (for Sharpe check).
        """
        if not self.enable_learning:
            return

        self._trades_since_last_update += 1

        if self._trades_since_last_update >= self.online_update_interval:
            self._run_online_update(feature_row, label, portfolio_returns)
            self._trades_since_last_update = 0

    def _run_online_update(
        self,
        feature_row: np.ndarray,
        label: int,
        portfolio_returns: List[float],
    ) -> None:
        """Apply a gradient step and revert if performance degrades."""
        # Snapshot current Sharpe before update
        current_sharpe = sharpe_reward(portfolio_returns) if portfolio_returns else 0.0

        # Save pre-update checkpoint
        self.learner.save_checkpoint(tag="pre_online_update")

        # Apply gradient step
        self.learner.online_update(feature_row, label)

        # Evaluate post-update Sharpe (using the same recent returns as proxy)
        # In a production system you'd compare on a held-out window
        post_sharpe = current_sharpe  # placeholder — see note below

        # NOTE: A proper implementation would run the updated model over a
        # held-out validation window to compute post-update performance.
        # For simplicity here we only revert if a degradation flag is raised
        # externally via revert_if_degraded().

        self.learner.save_checkpoint(tag="latest")
        self._last_val_sharpe = post_sharpe
        logger.info("Online update applied", extra={"post_sharpe": round(post_sharpe, 3)})

    def revert_if_degraded(self, new_sharpe: float) -> bool:
        """Check if a new Sharpe is significantly worse; if so, revert model.

        Args:
            new_sharpe: Most recently computed validation Sharpe.

        Returns:
            True if the model was reverted.
        """
        if self._last_val_sharpe is None:
            return False

        baseline = self._last_val_sharpe
        if baseline > 0 and (baseline - new_sharpe) / abs(baseline) > self.revert_threshold:
            logger.warning(
                "Online update degraded performance — reverting",
                extra={"before": round(baseline, 3), "after": round(new_sharpe, 3)},
            )
            reverted = self.learner.load_checkpoint(tag="pre_online_update")
            if reverted:
                self.learner.save_checkpoint(tag="latest")
            return True
        return False

    def restore_baseline(self) -> bool:
        """Restore the model to the offline-trained baseline checkpoint."""
        ok = self.learner.load_checkpoint(tag=self._baseline_checkpoint_tag)
        if ok:
            self.learner.save_checkpoint(tag="latest")
            logger.info("Restored to baseline checkpoint")
        return ok

    # ------------------------------------------------------------------
    # Load latest checkpoint at startup
    # ------------------------------------------------------------------

    def load_latest_or_baseline(self) -> bool:
        """Load the most recent checkpoint, falling back to baseline."""
        if self.learner.load_checkpoint(tag="latest"):
            logger.info("Loaded latest checkpoint")
            return True
        if self.learner.load_checkpoint(tag=self._baseline_checkpoint_tag):
            logger.info("Loaded baseline checkpoint")
            return True
        logger.info("No checkpoint found — starting with uninitialised weights")
        return False
