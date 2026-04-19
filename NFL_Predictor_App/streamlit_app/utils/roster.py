"""
Current NFL roster fetcher (April 2026).
Pulls live ESPN rosters + injury status for all 32 teams and merges with
2024 stat projections via name-matching so projections reflect:
  - Which team each player is actually on TODAY
  - Current injury status and adjusted projections
"""
import re
import time
import requests
import streamlit as st
import pandas as pd

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"

# ESPN uses different abbreviations than nfl-data-py for some teams
ESPN_ABBR_TO_STD: dict[str, str] = {
    "WSH": "WAS",   # Washington Commanders
    "LAR": "LA",    # Los Angeles Rams
    "JAC": "JAX",   # Jacksonville Jaguars
    "SL":  "LA",    # legacy
}

def _std_abbr(espn_abbr: str) -> str:
    """Normalize ESPN team abbreviation to nfl-data-py standard."""
    return ESPN_ABBR_TO_STD.get(espn_abbr, espn_abbr)

# Injury multipliers for 17-game season projections
INJURY_FACTOR = {
    "Active":       1.00,
    "Healthy":      1.00,
    "Questionable": 0.88,  # may miss 1-2 games
    "Doubtful":     0.45,  # likely misses several games
    "Out":          0.25,  # short-term, may return mid-season
    "IR":           0.12,  # could return on IR-DtR
    "PUP":          0.60,  # misses first 4 games minimum
    "Suspended":    0.65,
    "NFI":          0.00,  # non-football injury, full season
    "Covid-19":     0.85,
}

# ── Manual name-override table for known mismatches ───────────────────────────
# Maps ESPN fullName → nfl-data-py player_name format (first initial.last)
NAME_OVERRIDES: dict[str, str] = {
    "Patrick Mahomes II": "P.Mahomes",
    "Odell Beckham Jr.":  "O.Beckham",
    "Odell Beckham":      "O.Beckham",
    "AJ Brown":           "A.Brown",
    "JuJu Smith-Schuster":"J.Smith-Schuster",
    "Gabe Davis":         "G.Davis",
    "Travis Etienne Jr.": "T.Etienne",
    "Amon-Ra St. Brown":  "A.St. Brown",
    "Wan'Dale Robinson":  "W.Robinson",
    "De'Von Achane":      "D.Achane",
    "Ja'Marr Chase":      "J.Chase",
    "D'Andre Swift":      "D.Swift",
    "Ka'imi Fairbairn":   "K.Fairbairn",
    "D.K. Metcalf":       "D.Metcalf",
    "CeeDee Lamb":        "C.Lamb",
    "Tank Dell":          "N.Dell",           # Nathaniel "Tank" Dell
    "Mecole Hardman Jr.": "M.Hardman",
    "Kyle Pitts":         "K.Pitts",
    "Sam LaPorta":        "S.LaPorta",
    "Brock Bowers":       "B.Bowers",
}


def _normalize(name: str) -> str:
    """
    Convert any player name to lowercase first_initial.lastname key.
    Handles:
      'Patrick Mahomes'  → 'p.mahomes'
      'P.Mahomes'        → 'p.mahomes'
      'Ja'Marr Chase'    → 'j.chase'
      'JuJu Smith-Schuster' → 'j.smith-schuster'
      'Patrick Mahomes II'  → 'p.mahomes'
    """
    if not name:
        return ""
    name = name.strip()

    # Apply manual overrides first
    override = NAME_OVERRIDES.get(name)
    if override:
        name = override

    # Strip generational suffixes
    name = re.sub(r"\s+\b(Jr\.?|Sr\.?|II|III|IV)\b\.?$", "", name, flags=re.IGNORECASE).strip()

    # Already in abbreviated form like "P.Mahomes" or "J.Smith-Schuster"
    if re.match(r"^[A-Za-z]\.[A-Za-z]", name):
        return name.lower()

    # Full name: take first letter of first word + last word
    parts = name.split()
    if len(parts) >= 2:
        first_initial = parts[0][0]
        last = parts[-1]
        # Handle "D.K. Metcalf" → 'd.metcalf'
        if last.endswith("."):
            last = last[:-1]
        return f"{first_initial}.{last}".lower()

    return name.lower()


def _pos_group(pos: str) -> str:
    """Normalize position into broad group for disambiguation."""
    if pos in ("QB",):                          return "QB"
    if pos in ("RB", "FB", "HB"):               return "RB"
    if pos in ("WR",):                          return "WR"
    if pos in ("TE",):                          return "TE"
    return pos


# ── ESPN roster fetching ──────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_team_roster(team_id: str, team_abbr: str) -> list[dict]:
    """Fetch one team's roster from ESPN."""
    try:
        r = requests.get(f"{ESPN_BASE}/teams/{team_id}/roster", timeout=12)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []

    players = []
    for group in data.get("athletes", []):
        for athlete in group.get("items", []):
            inj_list = athlete.get("injuries") or []
            inj_status = "Active"
            inj_desc = ""
            if inj_list:
                inj = inj_list[0]
                inj_status = inj.get("status", "Active") or "Active"
                inj_desc = inj.get("longDescription") or inj.get("shortDescription") or ""

            pos = (athlete.get("position") or {}).get("abbreviation", "")
            full_name = athlete.get("fullName", "")

            players.append({
                "espn_id":    athlete.get("id", ""),
                "full_name":  full_name,
                "norm_key":   _normalize(full_name),
                "position":   pos,
                "pos_group":  _pos_group(pos),
                "jersey":     athlete.get("jersey", ""),
                "age":        athlete.get("age"),
                "team_abbr":  _std_abbr(team_abbr),
                "inj_status": inj_status,
                "inj_desc":   inj_desc,
                "inj_factor": INJURY_FACTOR.get(inj_status, 1.0),
            })
    return players


@st.cache_data(ttl=1800, show_spinner="Fetching current rosters from ESPN…")
def get_all_current_rosters() -> pd.DataFrame:
    """
    Fetch current rosters for all 32 NFL teams.
    Returns a DataFrame with one row per player including injury status.
    Calls ESPN API once per team; cached for 30 minutes.
    """
    # Get all teams with ESPN IDs
    try:
        r = requests.get(f"{ESPN_BASE}/teams", params={"limit": 32}, timeout=10)
        r.raise_for_status()
        espn_teams = r.json()
    except Exception:
        return pd.DataFrame()

    all_players: list[dict] = []
    teams_list = (espn_teams.get("sports") or [{}])[0]\
                            .get("leagues", [{}])[0]\
                            .get("teams", [])

    for item in teams_list:
        t = item.get("team", {})
        team_id  = t.get("id", "")
        team_abbr = t.get("abbreviation", "")
        if team_id:
            players = _fetch_team_roster(team_id, team_abbr)
            all_players.extend(players)
            time.sleep(0.05)   # gentle pacing — ESPN is a public API

    return pd.DataFrame(all_players) if all_players else pd.DataFrame()


# ── Projection ↔ Roster merge ─────────────────────────────────────────────────

def merge_projections_with_roster(proj_df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine nfl-data-py 2024 projections with live ESPN roster data.

    For each projected player:
      - Try to find them on a current ESPN roster by name-key + position
      - Update current_team to reflect free-agency / trades
      - Attach injury status and apply injury adjustment factor
      - Flag team changes and unmatched players

    Returns enriched DataFrame.
    """
    roster_df = get_all_current_rosters()

    if roster_df.empty:
        proj_df = proj_df.copy()
        proj_df["current_team"]    = proj_df["recent_team"]
        proj_df["team_changed"]    = False
        proj_df["inj_status"]      = "Active"
        proj_df["inj_desc"]        = ""
        proj_df["inj_factor"]      = 1.0
        proj_df["on_roster"]       = False
        return proj_df

    # ── Build lookup: (norm_key, pos_group) → roster row ──────────────────────
    # Primary lookup: exact key + position
    primary: dict[tuple, dict] = {}
    # Secondary lookup: key only (for position-agnostic fallback)
    secondary: dict[str, list[dict]] = {}

    for _, row in roster_df.iterrows():
        key = (row["norm_key"], row["pos_group"])
        entry = row.to_dict()
        primary[key] = entry
        secondary.setdefault(row["norm_key"], []).append(entry)

    # ── Match projected players to current roster ──────────────────────────────
    result = proj_df.copy()
    result["norm_key"]      = result["player_name"].apply(_normalize)
    result["current_team"]  = result["recent_team"]
    result["team_changed"]  = False
    result["inj_status"]    = "Active"
    result["inj_desc"]      = ""
    result["inj_factor"]    = 1.0
    result["on_roster"]     = False

    for idx, row in result.iterrows():
        nkey = row["norm_key"]
        pgrp = _pos_group(row["position"])

        match = primary.get((nkey, pgrp))
        if match is None:
            # Fallback: key without position constraint (unique match only)
            candidates = secondary.get(nkey, [])
            if len(candidates) == 1:
                match = candidates[0]

        if match:
            current_team = match["team_abbr"]
            result.at[idx, "current_team"]  = current_team
            result.at[idx, "team_changed"]  = (current_team != row["recent_team"])
            result.at[idx, "inj_status"]    = match["inj_status"]
            result.at[idx, "inj_desc"]      = match["inj_desc"]
            result.at[idx, "inj_factor"]    = match["inj_factor"]
            result.at[idx, "on_roster"]     = True

    # ── Apply injury adjustment to all projected stat columns ─────────────────
    proj_cols = [c for c in result.columns if c.endswith("_proj")]
    for col in proj_cols:
        result[col] = (result[col] * result["inj_factor"]).round(1)
        # Also re-derive floor/ceil from adjusted projection
        floor_col = col.replace("_proj", "_floor")
        ceil_col  = col.replace("_proj", "_ceil")
        if floor_col in result.columns:
            result[floor_col] = (result[col] * 0.75).round(1)
        if ceil_col in result.columns:
            result[ceil_col]  = (result[col] * 1.30).round(1)

    # ── Also add players ON current rosters who have NO 2024 projection ────────
    # (e.g. free-agent signings, trade acquisitions new to team)
    matched_keys = set(result[result["on_roster"]]["norm_key"].tolist())
    new_rows: list[dict] = []
    for _, rp in roster_df.iterrows():
        if rp["norm_key"] in matched_keys:
            continue
        if rp["pos_group"] not in ("QB", "RB", "WR", "TE"):
            continue
        new_rows.append({
            "player_name":      rp["full_name"],
            "player_id":        f"ESPN-{rp['espn_id']}",
            "recent_team":      _std_abbr(rp["team_abbr"]),
            "position":         rp["pos_group"],
            "games":            0,
            "current_team":     _std_abbr(rp["team_abbr"]),
            "team_changed":     False,
            "inj_status":       rp["inj_status"],
            "inj_desc":         rp["inj_desc"],
            "inj_factor":       rp["inj_factor"],
            "on_roster":        True,
            "norm_key":         rp["norm_key"],
            # All stat projections → NaN (no historical data)
        })

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        result = pd.concat([result, new_df], ignore_index=True)

    return result


def injury_badge(status: str) -> str:
    """Return a colored emoji badge for injury status."""
    return {
        "Active":       "🟢 Active",
        "Healthy":      "🟢 Active",
        "Questionable": "🟡 Questionable",
        "Doubtful":     "🟠 Doubtful",
        "Out":          "🔴 Out",
        "IR":           "⚫ IR",
        "PUP":          "⚫ PUP",
        "Suspended":    "🔵 Suspended",
        "NFI":          "⚫ NFI",
    }.get(status, f"⚪ {status}")
