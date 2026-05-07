
## What I'm Building

I'm building a Flask-based web application that helps users locate the nearest MBTA transit stop from any address or place name they enter. The app works by taking a user's text input and first sending it to the Mapbox Geocoding API to convert the location into geographic coordinates (latitude and longitude). Those coordinates are then passed to the MBTA V3 API, which returns the closest transit stop along with its route and distance. The final result — the stop name, the line it serves, the distance from the searched location, and ideally an interactive map — is displayed back to the user through a clean web interface. The full stack runs on Python and Flask, with all API calls handled server-side and results surfaced through rendered HTML templates.


## Why I Chose This

I chose this project because it combines everything I've been learning in a way that produces something actually usable. Writing isolated scripts and functions is useful for learning, but this project forces me to think about how all the pieces connect, how a form submission triggers a chain of API calls, how data flows between the backend and the frontend, and how errors need to be handled gracefully so the app doesn't break for the user. I'm also drawn to the local relevance of the MBTA; it's a real service I interact with, which makes debugging and testing feel meaningful rather than abstract. Using Mapbox adds a visual layer that makes the output genuinely satisfying to see.


## Core Features

The app will include a homepage with a simple text input form where users can type any place name or address in the Greater Boston area. On submission, the Flask backend will call the Mapbox Geocoding API to resolve the input into coordinates, then query the MBTA V3 API with those coordinates to retrieve the nearest stop. The results page will display the stop name, the MBTA line or route it serves, the transit mode (subway, bus, or commuter rail), and the approximate walking distance from the searched location. As a stretch goal, I plan to embed an interactive Mapbox map on the results page that shows both the searched location and the nearest stop with labeled pins and a line connecting them. All API keys will be managed securely using a .env file that is excluded from version control via .gitignore.


## What I Don't Know Yet

I'm not yet sure how to handle the case where a user enters a location that falls completely outside the MBTA service area I need to think through how to detect that and return a useful error message rather than a confusing result. I also haven't worked with embedding a Mapbox map directly in an HTML template before, so I'll need to explore the Mapbox GL JS documentation to understand how to pass coordinates from Flask into the frontend JavaScript. Additionally, I'm uncertain about rate limits on both APIs and whether I need to add any caching or throttling logic for repeated searches. Finally, I want to understand whether the MBTA API returns stops for all modes of transit (subway, bus, commuter rail) or if I need to filter by type, and which would be most useful to surface first.

## AI Note: 
