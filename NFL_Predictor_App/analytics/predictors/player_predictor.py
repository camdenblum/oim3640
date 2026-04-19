"""Position-specific player performance prediction models."""
import numpy as np
import joblib
from pathlib import Path
from xgboost import XGBRegressor

MODELS_DIR = Path(__file__).parent.parent / "models"

POSITION_STATS = {
    'QB': ['completions', 'attempts', 'yards', 'touchdowns', 'interceptions', 'rating'],
    'RB': ['carries', 'yards', 'touchdowns', 'targets', 'receptions', 'receiving_yards'],
    'WR': ['targets', 'receptions', 'yards', 'touchdowns', 'air_yards'],
    'TE': ['targets', 'receptions', 'yards', 'touchdowns'],
    'DEF': ['tackles', 'sacks', 'tfl', 'interceptions', 'pass_deflections'],
    'K': ['fg_made', 'fg_attempted', 'xp_made', 'fantasy_points'],
}

# Baseline league averages per position per game
POSITION_BASELINES = {
    'QB': {'completions': 22, 'attempts': 34, 'yards': 250, 'touchdowns': 1.7, 'interceptions': 0.9, 'rating': 90},
    'RB': {'carries': 15, 'yards': 65, 'touchdowns': 0.5, 'targets': 4, 'receptions': 3, 'receiving_yards': 22},
    'WR': {'targets': 6, 'receptions': 4, 'yards': 55, 'touchdowns': 0.4, 'air_yards': 50},
    'TE': {'targets': 5, 'receptions': 3, 'yards': 35, 'touchdowns': 0.3},
    'DEF': {'tackles': 4, 'sacks': 0.3, 'tfl': 0.5, 'interceptions': 0.1, 'pass_deflections': 0.4},
    'K': {'fg_made': 1.5, 'fg_attempted': 2, 'xp_made': 2, 'fantasy_points': 8},
}


def predict_player(player_id: int, position: str, feature_vector: np.ndarray,
                   matchup_rating: float) -> dict:
    """Generate stat projections with floor/ceiling for a player."""
    baseline = POSITION_BASELINES.get(position, POSITION_BASELINES['WR'])
    stat_keys = POSITION_STATS.get(position, POSITION_STATS['WR'])

    model_path = MODELS_DIR / f"player_{position.lower()}_model.joblib"

    if model_path.exists() and len(feature_vector) > 0:
        model = joblib.load(model_path)
        scale = float(model.predict(feature_vector.reshape(1, -1))[0])
    else:
        # Scale by matchup rating (0-100 → 0.5-1.5 multiplier)
        scale = 0.5 + (matchup_rating / 100)

    projected = {}
    floor_stats = {}
    ceiling_stats = {}

    for stat in stat_keys:
        base = baseline.get(stat, 1.0)
        proj = base * scale
        projected[stat] = round(max(0, proj), 1)
        floor_stats[stat] = round(max(0, proj * 0.6), 1)
        ceiling_stats[stat] = round(proj * 1.5, 1)

    fantasy_std = _calc_fantasy_std(projected, position)
    fantasy_ppr = _calc_fantasy_ppr(projected, position)

    return {
        'projected_stats': projected,
        'floor_stats': floor_stats,
        'ceiling_stats': ceiling_stats,
        'projected_fantasy_std': round(fantasy_std, 1),
        'projected_fantasy_ppr': round(fantasy_ppr, 1),
        'matchup_rating': round(matchup_rating, 1),
        'confidence_score': round(0.5 + abs(matchup_rating - 50) / 100, 3),
        'key_factors': _get_key_factors(position, matchup_rating, feature_vector),
    }


def _calc_fantasy_std(stats: dict, position: str) -> float:
    pts = 0.0
    pts += stats.get('yards', 0) * 0.1
    pts += stats.get('touchdowns', 0) * 6
    pts += stats.get('receptions', 0) * 0  # standard scoring
    pts += stats.get('carries', 0) * 0
    pts += stats.get('sacks', 0) * 1
    pts += stats.get('interceptions', 0) * 2
    if position == 'QB':
        pts += stats.get('yards', 0) * 0.04
        pts -= stats.get('interceptions', 0) * 2
    return max(0, pts)


def _calc_fantasy_ppr(stats: dict, position: str) -> float:
    pts = _calc_fantasy_std(stats, position)
    pts += stats.get('receptions', 0) * 1  # PPR bonus
    return max(0, pts)


def _get_key_factors(position: str, matchup_rating: float, features: np.ndarray) -> list[str]:
    factors = []
    if matchup_rating > 70:
        factors.append(f"Favorable matchup (rating: {matchup_rating:.0f}/100)")
    elif matchup_rating < 40:
        factors.append(f"Tough matchup (rating: {matchup_rating:.0f}/100)")
    if len(features) > 2 and features[2] > 0.7:
        factors.append("High snap percentage trend (70%+)")
    if position in ('WR', 'TE') and len(features) > 1 and features[1] > 0.8:
        factors.append("Strong recent target share")
    return factors or ["Based on season averages and matchup data"]


def compute_matchup_rating(player_position: str, opponent_team_id: int) -> float:
    """Score 0-100 how favorable the matchup is. 50 = neutral."""
    from db import query
    rows = query("""
        SELECT AVG(tgs.passing_yards) as pass_allowed, AVG(tgs.rushing_yards) as rush_allowed
        FROM team_game_stats tgs JOIN games g ON g.id = tgs.game_id
        WHERE tgs.team_id != %s AND g.status = 'final' LIMIT 8
    """, [opponent_team_id])
    if not rows or not rows[0]['pass_allowed']:
        return 50.0

    # Simplified: compare against league average
    league_pass = 220.0
    league_rush = 115.0
    if player_position in ('QB', 'WR', 'TE'):
        allowed = float(rows[0]['pass_allowed'] or league_pass)
        rating = (allowed / league_pass) * 50
    elif player_position == 'RB':
        allowed = float(rows[0]['rush_allowed'] or league_rush)
        rating = (allowed / league_rush) * 50
    else:
        rating = 50.0
    return float(np.clip(rating, 5, 95))
