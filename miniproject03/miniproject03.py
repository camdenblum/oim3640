"""
miniproject03.py
MBTA Stop Finder – Flask web application

Allows a user to type any Boston-area place name or address and get back the
nearest MBTA transit stop, along with an interactive Mapbox map showing both
the searched location and the stop.

APIs used:
  - Mapbox Geocoding API  (place name -> lat/lng)
  - MBTA V3 API           (lat/lng -> nearest stop)

Run:
    python miniproject03.py
then open http://127.0.0.1:5000 in your browser.

Environment variables (stored in a .env file one level up):
    MAP_BOX_KEY   – Mapbox public access token
    MBTA_KEY      – MBTA V3 API key (optional but raises rate limits)
"""

import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

MAP_BOX_KEY = os.environ.get("MAP_BOX_KEY", "")
MBTA_KEY = os.environ.get("MBTA_KEY", "")

MAPBOX_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
MBTA_BASE_URL = "https://api-v3.mbta.com"

# Greater-Boston bounding box used to bias Mapbox results toward the MBTA
# service area: [min_lng, min_lat, max_lng, max_lat]
BOSTON_BBOX = "-71.7,42.0,-70.5,42.7"

# ---------------------------------------------------------------------------
# Helper: Geocoding (Mapbox)
# ---------------------------------------------------------------------------


def get_lat_lng(place_name: str) -> tuple[float, float]:
    """
    Convert a place name or street address into (latitude, longitude) using
    the Mapbox Geocoding API.

    Raises ValueError if the location cannot be resolved (e.g. it is outside
    the Greater Boston bounding box or the name is unrecognisable).
    Raises requests.HTTPError on non-2xx API responses.
    """
    encoded = requests.utils.quote(place_name)
    url = f"{MAPBOX_BASE_URL}/{encoded}.json"
    params = {
        "access_token": MAP_BOX_KEY,
        "limit": 1,
        "bbox": BOSTON_BBOX,
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    features = response.json().get("features", [])
    if not features:
        raise ValueError(
            f'Could not find "{place_name}" in the Greater Boston area. '
            "Try a more specific address or landmark name."
        )

    # Mapbox returns coordinates as [longitude, latitude]
    longitude, latitude = features[0]["center"]
    return latitude, longitude


# ---------------------------------------------------------------------------
# Helper: Nearest MBTA stop
# ---------------------------------------------------------------------------


def get_nearest_mbta_stop(latitude: float, longitude: float) -> dict:
    """
    Query the MBTA V3 API for the stop closest to the given coordinates.

    Returns a dict with the following keys:
        name                 – human-readable stop name
        latitude / longitude – stop coordinates
        wheelchair_accessible – True if wheelchair_boarding == 1
        municipality         – city/town name (may be empty string)

    Raises ValueError if no stops are found near the coordinates.
    Raises requests.HTTPError on non-2xx API responses.
    """
    url = f"{MBTA_BASE_URL}/stops"
    params = {
        "filter[latitude]": latitude,
        "filter[longitude]": longitude,
        "sort": "distance",
        "page[limit]": 1,
    }
    headers = {"x-api-key": MBTA_KEY} if MBTA_KEY else {}

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    stops = response.json().get("data", [])
    if not stops:
        raise ValueError(
            "No MBTA stops were found near that location. "
            "The address may be outside the MBTA service area."
        )

    attrs = stops[0]["attributes"]
    # wheelchair_boarding values: 1 = accessible, 2 = not accessible, 0 = unknown
    return {
        "name": attrs.get("name", "Unknown Stop"),
        "latitude": attrs.get("latitude"),
        "longitude": attrs.get("longitude"),
        "wheelchair_accessible": attrs.get("wheelchair_boarding") == 1,
        "municipality": attrs.get("municipality", ""),
    }


# ---------------------------------------------------------------------------
# Convenience wrapper (also useful for testing from the command line)
# ---------------------------------------------------------------------------


def find_stop_near(place_name: str) -> tuple[str, bool]:
    """Return (stop_name, wheelchair_accessible) for the nearest stop."""
    lat, lng = get_lat_lng(place_name)
    stop = get_nearest_mbta_stop(lat, lng)
    return stop["name"], stop["wheelchair_accessible"]


# ---------------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    """Render the homepage with the search form."""
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    """
    Handle form submission:
      1. Read the user's input.
      2. Geocode it with Mapbox.
      3. Find the nearest MBTA stop.
      4. Render the results page (or surface an error on the homepage).
    """
    place_name = request.form.get("place_name", "").strip()

    if not place_name:
        return render_template("index.html", error="Please enter a place name or address.")

    try:
        lat, lng = get_lat_lng(place_name)
        stop = get_nearest_mbta_stop(lat, lng)
    except ValueError as exc:
        # Expected errors: unrecognised location, out-of-area, no stops found
        return render_template("index.html", error=str(exc))
    except requests.HTTPError as exc:
        return render_template("index.html", error=f"API error ({exc.response.status_code}): check your API keys.")
    except requests.RequestException as exc:
        return render_template("index.html", error=f"Network error: {exc}")

    return render_template(
        "result.html",
        place_name=place_name,
        stop=stop,
        search_lat=lat,
        search_lng=lng,
        mapbox_key=MAP_BOX_KEY,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Command-line mode: quick lookup without starting the web server
    import sys

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        try:
            stop_name, accessible = find_stop_near(query)
            print(f"Nearest MBTA stop : {stop_name}")
            print(f"Wheelchair accessible: {'Yes' if accessible else 'No'}")
        except (ValueError, requests.RequestException) as err:
            print(f"Error: {err}")
    else:
        # Web server mode
        app.run(debug=True)
