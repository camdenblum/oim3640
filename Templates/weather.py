from flask import Flask, request, jsonify, render_template_string
import os
import requests

app = Flask(__name__)

WEATHER_PAGE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Weather Lookup</title>
    <style>
      :root{--bg:#f6f8fb;--card:#ffffff;--accent:#1e88e5}
      body{font-family:Inter,system-ui,Segoe UI,Arial,sans-serif;background:var(--bg);margin:0;padding:2rem}
      .container{max-width:760px;margin:0 auto}
      .card{background:var(--card);border-radius:12px;padding:1.25rem;box-shadow:0 6px 18px rgba(14,30,37,0.08)}
      h1{margin:0 0 0.5rem 0;font-size:1.25rem}
      form{display:flex;gap:.5rem;align-items:center}
      input[type="text"]{flex:1;padding:.6rem .75rem;border:1px solid #e6eef9;border-radius:8px;font-size:1rem}
      button{background:var(--accent);color:white;border:none;padding:.6rem .9rem;border-radius:8px;cursor:pointer}
      .meta{color:#556; font-size:.9rem;margin-top:.5rem}
      .weather-row{display:flex;align-items:center;gap:1rem;margin-top:1rem}
      .temp{font-size:2.3rem;font-weight:600}
      .desc{font-size:1rem;color:#234}
      .details{margin-left:auto;text-align:right;color:#445}
      .icon{width:96px;height:96px}
      .note{margin-top:.6rem;font-size:.9rem;color:#b02}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="card">
        <h1>Weather Lookup</h1>
        <form method="post" action="/weather">
          <input name="location" type="text" placeholder="City name or city,country (e.g. 'Boston' or 'London,UK')" value="{{ location or '' }}">
          <button type="submit">Get Weather</button>
        </form>

        {% if missing_key %}
          <div class="note">OPENWEATHER_API_KEY is not set. Set it in your environment to fetch live weather.</div>
        {% endif %}

        {% if error %}
          <div class="note">{{ error }}</div>
        {% endif %}

        {% if weather %}
          <div class="weather-row">
            <img class="icon" src="{{ weather.icon_url }}" alt="{{ weather.description }}">
            <div>
              <div class="temp">{{ weather.temp_c }}°C / {{ weather.temp_f }}°F</div>
              <div class="desc">{{ weather.description }}</div>
              <div class="meta">{{ weather.location_name }} • Humidity {{ weather.humidity }}% • Wind {{ weather.wind_kph }} km/h</div>
            </div>
            <div class="details">
              <div>Feels like <strong>{{ weather.feels_c }}°C</strong></div>
              <div class="meta">Data from OpenWeather</div>
            </div>
          </div>
        {% endif %}
      </div>
    </div>
  </body>
</html>
"""


def fetch_weather(location: str):
    """Fetch weather from OpenWeatherMap for a given location string.
    Returns (data_dict, error_str, missing_key_bool).
    """
    key = os.getenv('OPENWEATHER_API_KEY')
    if not key:
        return None, None, True

    params = {
        'q': location,
        'appid': key,
        'units': 'metric'
    }
    try:
        resp = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        if data.get('cod') != 200:
            return None, data.get('message', 'Unknown error'), False

        w = data['weather'][0]
        main = data['main']
        wind = data.get('wind', {})
        temp_c = round(main.get('temp'), 1)
        temp_f = round((temp_c * 9/5) + 32, 1) if temp_c is not None else None
        feels_c = round(main.get('feels_like'), 1) if main.get('feels_like') is not None else None
        humidity = main.get('humidity')
        wind_kph = round((wind.get('speed', 0) * 3.6), 1)
        icon = w.get('icon')
        icon_url = f'https://openweathermap.org/img/wn/{icon}@4x.png' if icon else ''
        description = w.get('description', '').title()
        location_name = f"{data.get('name')}, {data.get('sys', {}).get('country','')}"

        return {
            'temp_c': temp_c,
            'temp_f': temp_f,
            'feels_c': feels_c,
            'humidity': humidity,
            'wind_kph': wind_kph,
            'icon_url': icon_url,
            'description': description,
            'location_name': location_name
        }, None, False

    except requests.exceptions.RequestException as e:
        return None, 'Network error while fetching weather.', False
    except Exception:
        return None, 'Unexpected error while processing weather data.', False


@app.route('/')
def index():
    return render_template_string(WEATHER_PAGE, weather=None, error=None, missing_key=False, location='')


@app.route('/weather', methods=['GET', 'POST'])
def weather_page():
    location = ''
    if request.method == 'POST':
        location = (request.form.get('location') or '').strip()
    else:
        location = (request.args.get('location') or '').strip()

    if not location:
        return render_template_string(WEATHER_PAGE, weather=None, error=None, missing_key=False, location='')

    weather, error, missing_key = fetch_weather(location)
    return render_template_string(WEATHER_PAGE, weather=weather, error=error, missing_key=missing_key, location=location)


@app.route('/api/weather')
def weather_api():
    location = (request.args.get('location') or '').strip()
    if not location:
        return jsonify({'error': 'location query parameter required'}), 400
    weather, error, missing_key = fetch_weather(location)
    if missing_key:
        return jsonify({'error': 'OPENWEATHER_API_KEY not set in environment'}), 500
    if error:
        return jsonify({'error': error}), 404
    return jsonify(weather)


if __name__ == '__main__':
    app.run(debug=True)
