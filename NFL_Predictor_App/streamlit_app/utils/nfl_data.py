"""
nfl-data-py integration — loads historical schedule data to build accurate Elo ratings.
This is optional; the app works without it using baseline Elo values.
"""
import streamlit as st
import pandas as pd
from utils.predictor import update_elo_after_game, set_elo, _BASE_ELO


def load_historical_elo(seasons: list[int] | None = None) -> str:
    """
    Download NFL schedule data and replay all game results to build Elo ratings.
    Returns a status message.
    """
    if seasons is None:
        seasons = [2022, 2023, 2024]

    try:
        import nfl_data_py as nfl
    except ImportError:
        return "nfl-data-py not installed. Run: pip install nfl-data-py"

    # Reset to base Elo before replaying history
    for abbr, rating in _BASE_ELO.items():
        set_elo(abbr, rating)

    progress = st.progress(0, text="Downloading historical schedules…")
    try:
        schedules = nfl.import_schedules(seasons)
    except Exception as e:
        return f"Failed to download schedules: {e}"

    # Filter to completed regular-season games with scores
    completed = schedules[
        schedules["game_type"].isin(["REG", "POST"]) &
        schedules["home_score"].notna() &
        schedules["away_score"].notna()
    ].copy()

    completed = completed.sort_values(["season", "week", "game_id"])
    total = len(completed)
    games_processed = 0

    for _, row in completed.iterrows():
        home_abbr = str(row.get("home_team", "")).strip()
        away_abbr = str(row.get("away_team", "")).strip()
        home_score = int(row.get("home_score", 0) or 0)
        away_score = int(row.get("away_score", 0) or 0)
        season = int(row.get("season", 2024))
        week = int(row.get("week", 1))
        margin = abs(home_score - away_score)

        if not home_abbr or not away_abbr or home_abbr == away_abbr:
            continue
        if home_score == away_score:
            continue  # skip ties for simplicity

        if home_score > away_score:
            update_elo_after_game(home_abbr, away_abbr, margin, True, season, week)
        else:
            update_elo_after_game(away_abbr, home_abbr, margin, False, season, week)

        games_processed += 1
        if games_processed % 50 == 0:
            pct = games_processed / total
            progress.progress(pct, text=f"Processing game {games_processed}/{total}…")

    progress.progress(1.0, text="Done!")
    return f"Processed {games_processed} games across {len(seasons)} seasons. Elo ratings updated."


@st.cache_data(ttl=3600)
def get_player_stats(seasons: list[int] | None = None, position: str | None = None) -> pd.DataFrame:
    """Load weekly player stats from nfl-data-py."""
    if seasons is None:
        seasons = [2024]
    try:
        import nfl_data_py as nfl
        df = nfl.import_weekly_data(seasons)
        if position and position != "All":
            df = df[df["position"] == position]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner="Building 2026 player projections from 2024 data…")
def get_2026_projections() -> pd.DataFrame:
    """
    Project 2026 season stats for all offensive players using 2024 as the base year.
    Applies 5% regression to mean and scales to 17 games.
    Returns one row per player with season totals + per-game averages + floor/ceiling.
    """
    try:
        import nfl_data_py as nfl
        df = nfl.import_weekly_data([2024])
    except Exception as e:
        return pd.DataFrame()

    positions = ["QB", "RB", "WR", "TE"]
    df = df[df["position"].isin(positions)].copy()

    agg = df.groupby(["player_id", "player_name", "recent_team", "position"]).agg(
        games=("week", "count"),
        pass_yards=("passing_yards", "sum"),
        pass_tds=("passing_tds", "sum"),
        interceptions=("interceptions", "sum"),
        completions=("completions", "sum"),
        attempts=("attempts", "sum"),
        rush_yards=("rushing_yards", "sum"),
        rush_tds=("rushing_tds", "sum"),
        carries=("carries", "sum"),
        rec_yards=("receiving_yards", "sum"),
        receptions=("receptions", "sum"),
        rec_tds=("receiving_tds", "sum"),
        targets=("targets", "sum"),
        fantasy_std=("fantasy_points", "sum"),
        fantasy_ppr=("fantasy_points_ppr", "sum"),
    ).reset_index()

    # Only include players who played meaningful snaps
    agg = agg[agg["games"] >= 5].copy()

    GAMES_2026 = 17
    REGRESSION = 0.95  # slight regression to the mean

    stat_cols = [
        "pass_yards", "pass_tds", "interceptions", "completions", "attempts",
        "rush_yards", "rush_tds", "carries",
        "rec_yards", "receptions", "rec_tds", "targets",
        "fantasy_std", "fantasy_ppr",
    ]

    for col in stat_cols:
        pg = agg[col] / agg["games"]
        proj = pg * REGRESSION * GAMES_2026
        agg[f"{col}_pg"] = pg.round(2)
        agg[f"{col}_proj"] = proj.round(1)
        agg[f"{col}_floor"] = (proj * 0.75).round(1)
        agg[f"{col}_ceil"] = (proj * 1.30).round(1)

    # Completion percentage
    agg["comp_pct"] = (agg["completions"] / agg["attempts"].replace(0, 1) * 100).round(1)
    agg["ypc"] = (agg["rush_yards"] / agg["carries"].replace(0, 1)).round(2)
    agg["ypr"] = (agg["rec_yards"] / agg["receptions"].replace(0, 1)).round(2)
    agg["catch_pct"] = (agg["receptions"] / agg["targets"].replace(0, 1) * 100).round(1)

    return agg.sort_values("fantasy_ppr_proj", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=3600)
def get_season_leaders(season: int = 2024) -> dict[str, pd.DataFrame]:
    """Return stat leaders by category for the season."""
    try:
        import nfl_data_py as nfl
        df = nfl.import_weekly_data([season])
    except Exception:
        return {}

    leaders: dict[str, pd.DataFrame] = {}

    # Passing
    qb = df[df["position"] == "QB"].groupby(["player_id", "player_name", "recent_team"]).agg(
        pass_yards=("passing_yards", "sum"),
        pass_tds=("passing_tds", "sum"),
        interceptions=("interceptions", "sum"),
        completions=("completions", "sum"),
        attempts=("attempts", "sum"),
        games=("week", "count"),
    ).reset_index().sort_values("pass_yards", ascending=False).head(20)
    leaders["Passing"] = qb

    # Rushing
    rb = df[df["position"].isin(["RB", "QB", "WR"])].groupby(
        ["player_id", "player_name", "recent_team", "position"]
    ).agg(
        rush_yards=("rushing_yards", "sum"),
        rush_tds=("rushing_tds", "sum"),
        carries=("carries", "sum"),
        games=("week", "count"),
    ).reset_index().sort_values("rush_yards", ascending=False).head(20)
    leaders["Rushing"] = rb

    # Receiving
    rec = df[df["position"].isin(["WR", "TE", "RB"])].groupby(
        ["player_id", "player_name", "recent_team", "position"]
    ).agg(
        rec_yards=("receiving_yards", "sum"),
        receptions=("receptions", "sum"),
        rec_tds=("receiving_tds", "sum"),
        targets=("targets", "sum"),
        games=("week", "count"),
    ).reset_index().sort_values("rec_yards", ascending=False).head(20)
    leaders["Receiving"] = rec

    return leaders
