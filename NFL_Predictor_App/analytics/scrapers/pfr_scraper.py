"""
Pro Football Reference scraper with rate limiting and disk caching.
Respects PFR's robots.txt — only scrapes static stat pages.
"""
import time
import hashlib
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd

CACHE_DIR = Path(__file__).parent.parent / "cache" / "pfr"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DELAY_SECONDS = 3.5  # Well under PFR's rate limit


def fetch_pfr_page(url: str, cache_hours: int = 24) -> BeautifulSoup:
    """Fetch a PFR page with disk caching and rate limiting."""
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.html"

    if cache_file.exists():
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours < cache_hours:
            return BeautifulSoup(cache_file.read_text(encoding="utf-8"), "lxml")

    time.sleep(DELAY_SECONDS)
    headers = {
        "User-Agent": "Mozilla/5.0 (research project; not commercial)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.5",
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    cache_file.write_text(response.text, encoding="utf-8")
    return BeautifulSoup(response.text, "lxml")


def get_team_stats_table(team_abbr: str, year: int) -> pd.DataFrame:
    """Scrape a team's season stats page from PFR."""
    pfr_map = {
        "ARI": "crd", "ATL": "atl", "BAL": "rav", "BUF": "buf", "CAR": "car",
        "CHI": "chi", "CIN": "cin", "CLE": "cle", "DAL": "dal", "DEN": "den",
        "DET": "det", "GB": "gnb", "HOU": "htx", "IND": "clt", "JAX": "jax",
        "KC": "kan", "LV": "rai", "LAC": "sdg", "LA": "ram", "MIA": "mia",
        "MIN": "min", "NE": "nwe", "NO": "nor", "NYG": "nyg", "NYJ": "nyj",
        "PHI": "phi", "PIT": "pit", "SF": "sfo", "SEA": "sea", "TB": "tam",
        "TEN": "oti", "WAS": "was",
    }
    pfr_abbr = pfr_map.get(team_abbr.upper(), team_abbr.lower())
    url = f"https://www.pro-football-reference.com/teams/{pfr_abbr}/{year}.htm"
    try:
        soup = fetch_pfr_page(url)
        tables = pd.read_html(str(soup))
        return tables[1] if len(tables) > 1 else tables[0]
    except Exception as e:
        print(f"Could not fetch PFR data for {team_abbr} {year}: {e}")
        return pd.DataFrame()


def get_player_game_log(pfr_player_id: str, year: int) -> pd.DataFrame:
    """Scrape a player's game log from PFR."""
    url = f"https://www.pro-football-reference.com/players/{pfr_player_id[0]}/{pfr_player_id}/gamelog/{year}/"
    try:
        soup = fetch_pfr_page(url, cache_hours=6)
        tables = pd.read_html(str(soup))
        if not tables:
            return pd.DataFrame()
        df = tables[0]
        # Remove header rows embedded in table body
        df = df[df.iloc[:, 0] != df.columns[0]]
        return df
    except Exception as e:
        print(f"Could not fetch game log for {pfr_player_id}: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    # Test
    df = get_team_stats_table("KC", 2024)
    print(df.head())
