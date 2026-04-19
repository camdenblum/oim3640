"""
Elo-based game predictor with Monte Carlo simulation.
Elo ratings are persisted in a local SQLite database.
"""
import math
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "data" / "nfl_elo.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

K_FACTOR = 20
HOME_ADVANTAGE = 65  # Elo points added to home team

# Starting Elo — historically calibrated baseline per team strength tier
_BASE_ELO: dict[str, float] = {
    # Elite
    "KC": 1620, "SF": 1590, "PHI": 1570, "BUF": 1565,
    # Strong
    "BAL": 1545, "DAL": 1540, "DET": 1535, "MIA": 1525,
    "CIN": 1520, "LAC": 1515, "GB": 1510, "MIN": 1508,
    # Average
    "HOU": 1500, "SEA": 1498, "JAX": 1495, "NYJ": 1492,
    "CLE": 1490, "NE": 1488, "TB": 1485, "LA": 1482,
    "PIT": 1480, "NYG": 1475, "LV": 1472, "IND": 1468,
    "TEN": 1465, "ATL": 1460, "NO": 1455, "WAS": 1452,
    # Rebuilding
    "DEN": 1440, "CAR": 1420, "ARI": 1415, "CHI": 1410,
}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS elo_ratings (
            abbr      TEXT PRIMARY KEY,
            rating    REAL NOT NULL DEFAULT 1500,
            wins      INTEGER DEFAULT 0,
            losses    INTEGER DEFAULT 0,
            ties      INTEGER DEFAULT 0,
            updated   TEXT
        );
        CREATE TABLE IF NOT EXISTS elo_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            abbr      TEXT,
            rating    REAL,
            season    INTEGER,
            week      INTEGER,
            saved_at  TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    return conn


def get_elo(abbr: str) -> float:
    with _get_conn() as conn:
        row = conn.execute("SELECT rating FROM elo_ratings WHERE abbr=?", (abbr,)).fetchone()
    if row:
        return float(row["rating"])
    return _BASE_ELO.get(abbr, 1500.0)


def get_all_elos() -> dict[str, float]:
    """Return {abbr: elo} for all teams, merging DB with base defaults."""
    with _get_conn() as conn:
        rows = conn.execute("SELECT abbr, rating FROM elo_ratings").fetchall()
    result = dict(_BASE_ELO)
    for row in rows:
        result[row["abbr"]] = float(row["rating"])
    return result


def set_elo(abbr: str, rating: float, wins: int = 0, losses: int = 0, ties: int = 0) -> None:
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO elo_ratings (abbr, rating, wins, losses, ties, updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(abbr) DO UPDATE SET
                rating=excluded.rating,
                wins=excluded.wins,
                losses=excluded.losses,
                ties=excluded.ties,
                updated=excluded.updated
        """, (abbr, rating, wins, losses, ties, datetime.utcnow().isoformat()))


def update_elo_after_game(
    winner_abbr: str,
    loser_abbr: str,
    margin: int,
    winner_was_home: bool,
    season: int = 2024,
    week: int = 1,
) -> tuple[float, float]:
    """Update Elo ratings after a completed game. Returns (new_winner_elo, new_loser_elo)."""
    w_elo = get_elo(winner_abbr)
    l_elo = get_elo(loser_abbr)

    home_bonus = HOME_ADVANTAGE if winner_was_home else -HOME_ADVANTAGE
    expected_w = 1.0 / (1.0 + 10 ** ((l_elo - w_elo - home_bonus) / 400))

    # Margin-of-victory multiplier (FiveThirtyEight method)
    elo_diff = w_elo - l_elo
    mov_mult = math.log(max(abs(margin), 1) + 1) * (2.2 / (elo_diff * 0.001 + 2.2))
    delta = K_FACTOR * mov_mult * (1 - expected_w)

    new_w = w_elo + delta
    new_l = l_elo - delta

    with _get_conn() as conn:
        for abbr, rating, w_inc, l_inc in [
            (winner_abbr, new_w, 1, 0),
            (loser_abbr, new_l, 0, 1),
        ]:
            existing = conn.execute(
                "SELECT wins, losses FROM elo_ratings WHERE abbr=?", (abbr,)
            ).fetchone()
            wins = (existing["wins"] if existing else 0) + w_inc
            losses = (existing["losses"] if existing else 0) + l_inc
            conn.execute("""
                INSERT INTO elo_ratings (abbr, rating, wins, losses, updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(abbr) DO UPDATE SET
                    rating=excluded.rating,
                    wins=excluded.wins,
                    losses=excluded.losses,
                    updated=excluded.updated
            """, (abbr, rating, wins, losses, datetime.utcnow().isoformat()))
        conn.commit()

    return new_w, new_l


def predict_game(home_abbr: str, away_abbr: str, n_simulations: int = 10_000) -> dict:
    """
    Predict a game using Elo + Monte Carlo simulation.
    Returns a dict with win probabilities, projected scores, spread, total, and simulation data.
    """
    home_elo = get_elo(home_abbr)
    away_elo = get_elo(away_abbr)

    # Elo win probability (with home field)
    elo_diff = home_elo + HOME_ADVANTAGE - away_elo
    elo_home_prob = 1.0 / (1.0 + 10 ** (-elo_diff / 400))

    # Projected points based on Elo strength
    # League avg ~23 pts/game, std ~10 pts
    avg = 23.0
    std = 10.0
    home_proj = avg + (home_elo - 1500) / 500 * 7 + 1.5   # +1.5 home field pts
    away_proj = avg + (away_elo - 1500) / 500 * 7

    # Monte Carlo
    rng = np.random.default_rng(seed=42)
    home_sims = rng.normal(home_proj, std, n_simulations).clip(0)
    away_sims = rng.normal(away_proj, std, n_simulations).clip(0)

    sim_home_wins = (home_sims > away_sims).sum()
    sim_ties = (home_sims == away_sims).sum()
    sim_home_prob = (sim_home_wins + sim_ties * 0.5) / n_simulations

    # Blend Elo and simulation
    final_home_prob = 0.55 * elo_home_prob + 0.45 * sim_home_prob
    final_home_prob = float(np.clip(final_home_prob, 0.05, 0.95))

    pred_home = float(np.mean(home_sims))
    pred_away = float(np.mean(away_sims))
    spread = pred_home - pred_away
    total = pred_home + pred_away
    totals = (home_sims + away_sims).tolist()

    # Confidence: how far from 50/50
    confidence = abs(final_home_prob - 0.5) * 2 * 100

    # Human-readable key factors
    factors = _build_factors(home_abbr, away_abbr, home_elo, away_elo, spread, final_home_prob)

    return {
        "home_abbr": home_abbr,
        "away_abbr": away_abbr,
        "home_elo": home_elo,
        "away_elo": away_elo,
        "home_win_prob": final_home_prob,
        "away_win_prob": 1 - final_home_prob,
        "predicted_home_score": pred_home,
        "predicted_away_score": pred_away,
        "predicted_spread": spread,
        "predicted_total": total,
        "simulation_totals": totals,
        "confidence": confidence,
        "factors": factors,
    }


def _build_factors(home: str, away: str, h_elo: float, a_elo: float, spread: float, home_prob: float) -> list[str]:
    factors = []
    diff = h_elo - a_elo
    if abs(diff) > 80:
        stronger = home if diff > 0 else away
        edge = abs(diff)
        factors.append(f"{stronger} has a large Elo advantage (+{edge:.0f} pts vs opponent)")
    elif abs(diff) > 30:
        stronger = home if diff > 0 else away
        factors.append(f"{stronger} holds a moderate Elo edge (+{abs(diff):.0f} pts)")
    else:
        factors.append(f"Teams are evenly matched (Elo gap: {abs(diff):.0f} pts)")

    factors.append(f"Home field advantage: +{HOME_ADVANTAGE} Elo pts, +1.5 projected points for {home}")
    factors.append(f"Predicted spread: {abs(spread):.1f} pts {'favor home' if spread > 0 else 'favor away'}")

    if home_prob > 0.70:
        factors.append(f"{home} is a strong favorite ({home_prob*100:.0f}% win probability)")
    elif home_prob < 0.30:
        factors.append(f"{away} is a strong favorite ({(1-home_prob)*100:.0f}% win probability)")
    else:
        factors.append("This matchup is too close to call — any outcome is realistic")

    return factors
