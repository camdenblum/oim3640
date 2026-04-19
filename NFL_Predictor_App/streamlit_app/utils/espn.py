"""ESPN Public API helpers — no API key required."""
import requests
import streamlit as st
from datetime import datetime

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
ESPN_CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl"


def get_current_season() -> int:
    now = datetime.now()
    return now.year if now.month >= 9 else now.year - 1


@st.cache_data(ttl=60)
def get_current_week() -> int:
    try:
        r = requests.get(f"{ESPN_BASE}/scoreboard", timeout=8)
        r.raise_for_status()
        return r.json().get("week", {}).get("number", 1)
    except Exception:
        return 1


@st.cache_data(ttl=120)
def get_scoreboard(week: int | None = None, season: int | None = None) -> list[dict]:
    """Fetch NFL scoreboard. Returns list of game dicts."""
    params: dict = {}
    if week and season:
        params = {"seasontype": 2, "week": week, "dates": season}
    try:
        r = requests.get(f"{ESPN_BASE}/scoreboard", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    games = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue

        status = event.get("status", {}).get("type", {})
        home_team = home.get("team", {})
        away_team = away.get("team", {})

        broadcasts = comp.get("broadcasts", [])
        broadcast = broadcasts[0].get("names", [""])[0] if broadcasts else ""

        games.append({
            "id": event.get("id", ""),
            "date": event.get("date", ""),
            "week": data.get("week", {}).get("number", week or 1),
            "status_name": status.get("name", ""),
            "status_detail": event.get("status", {}).get("type", {}).get("shortDetail", ""),
            "completed": status.get("completed", False),
            "home_id": home_team.get("id", ""),
            "home_name": home_team.get("displayName", ""),
            "home_abbr": home_team.get("abbreviation", "???"),
            "home_score": int(home.get("score", 0) or 0),
            "home_color": "#" + (home_team.get("color") or "013369"),
            "home_logo": (home_team.get("logos") or [{}])[0].get("href", ""),
            "home_record": home.get("records", [{}])[0].get("summary", "") if home.get("records") else "",
            "away_id": away_team.get("id", ""),
            "away_name": away_team.get("displayName", ""),
            "away_abbr": away_team.get("abbreviation", "???"),
            "away_score": int(away.get("score", 0) or 0),
            "away_color": "#" + (away_team.get("color") or "D50A0A"),
            "away_logo": (away_team.get("logos") or [{}])[0].get("href", ""),
            "away_record": away.get("records", [{}])[0].get("summary", "") if away.get("records") else "",
            "venue": comp.get("venue", {}).get("fullName", ""),
            "broadcast": broadcast,
        })
    return games


@st.cache_data(ttl=3600)
def get_all_teams() -> list[dict]:
    """Fetch all 32 NFL teams."""
    try:
        r = requests.get(f"{ESPN_BASE}/teams", params={"limit": 32}, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    teams = []
    for item in (data.get("sports") or [{}])[0].get("leagues", [{}])[0].get("teams", []):
        t = item.get("team", {})
        teams.append({
            "id": t.get("id", ""),
            "name": t.get("displayName", ""),
            "abbr": t.get("abbreviation", ""),
            "city": t.get("location", ""),
            "nickname": t.get("name", ""),
            "color": "#" + (t.get("color") or "013369"),
            "alt_color": "#" + (t.get("alternateColor") or "ffffff"),
            "logo": (t.get("logos") or [{}])[0].get("href", ""),
        })
    return teams


@st.cache_data(ttl=1800)
def get_standings() -> list[dict]:
    """Fetch NFL standings by conference/division."""
    try:
        r = requests.get(
            "https://site.api.espn.com/apis/v2/sports/football/nfl/standings",
            params={"season": get_current_season()},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    rows = []
    for conf in data.get("children", []):
        conf_name = conf.get("abbreviation", conf.get("name", ""))
        for div in conf.get("children", []):
            div_name = div.get("name", "")
            for entry in div.get("standings", {}).get("entries", []):
                team = entry.get("team", {})
                stats = {s["name"]: s.get("value", 0) for s in entry.get("stats", [])}
                rows.append({
                    "id": team.get("id", ""),
                    "name": team.get("displayName", ""),
                    "abbr": team.get("abbreviation", ""),
                    "logo": (team.get("logos") or [{}])[0].get("href", "") if team.get("logos") else "",
                    "conference": conf_name,
                    "division": div_name,
                    "wins": int(stats.get("wins", 0)),
                    "losses": int(stats.get("losses", 0)),
                    "ties": int(stats.get("ties", 0)),
                    "pct": float(stats.get("winPercent", 0)),
                    "pf": int(stats.get("pointsFor", 0)),
                    "pa": int(stats.get("pointsAgainst", 0)),
                    "diff": int(stats.get("pointDifferential", 0)),
                    "streak": str(stats.get("streak", "")),
                    "home": str(stats.get("home", "")),
                    "away": str(stats.get("away", "")),
                    "div": str(stats.get("vsDiv", "")),
                })
    return rows


@st.cache_data(ttl=3600)
def get_team_roster(team_id: str) -> list[dict]:
    """Fetch roster for a given ESPN team ID."""
    try:
        r = requests.get(f"{ESPN_BASE}/teams/{team_id}/roster", timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    players = []
    for group in data.get("athletes", []):
        for athlete in group.get("items", []):
            inj = (athlete.get("injuries") or [{}])[0]
            players.append({
                "id": athlete.get("id", ""),
                "name": athlete.get("fullName", ""),
                "position": athlete.get("position", {}).get("abbreviation", ""),
                "jersey": athlete.get("jersey", ""),
                "age": athlete.get("age", ""),
                "status": inj.get("status", "Active") if inj else "Active",
            })
    return players
