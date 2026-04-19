"""
The Odds API integration + Elo-based Monte Carlo playoff simulation.
Provides Super Bowl futures odds and championship win probabilities.
"""
import requests
import numpy as np
import streamlit as st
from utils.predictor import get_all_elos

ODDS_API_KEY = "e949b99dec8e32f1316fb0e3f3a88d41"
ODDS_BASE = "https://api.the-odds-api.com/v4"

# Full team name → abbreviation mapping (for Odds API response parsing)
TEAM_NAME_TO_ABBR: dict[str, str] = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GB",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC", "Las Vegas Raiders": "LV", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LA", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NE", "New Orleans Saints": "NO", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SF", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
}

# NFL conference structure for playoff simulation
AFC_TEAMS = ["BAL", "BUF", "CIN", "CLE", "DEN", "HOU", "IND", "JAX", "KC", "LV", "LAC", "MIA", "NE", "NYJ", "PIT", "TEN"]
NFC_TEAMS = ["ARI", "ATL", "CAR", "CHI", "DAL", "DET", "GB", "LA", "MIN", "NO", "NYG", "PHI", "SEA", "SF", "TB", "WAS"]


def american_to_prob(odds: float) -> float:
    """Convert American odds to implied probability (ignoring vig)."""
    if odds > 0:
        return 100.0 / (odds + 100.0)
    else:
        return abs(odds) / (abs(odds) + 100.0)


def prob_to_american(prob: float) -> str:
    """Convert probability to American odds string."""
    prob = max(0.01, min(0.99, prob))
    if prob >= 0.5:
        odds = -round((prob / (1 - prob)) * 100)
        return f"{odds}"
    else:
        odds = round(((1 - prob) / prob) * 100)
        return f"+{odds}"


@st.cache_data(ttl=1800)
def get_super_bowl_futures() -> list[dict]:
    """
    Fetch Super Bowl winner futures from The Odds API.
    Falls back to Elo simulation if API is unavailable or offseason.
    Returns list of {team_name, abbr, odds_american, implied_prob, source}.
    """
    # Try outrights market first
    for sport_key in ["americanfootball_nfl", "americanfootball_nfl_super_bowl_winner"]:
        try:
            r = requests.get(
                f"{ODDS_BASE}/sports/{sport_key}/odds",
                params={
                    "apiKey": ODDS_API_KEY,
                    "regions": "us",
                    "markets": "outrights",
                    "oddsFormat": "american",
                    "bookmakers": "draftkings,fanduel,betmgm",
                },
                timeout=10,
            )
            if r.status_code == 200:
                events = r.json()
                if events:
                    return _parse_odds_response(events)
        except Exception:
            continue

    # Try sports list to find futures-specific key
    try:
        r = requests.get(f"{ODDS_BASE}/sports", params={"apiKey": ODDS_API_KEY}, timeout=8)
        if r.status_code == 200:
            sports = r.json()
            nfl_futures = [s for s in sports if "nfl" in s.get("key", "").lower() and
                           ("super" in s.get("title", "").lower() or "championship" in s.get("title", "").lower())]
            for sport in nfl_futures:
                try:
                    r2 = requests.get(
                        f"{ODDS_BASE}/sports/{sport['key']}/odds",
                        params={"apiKey": ODDS_API_KEY, "regions": "us",
                                "markets": "h2h,outrights", "oddsFormat": "american"},
                        timeout=10,
                    )
                    if r2.status_code == 200 and r2.json():
                        return _parse_odds_response(r2.json())
                except Exception:
                    continue
    except Exception:
        pass

    # Final fallback: Elo-based simulation
    return elo_championship_probabilities()


def _parse_odds_response(events: list) -> list[dict]:
    """Parse The Odds API response into our standard format."""
    team_odds: dict[str, list[float]] = {}

    for event in events:
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") in ("outrights", "h2h"):
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0)
                        if name and price:
                            team_odds.setdefault(name, []).append(float(price))

    if not team_odds:
        return elo_championship_probabilities()

    results = []
    for team_name, prices in team_odds.items():
        avg_price = sum(prices) / len(prices)
        abbr = TEAM_NAME_TO_ABBR.get(team_name, team_name[:3].upper())
        prob = american_to_prob(avg_price)
        results.append({
            "team_name": team_name,
            "abbr": abbr,
            "odds_american": f"+{int(avg_price)}" if avg_price > 0 else str(int(avg_price)),
            "implied_prob": prob,
            "source": "The Odds API (live)",
        })

    # Normalize probabilities (remove bookmaker vig)
    total_prob = sum(r["implied_prob"] for r in results)
    for r in results:
        r["implied_prob"] = r["implied_prob"] / total_prob

    return sorted(results, key=lambda x: -x["implied_prob"])


# ── Elo-based Monte Carlo playoff simulation ───────────────────────────────────

def _sim_game(team_a: str, team_b: str, elos: dict, neutral: bool = False) -> str:
    """Simulate one game, return winner's abbreviation."""
    elo_a = elos.get(team_a, 1500)
    elo_b = elos.get(team_b, 1500)
    home_bonus = 0 if neutral else 32  # smaller home field for playoffs
    prob_a = 1.0 / (1.0 + 10 ** ((elo_b - elo_a - home_bonus) / 400))
    return team_a if np.random.random() < prob_a else team_b


def _sim_conference(seeds: list[str], elos: dict) -> str:
    """
    Simulate a conference playoff bracket.
    seeds: 7 teams ordered 1-seed to 7-seed (1-seed gets a bye).
    Returns the conference champion.
    """
    # Wild card round: 2v7, 3v6, 4v5
    wc_winners = [
        seeds[0],  # 1-seed has bye
        _sim_game(seeds[1], seeds[6], elos),  # 2 vs 7
        _sim_game(seeds[2], seeds[5], elos),  # 3 vs 6
        _sim_game(seeds[3], seeds[4], elos),  # 4 vs 5
    ]
    # Divisional: 1 vs lowest remaining seed winner, top WC vs next
    div1 = _sim_game(wc_winners[0], wc_winners[3], elos)  # 1 vs winner(4/5)
    div2 = _sim_game(wc_winners[1], wc_winners[2], elos)  # winner(2/7) vs winner(3/6)
    # Conference championship
    return _sim_game(div1, div2, elos, neutral=False)


def elo_championship_probabilities(n_sims: int = 25_000) -> list[dict]:
    """
    Monte Carlo simulation of NFL playoffs using Elo ratings.
    Simulates n_sims seasons and counts Super Bowl wins per team.
    """
    elos = get_all_elos()
    champions: dict[str, int] = {t: 0 for t in list(AFC_TEAMS) + list(NFC_TEAMS)}
    sb_appearances: dict[str, int] = {t: 0 for t in list(AFC_TEAMS) + list(NFC_TEAMS)}

    afc_elos = [(elos.get(t, 1500), t) for t in AFC_TEAMS]
    nfc_elos = [(elos.get(t, 1500), t) for t in NFC_TEAMS]

    rng = np.random.default_rng(seed=42)

    for _ in range(n_sims):
        # Seed top-7 by Elo (with small noise to vary results across sims)
        noise = rng.normal(0, 25, len(afc_elos))
        afc_seeded = sorted(
            [(elo + n, t) for (elo, t), n in zip(afc_elos, noise)],
            reverse=True
        )[:7]
        noise = rng.normal(0, 25, len(nfc_elos))
        nfc_seeded = sorted(
            [(elo + n, t) for (elo, t), n in zip(nfc_elos, noise)],
            reverse=True
        )[:7]

        afc_seeds = [t for _, t in afc_seeded]
        nfc_seeds = [t for _, t in nfc_seeded]

        afc_champ = _sim_conference(afc_seeds, elos)
        nfc_champ = _sim_conference(nfc_seeds, elos)

        sb_appearances[afc_champ] = sb_appearances.get(afc_champ, 0) + 1
        sb_appearances[nfc_champ] = sb_appearances.get(nfc_champ, 0) + 1

        sb_winner = _sim_game(afc_champ, nfc_champ, elos, neutral=True)
        champions[sb_winner] = champions.get(sb_winner, 0) + 1

    results = []
    for team, wins in champions.items():
        prob = wins / n_sims
        if prob > 0:
            results.append({
                "team_name": _abbr_to_name(team),
                "abbr": team,
                "odds_american": prob_to_american(prob),
                "implied_prob": prob,
                "sb_appearances_pct": sb_appearances.get(team, 0) / n_sims,
                "source": "Elo Monte Carlo simulation",
            })

    return sorted(results, key=lambda x: -x["implied_prob"])


def _abbr_to_name(abbr: str) -> str:
    reverse = {v: k for k, v in TEAM_NAME_TO_ABBR.items()}
    return reverse.get(abbr, abbr)
