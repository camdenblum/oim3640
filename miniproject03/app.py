"""
app.py
Flask web app – MBTA Stop Finder
Run with:  python app.py
"""

import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from mbta_helper import get_lat_lng, get_nearest_mbta_stop

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

MAPBOX_KEY = os.environ.get("MAP_BOX_KEY")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    place_name = request.form.get("place_name", "").strip()

    if not place_name:
        return render_template("index.html", error="Please enter a place name.")

    try:
        lat, lng = get_lat_lng(place_name)
        stop = get_nearest_mbta_stop(lat, lng)
    except ValueError as e:
        return render_template("index.html", error=str(e))
    except Exception as e:
        return render_template("index.html", error=f"API error: {e}")

    return render_template(
        "result.html",
        place_name=place_name,
        stop=stop,
        search_lat=lat,
        search_lng=lng,
        mapbox_key=MAPBOX_KEY,
    )


if __name__ == "__main__":
    app.run(debug=True)
