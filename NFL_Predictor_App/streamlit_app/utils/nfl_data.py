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
        seasons = [2022, 2023, 2024, 2025]

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
        seasons = [2025]
    try:
        import nfl_data_py as nfl
        df = nfl.import_weekly_data(seasons)
        if position and position != "All":
            df = df[df["position"] == position]
        return df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner="Building 2026 player projections from 2025 data…")
def get_2026_projections() -> pd.DataFrame:
    """
    Project 2026 season stats using a 60/40 weighted blend of 2025 (primary) and 2024 data.
    Players need ≥5 games in 2025. 2024 data blended in for stability where available.
    Applies 5% regression to mean and scales to 17 games.
    """
    try:
        import nfl_data_py as nfl
        df_2025 = nfl.import_weekly_data([2025])
        df_2024 = nfl.import_weekly_data([2024])
    except Exception:
        return pd.DataFrame()

    positions = ["QB", "RB", "WR", "TE"]
    stat_map = {
        "pass_yards": "passing_yards",
        "pass_tds": "passing_tds",
        "interceptions": "interceptions",
        "completions": "completions",
        "attempts": "attempts",
        "rush_yards": "rushing_yards",
        "rush_tds": "rushing_tds",
        "carries": "carries",
        "rec_yards": "receiving_yards",
        "receptions": "receptions",
        "rec_tds": "receiving_tds",
        "targets": "targets",
        "fantasy_std": "fantasy_points",
        "fantasy_ppr": "fantasy_points_ppr",
    }
    stat_cols = list(stat_map.keys())

    def aggregate_season(df: pd.DataFrame) -> pd.DataFrame:
        df = df[df["position"].isin(positions)].copy()
        agg_dict: dict = {"games": ("week", "count")}
        for new_col, raw_col in stat_map.items():
            if raw_col in df.columns:
                agg_dict[new_col] = (raw_col, "sum")
        agg = df.groupby(["player_id", "player_name", "recent_team", "position"]).agg(
            **agg_dict
        ).reset_index()
        for col in stat_cols:
            if col in agg.columns:
                agg[f"{col}_pg"] = agg[col] / agg["games"].replace(0, 1)
        return agg

    agg_25 = aggregate_season(df_2025)
    agg_24 = aggregate_season(df_2024)

    # Require ≥5 games in 2025 to be included
    agg_25 = agg_25[agg_25["games"] >= 5].copy()
    agg_24_valid = agg_24[agg_24["games"] >= 5].copy()

    # Pull 2024 per-game rates for blending
    pg_cols_24 = {f"{c}_pg": f"{c}_pg_24" for c in stat_cols if f"{c}_pg" in agg_24_valid.columns}
    agg = agg_25.merge(
        agg_24_valid[["player_id"] + list(pg_cols_24.keys())].rename(columns=pg_cols_24),
        on="player_id",
        how="left",
    )

    # Weighted blend: 60% 2025, 40% 2024 where 2024 data exists
    W25, W24 = 0.60, 0.40
    for col in stat_cols:
        pg_col = f"{col}_pg"
        pg_24_col = f"{col}_pg_24"
        if pg_24_col in agg.columns:
            has_24 = agg[pg_24_col].notna()
            agg[pg_col] = agg[pg_col].where(
                ~has_24,
                agg[pg_col] * W25 + agg[pg_24_col].fillna(0) * W24,
            )
            agg = agg.drop(columns=[pg_24_col])

    GAMES_2026 = 17
    REGRESSION = 0.95

    for col in stat_cols:
        if f"{col}_pg" in agg.columns:
            pg = agg[f"{col}_pg"]
            proj = pg * REGRESSION * GAMES_2026
            agg[f"{col}_pg"] = pg.round(2)
            agg[f"{col}_proj"] = proj.round(1)
            agg[f"{col}_floor"] = (proj * 0.75).round(1)
            agg[f"{col}_ceil"] = (proj * 1.30).round(1)

    agg["comp_pct"] = (agg["completions"] / agg["attempts"].replace(0, 1) * 100).round(1)
    agg["ypc"] = (agg["rush_yards"] / agg["carries"].replace(0, 1)).round(2)
    agg["ypr"] = (agg["rec_yards"] / agg["receptions"].replace(0, 1)).round(2)
    agg["catch_pct"] = (agg["receptions"] / agg["targets"].replace(0, 1) * 100).round(1)

    return agg.sort_values("fantasy_ppr_proj", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=3600)
def get_season_leaders(season: int = 2025) -> dict[str, pd.DataFrame]:
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
