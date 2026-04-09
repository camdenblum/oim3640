
from flask import Flask, render_template, request
from datetime import datetime, timezone
import math
import os
import requests

# Load .env file if present (pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)

# ── API Keys ───────────────────────────────────────────────────────────────────
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_KEY')
SPORTSDB_KEY    = os.environ.get("SPORTSDB_KEY", "3")
SPORTSDB_BASE   = f"https://www.thesportsdb.com/api/v1/json/{SPORTSDB_KEY}"

# ── Boston team configuration ──────────────────────────────────────────────────
BOSTON_TEAMS = [
    {"name": "Boston Red Sox",       "id": "135269", "sport": "MLB", "venue": "Fenway Park",     "venue_lat": 42.3467, "venue_lng": -71.0972, "color": "#BD3039", "logo": "⚾"},
    {"name": "Boston Celtics",       "id": "134860", "sport": "NBA", "venue": "TD Garden",        "venue_lat": 42.3662, "venue_lng": -71.0621, "color": "#007A33", "logo": "🏀"},
    {"name": "Boston Bruins",        "id": "134830", "sport": "NHL", "venue": "TD Garden",        "venue_lat": 42.3662, "venue_lng": -71.0621, "color": "#FFB81C", "logo": "🏒"},
    {"name": "New England Patriots", "id": "134920", "sport": "NFL", "venue": "Gillette Stadium", "venue_lat": 42.0909, "venue_lng": -71.2643, "color": "#002244", "logo": "🏈"},
]


def haversine(lat1, lng1, lat2, lng2):
    R = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi    = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def geocode(place: str):
    url    = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": place, "key": GOOGLE_MAPS_KEY, "region": "us", "components": "country:US"}
    resp   = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data   = resp.json()
    status = data.get("status", "")
    if status == "REQUEST_DENIED":
        raise ValueError(f"Google Maps API error: {data.get('error_message', 'API key issue')}")
    if status == "ZERO_RESULTS" or not data.get("results"):
        raise ValueError(f'No location found for "{place}". Try a more specific address.')
    if status not in ("OK", "PARTIAL_MATCH"):
        raise ValueError(f"Geocoding failed (status: {status}).")
    result = data["results"][0]
    loc    = result["geometry"]["location"]
    return loc["lat"], loc["lng"], result["formatted_address"]


def fetch_upcoming_events(team_id: str):
    try:
        resp = requests.get(f"{SPORTSDB_BASE}/eventsnext.php", params={"id": team_id}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("events") or []
    except Exception:
        return []


def parse_event_datetime(event: dict):
    date_str = (event.get("dateEvent") or "").strip()
    time_str = (event.get("strTime")   or "00:00:00").strip()
    if len(time_str) == 5:
        time_str += ":00"
    time_str = time_str[:8]
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def is_home_game(event: dict, team: dict) -> bool:
    home_field = (event.get("strHomeTeam") or "").lower()
    for keyword in team["name"].lower().split():
        if keyword in home_field:
            return True
    return False


def format_game_datetime(dt: datetime):
    date_str = dt.strftime("%A, %B %d, %Y").replace(" 0", " ")
    hour     = dt.strftime("%I").lstrip("0") or "12"
    time_str = f"{hour}:{dt.strftime('%M')} {dt.strftime('%p')} UTC"
    return date_str, time_str


def find_nearest_game(user_lat, user_lng):
    now, candidates = datetime.now(timezone.utc), []
    for team in BOSTON_TEAMS:
        for ev in fetch_upcoming_events(team["id"]):
            if not is_home_game(ev, team):
                continue
            dt = parse_event_datetime(ev)
            if dt is None or dt <= now:
                continue
            display_date, display_time = format_game_datetime(dt)
            candidates.append({
                "team": team["name"], "sport": team["sport"], "venue": team["venue"],
                "venue_lat": team["venue_lat"], "venue_lng": team["venue_lng"],
                "color": team["color"], "logo": team["logo"],
                "opponent": ev.get("strAwayTeam") or "TBD",
                "datetime": dt, "display_date": display_date, "display_time": display_time,
                "distance_mi": round(haversine(user_lat, user_lng, team["venue_lat"], team["venue_lng"]), 1),
                "league": ev.get("strLeague") or team["sport"],
                "round": ev.get("intRound") or "", "status": ev.get("strStatus") or "Scheduled",
            })
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x["datetime"].date(), x["distance_mi"]))
    return candidates[0]


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", google_maps_key=GOOGLE_MAPS_KEY)


@app.route("/find", methods=["POST"])
def find():
    location_input = (request.form.get("location") or "").strip()
    if not location_input:
        return render_template("index.html", google_maps_key=GOOGLE_MAPS_KEY, error="Please enter a location.")
    try:
        user_lat, user_lng, place_name = geocode(location_input)
    except ValueError as e:
        return render_template("index.html", google_maps_key=GOOGLE_MAPS_KEY, error=str(e))
    except Exception as e:
        return render_template("index.html", google_maps_key=GOOGLE_MAPS_KEY,
                               error=f"Location lookup failed — check your GOOGLE_MAPS_KEY. ({e})")
    game = find_nearest_game(user_lat, user_lng)
    if game is None:
        return render_template("index.html", google_maps_key=GOOGLE_MAPS_KEY,
                               error="No upcoming home games found right now. The sports API may also be rate-limited — try again shortly.")
    return render_template("result.html", game=game, user_lat=user_lat, user_lng=user_lng,
                           place_name=place_name, google_maps_key=GOOGLE_MAPS_KEY)


if __name__ == "__main__":
    app.run(debug=True)

