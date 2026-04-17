"""
mbta_helper.py
Helper functions for geocoding (Mapbox) and finding the nearest MBTA stop.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

MAP_BOX_KEY = os.environ.get("MAP_BOX_KEY")
MBTA_KEY = os.environ.get("MBTA_KEY")

MAPBOX_BASE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
MBTA_BASE_URL = "https://api-v3.mbta.com"


def get_lat_lng(place_name: str) -> tuple:
    """
    Convert a place name or address into (latitude, longitude) using the
    Mapbox Geocoding API.  Raises ValueError if the place cannot be found.
    """
    url = f"{MAPBOX_BASE_URL}/{requests.utils.quote(place_name)}.json"
    params = {
        "access_token": MAP_BOX_KEY,
        "limit": 1,
        # Bounding box for Greater Boston so results stay relevant
        "bbox": "-71.7,42.0,-70.5,42.7",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    features = response.json().get("features", [])
    if not features:
        raise ValueError(f'Could not find location: "{place_name}"')

    longitude, latitude = features[0]["center"]
    return latitude, longitude


def get_nearest_mbta_stop(latitude: float, longitude: float) -> dict:
    """
    Return a dict with details about the MBTA stop closest to the given
    coordinates.  Raises ValueError if no stops are found.

    Returned keys: name, latitude, longitude, wheelchair_accessible, municipality
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
        raise ValueError("No MBTA stops found near that location.")

    attrs = stops[0]["attributes"]
    # wheelchair_boarding: 1 = accessible, 2 = not accessible, 0 = no info
    return {
        "name": attrs.get("name", "Unknown"),
        "latitude": attrs.get("latitude"),
        "longitude": attrs.get("longitude"),
        "wheelchair_accessible": attrs.get("wheelchair_boarding") == 1,
        "municipality": attrs.get("municipality", ""),
    }


def find_stop_near(place_name: str) -> tuple:
    """Convenience wrapper: place name -> (stop_name, wheelchair_accessible)."""
    lat, lng = get_lat_lng(place_name)
    stop = get_nearest_mbta_stop(lat, lng)
    return stop["name"], stop["wheelchair_accessible"]


if __name__ == "__main__":
    place = input("Enter a place name or address: ").strip()
    stop_name, accessible = find_stop_near(place)
    print(f"Nearest MBTA stop : {stop_name}")
    print(f"Wheelchair accessible: {'Yes' if accessible else 'No'}")
