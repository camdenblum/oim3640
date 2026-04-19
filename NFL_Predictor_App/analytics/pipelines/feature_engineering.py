"""Feature engineering pipeline for game and player prediction models."""
import numpy as np
import pandas as pd
from db import query


def get_team_rolling_stats(team_id: int, before_week: int, season_year: int, n_games: int = 4) -> dict:
    """Compute rolling stats for a team over the last n_games before given week."""
    rows = query("""
        SELECT tgs.points_scored, tgs.points_allowed, tgs.total_yards, tgs.passing_yards,
               tgs.rushing_yards, tgs.turnovers, tgs.third_down_conversions, tgs.third_down_attempts,
               tgs.red_zone_trips, tgs.red_zone_touchdowns, tgs.epa_per_play, tgs.success_rate,
               tgs.blitz_rate, tgs.pressure_rate, tgs.sacks, tgs.interceptions_caught,
               g.week, tgs.is_home
        FROM team_game_stats tgs
        JOIN games g ON g.id = tgs.game_id
        WHERE tgs.team_id = %s AND g.season_year = %s AND g.week < %s AND g.status = 'final'
        ORDER BY g.week DESC LIMIT %s
    """, [team_id, season_year, before_week, n_games])

    if not rows:
        return _default_team_stats()

    df = pd.DataFrame(rows)
    stats = {
        f'ppg_l{n_games}': float(df['points_scored'].mean()),
        f'ppg_allowed_l{n_games}': float(df['points_allowed'].mean()),
        f'yards_per_game_l{n_games}': float(df['total_yards'].mean()),
        f'pass_yards_l{n_games}': float(df['passing_yards'].mean()),
        f'rush_yards_l{n_games}': float(df['rushing_yards'].mean()),
        f'turnovers_l{n_games}': float(df['turnovers'].mean()),
        f'epa_per_play_l{n_games}': float(df['epa_per_play'].mean() if df['epa_per_play'].notna().any() else 0),
        f'third_down_pct_l{n_games}': float(
            (df['third_down_conversions'].sum() / max(df['third_down_attempts'].sum(), 1))
        ),
        f'red_zone_eff_l{n_games}': float(
            (df['red_zone_touchdowns'].sum() / max(df['red_zone_trips'].sum(), 1))
        ),
        f'sacks_l{n_games}': float(df['sacks'].mean()),
        f'pressure_rate_l{n_games}': float(df['pressure_rate'].mean() if df['pressure_rate'].notna().any() else 0.25),
        f'wins_l{n_games}': int((df['points_scored'] > df['points_allowed']).sum()),
    }
    return stats


def _default_team_stats() -> dict:
    return {
        'ppg_l4': 21.0, 'ppg_allowed_l4': 21.0,
        'yards_per_game_l4': 330.0, 'pass_yards_l4': 220.0, 'rush_yards_l4': 110.0,
        'turnovers_l4': 1.5, 'epa_per_play_l4': 0.0, 'third_down_pct_l4': 0.40,
        'red_zone_eff_l4': 0.55, 'sacks_l4': 2.5, 'pressure_rate_l4': 0.25,
        'wins_l4': 2,
    }


def get_elo_rating(team_id: int) -> float:
    rows = query("SELECT rating FROM elo_ratings WHERE team_id = %s", [team_id])
    return float(rows[0]['rating']) if rows else 1500.0


def build_game_feature_vector(home_team_id: int, away_team_id: int, season_year: int,
                               week: int, venue: str = '', weather_temp: int = 70,
                               weather_wind: int = 5) -> np.ndarray:
    """Build the 70+ feature vector for game prediction."""
    home_l4 = get_team_rolling_stats(home_team_id, week, season_year, 4)
    home_l8 = get_team_rolling_stats(home_team_id, week, season_year, 8)
    away_l4 = get_team_rolling_stats(away_team_id, week, season_year, 4)
    away_l8 = get_team_rolling_stats(away_team_id, week, season_year, 8)
    home_elo = get_elo_rating(home_team_id)
    away_elo = get_elo_rating(away_team_id)
    elo_diff = home_elo + 65 - away_elo  # 65 = home field advantage

    # Injury flags
    home_qb_injured = _check_qb_injured(home_team_id)
    away_qb_injured = _check_qb_injured(away_team_id)

    features = [
        home_l4['ppg_l4'], home_l4['ppg_allowed_l4'],
        away_l4['ppg_l4'], away_l4['ppg_allowed_l4'],
        home_l8['ppg_l8'] if 'ppg_l8' in home_l8 else home_l4['ppg_l4'],
        away_l8['ppg_l8'] if 'ppg_l8' in away_l8 else away_l4['ppg_l4'],
        home_l4['yards_per_game_l4'], away_l4['yards_per_game_l4'],
        home_l4['pass_yards_l4'], away_l4['pass_yards_l4'],
        home_l4['rush_yards_l4'], away_l4['rush_yards_l4'],
        home_l4['epa_per_play_l4'], away_l4['epa_per_play_l4'],
        home_l4['third_down_pct_l4'], away_l4['third_down_pct_l4'],
        home_l4['red_zone_eff_l4'], away_l4['red_zone_eff_l4'],
        home_l4['turnovers_l4'], away_l4['turnovers_l4'],
        home_l8['turnovers_l4'], away_l8['turnovers_l4'],  # l8 turnover diff
        home_l4['sacks_l4'], away_l4['sacks_l4'],
        home_l4['pressure_rate_l4'], away_l4['pressure_rate_l4'],
        1.0,  # home_field_advantage binary
        1.0 if 'turf' in venue.lower() else 0.0,  # surface_type
        1.0 if any(d in venue.lower() for d in ['dome', 'indoor', 'stadium']) else 0.0,
        (weather_temp - 55) / 30.0,  # normalized temp
        weather_wind / 20.0,  # normalized wind
        week / 18.0,  # week of season
        float(home_qb_injured), float(away_qb_injured),
        home_elo / 1500.0, away_elo / 1500.0, elo_diff / 400.0,
        home_l4['wins_l4'] / 4.0, away_l4['wins_l4'] / 4.0,
        _h2h_win_pct(home_team_id, away_team_id),
        _momentum_score(home_team_id, season_year, week),
        _momentum_score(away_team_id, season_year, week),
    ]
    return np.array(features, dtype=np.float32)


def _check_qb_injured(team_id: int) -> bool:
    rows = query("""
        SELECT 1 FROM players WHERE team_id = %s AND position = 'QB'
        AND injury_status IN ('Out', 'Injured Reserve', 'Doubtful', 'PUP') AND is_starter = true
    """, [team_id])
    return len(rows) > 0


def _h2h_win_pct(home_team_id: int, away_team_id: int) -> float:
    rows = query("""
        SELECT home_score, away_score, home_team_id FROM games
        WHERE ((home_team_id=%s AND away_team_id=%s) OR (home_team_id=%s AND away_team_id=%s))
        AND status='final' ORDER BY game_date DESC LIMIT 5
    """, [home_team_id, away_team_id, away_team_id, home_team_id])
    if not rows:
        return 0.5
    home_wins = sum(1 for r in rows if (r['home_team_id'] == home_team_id and r['home_score'] > r['away_score'])
                    or (r['home_team_id'] != home_team_id and r['away_score'] > r['home_score']))
    return home_wins / len(rows)


def _momentum_score(team_id: int, season_year: int, before_week: int) -> float:
    rows = query("""
        SELECT tgs.points_scored, tgs.points_allowed, g.week
        FROM team_game_stats tgs JOIN games g ON g.id = tgs.game_id
        WHERE tgs.team_id = %s AND g.season_year = %s AND g.week < %s AND g.status = 'final'
        ORDER BY g.week DESC LIMIT 4
    """, [team_id, season_year, before_week])
    if not rows:
        return 0.5
    # Weighted recent form: more recent = higher weight
    weights = [0.4, 0.3, 0.2, 0.1]
    score = 0.0
    for i, row in enumerate(rows[:4]):
        w = weights[i] if i < len(weights) else 0.05
        score += w * (1.0 if row['points_scored'] > row['points_allowed'] else 0.0)
    return score


def build_player_feature_vector(player_id: int, game_id: int, opponent_team_id: int) -> np.ndarray:
    """Build feature vector for player projection."""
    rows = query("""
        SELECT p.position, pgs.snaps_played, pgs.snap_percentage,
               pgs.qb_yards, pgs.qb_touchdowns, pgs.qb_interceptions,
               pgs.rb_yards, pgs.rb_carries, pgs.rb_touchdowns,
               pgs.rec_yards, pgs.rec_receptions, pgs.rec_targets, pgs.rec_touchdowns,
               g.week, g.season_year, pgs.team_id
        FROM player_game_stats pgs
        JOIN games g ON g.id = pgs.game_id
        JOIN players p ON p.id = pgs.player_id
        WHERE pgs.player_id = %s AND g.status = 'final'
        ORDER BY g.season_year DESC, g.week DESC LIMIT 8
    """, [player_id])

    if not rows:
        return np.zeros(20, dtype=np.float32)

    df = pd.DataFrame(rows)
    position = rows[0]['position'] if rows else 'QB'

    if position == 'QB':
        stat_col = 'qb_yards'
    elif position == 'RB':
        stat_col = 'rb_yards'
    else:
        stat_col = 'rec_yards'

    avg_l4 = float(df[stat_col].head(4).mean() or 0)
    avg_l8 = float(df[stat_col].mean() or 0)
    avg_snaps = float(df['snap_percentage'].mean() or 0)

    opp_stats = _get_opponent_defense_stats(opponent_team_id, position)

    features = [
        avg_l4 / 300.0,
        avg_l8 / 300.0,
        avg_snaps / 100.0,
        opp_stats.get('yards_allowed_rank', 16) / 32.0,
        opp_stats.get('td_allowed_rank', 16) / 32.0,
        opp_stats.get('pressure_rate', 0.25),
        opp_stats.get('blitz_rate', 0.20),
    ]
    return np.array(features + [0.0] * (20 - len(features)), dtype=np.float32)


def _get_opponent_defense_stats(team_id: int, position: str) -> dict:
    rows = query("""
        SELECT AVG(tgs.pressure_rate) as pressure_rate, AVG(tgs.blitz_rate) as blitz_rate,
               AVG(tgs.passing_yards) as pass_yards_allowed, AVG(tgs.rushing_yards) as rush_yards_allowed
        FROM team_game_stats tgs JOIN games g ON g.id = tgs.game_id
        WHERE tgs.team_id != %s AND g.status = 'final'
        LIMIT 8
    """, [team_id])
    if rows:
        return dict(rows[0])
    return {'pressure_rate': 0.25, 'blitz_rate': 0.20, 'yards_allowed_rank': 16, 'td_allowed_rank': 16}
