"""
learning/reward.py — Reward and fitness functions for learning.

Defines how we measure a trade's or strategy's quality, feeding back into
the learning loop to improve future decisions.

Multiple reward functions are provided — the active one is chosen by config.
"""
from __future__ import annotations

import math
from typing import List, Optional


# ---------------------------------------------------------------------------
# Single-trade reward
# ---------------------------------------------------------------------------

def trade_reward(
    pnl: float,
    entry_price: float,
    exit_price: float,
    holding_periods: int,
    commission: float = 0.0,
    slippage: float = 0.0,
    drawdown_penalty: float = 0.0,
) -> float:
    """Compute a scalar reward for a single completed trade.

    Reward = risk-adjusted return minus penalties for drawdown and costs.

    Args:
        pnl: Net P&L of the trade (after commissions and slippage).
        entry_price: Price at which the position was opened.
        exit_price: Price at which the position was closed.
        holding_periods: Number of bars held.
        commission: Total commissions paid.
        slippage: Total slippage paid.
        drawdown_penalty: Optional penalty for intra-trade drawdown.

    Returns:
        Scalar reward in approximately [-1, 1].
    """
    if entry_price <= 0:
        return 0.0

    # Percentage return
    pct_return = (exit_price - entry_price) / entry_price

    # Time penalty — longer holds reduce reward per period
    time_penalty = max(0.0, math.log1p(holding_periods) / 20)

    # Cost penalty
    cost_pct = (commission + slippage) / (entry_price + 1e-9)

    # Combine
    reward = pct_return - time_penalty - cost_pct - drawdown_penalty

    # Clip to reasonable range
    return max(-1.0, min(1.0, reward))


def sharpe_reward(
    returns: List[float],
    risk_free_rate: float = 0.04,
    periods_per_year: int = 252,
) -> float:
    """Compute an annualised Sharpe ratio as a reward signal.

    Args:
        returns: List of periodic (daily) returns as fractions.
        risk_free_rate: Annual risk-free rate (default 4%).
        periods_per_year: Trading periods per year (252 for daily).

    Returns:
        Annualised Sharpe ratio (can be negative).
    """
    if len(returns) < 2:
        return 0.0

    import numpy as np

    r = np.array(returns)
    rfr_per_period = risk_free_rate / periods_per_year
    excess = r - rfr_per_period
    std = r.std()

    if std < 1e-9:
        return 0.0

    return float(excess.mean() / std * math.sqrt(periods_per_year))


def calmar_reward(
    returns: List[float],
    periods_per_year: int = 252,
) -> float:
    """Calmar ratio = annualised return / max drawdown.

    Penalises strategies with large drawdowns relative to their gains.

    Args:
        returns: Periodic returns as fractions.
        periods_per_year: Trading periods per year.

    Returns:
        Calmar ratio (higher is better, capped at 10).
    """
    if len(returns) < 2:
        return 0.0

    import numpy as np

    r = np.array(returns)
    ann_return = r.mean() * periods_per_year

    # Compute max drawdown from cumulative returns
    cum = np.cumprod(1 + r)
    peak = np.maximum.accumulate(cum)
    dd = (peak - cum) / peak
    max_dd = float(dd.max())

    if max_dd < 1e-6:
        return min(10.0, ann_return / 1e-6)

    return min(10.0, ann_return / max_dd)


def composite_reward(
    pnl: float,
    returns: List[float],
    max_drawdown: float,
    win_rate: float,
    sharpe_weight: float = 0.5,
    pnl_weight: float = 0.3,
    win_rate_weight: float = 0.2,
) -> float:
    """Weighted composite of multiple reward signals.

    Useful as the primary reward when training the strategy model.

    Args:
        pnl: Total realised P&L.
        returns: List of periodic returns.
        max_drawdown: Max portfolio drawdown as a fraction (e.g. 0.10 = 10%).
        win_rate: Fraction of trades that were profitable (0–1).
        *_weight: Weights for each component (must sum to 1).

    Returns:
        Composite scalar reward.
    """
    sharpe = sharpe_reward(returns)
    # Normalise Sharpe to [-1, 1]
    sharpe_norm = max(-1.0, min(1.0, sharpe / 3.0))

    # Normalise PnL to [-1, 1] using a soft clamp
    pnl_norm = math.tanh(pnl / 1000.0)

    # Win rate shifted to [-1, 1]
    win_norm = (win_rate - 0.5) * 2

    # Drawdown penalty
    dd_penalty = max_drawdown * 2  # 10% drawdown → -0.2 penalty

    composite = (
        sharpe_weight * sharpe_norm
        + pnl_weight * pnl_norm
        + win_rate_weight * win_norm
        - dd_penalty
    )
    return max(-1.0, min(1.0, composite))


# ---------------------------------------------------------------------------
# Label generator for supervised learning
# ---------------------------------------------------------------------------

def label_from_reward(reward: float, threshold: float = 0.01) -> int:
    """Convert a reward scalar to a binary class label.

    Args:
        reward: Scalar reward value.
        threshold: Minimum positive reward to assign label 1.

    Returns:
        1 if reward >= threshold, else 0.
    """
    return 1 if reward >= threshold else 0
