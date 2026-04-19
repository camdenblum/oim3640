# NFL Predictor — Advanced Analytics Platform

ML-powered NFL game predictions, player projections, and advanced analytics. Every prediction is explainable, data-driven, and continuously updated as the season progresses.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + TailwindCSS + Recharts/D3 |
| Backend | Node.js + Express + TypeScript |
| Analytics | Python 3.11 + FastAPI + XGBoost + scikit-learn |
| Database | PostgreSQL 15 + Redis |
| Data | ESPN Public API · NFLverse · Pro Football Reference · OpenWeatherMap |

## Quick Start (Docker)

```bash
cp .env.example .env
# Add your free API keys to .env (see below)
docker-compose up
```

Then open http://localhost:3000

## Quick Start (Local Dev)

```bash
# Requires: Node 20+, Python 3.11+, PostgreSQL, Redis
cp .env.example .env
chmod +x start.sh && ./start.sh
```

## Free API Keys Required

| Service | URL | Used For |
|---------|-----|----------|
| OpenWeatherMap | openweathermap.org/api | Weather impact on outdoor games |
| The Odds API | the-odds-api.com | Vegas implied totals for calibration |
| MySportsFeeds | mysportsfeeds.com/data-feeds/signup | Depth charts (optional backup) |

ESPN and NFLverse require **no keys** — they're fully public.

## Architecture

```
nfl-predictor/
├── frontend/          React app (port 3000)
│   ├── src/pages/     14 full pages
│   ├── src/components/Reusable UI components
│   └── src/utils/     Stat calculation helpers
├── backend/           Express API (port 3001)
│   ├── src/routes/    REST endpoints for all resources
│   ├── src/services/  Business logic + DB queries
│   └── src/jobs/      Cron jobs (ESPN sync, game updates)
├── analytics/         Python FastAPI (port 8001)
│   ├── api.py         Prediction endpoints
│   ├── updater.py     Weekly model retraining
│   ├── predictors/    Game + player ML models
│   ├── pipelines/     Feature engineering
│   └── scrapers/      PFR scraper with caching
└── database/
    └── seeds/         Historical data seeder (NFLverse)
```

## Model Architecture

**Game Predictions** — Ensemble of:
1. **Elo System** — K=20, home field = +65 Elo pts, MOV multiplier
2. **XGBoost Classifier** — 42+ features, walk-forward CV
3. **Monte Carlo Simulation** — 10,000 iterations for score distribution

**Features include:** Rolling EPA, 3rd down %, red zone efficiency, turnover differential, injury flags, weather, rest days, head-to-head history, coaching tendencies

**Player Projections** — Position-specific XGBoost models (QB, RB, WR/TE, DEF) with matchup ratings (0–100 scale)

## Data Sources

| Source | Provides | Cost |
|--------|----------|------|
| ESPN Public API | Scores, rosters, schedules, injuries | FREE, no key |
| NFLverse (nfl-data-py) | PBP, EPA, snap counts, advanced stats | FREE, no key |
| Pro Football Reference | Historical splits, game logs | FREE (scraped, 3.5s delay) |
| OpenWeatherMap | Stadium weather forecasts | FREE (1k calls/day) |
| The Odds API | Vegas lines for calibration | FREE (500/month) |

## Pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard — featured game, all week's predictions, power rankings |
| `/teams` | All 32 teams by conference/division |
| `/teams/:id` | Team detail — 6 tabs: Overview, Offense, Defense, Advanced, Schedule, Roster |
| `/players` | Player directory with leaderboards and position filter |
| `/players/:id` | Player profile — 4 tabs: Stats, Trends, Splits, Projections |
| `/games` | Schedule/scoreboard with live scores |
| `/games/:id` | Game detail + box score |
| `/predict` | This week's game predictions hub |
| `/predict/game/:id` | Full prediction breakdown — Monte Carlo, key factors, player projections |
| `/predict/players` | Player projection leaderboard |
| `/predict/season` | Season win totals + playoff probabilities |
| `/analytics` | Standings, league trends, schedule difficulty |
| `/analytics/power-rankings` | Algorithm-based power rankings (Elo + EPA + SOS) |
| `/model` | Model performance dashboard + feature importance |

## Scheduled Jobs

| Job | Schedule | Purpose |
|-----|----------|---------|
| syncLiveScores | Every 5 min | Live game score updates |
| syncGames | Every 2 hrs | ESPN game sync |
| syncTeams | Every 6 hrs | Roster + injury updates |
| triggerModelRetrain | Tuesdays 6am | Weekly ML retraining |
| regeneratePredictions | Wednesdays 9am | Fresh predictions with new data |

## Running the Seed

```bash
# Load 3 seasons of historical data from NFLverse
python database/seeds/seed.py

# Then train the ML models
python analytics/updater.py
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a new stat category end-to-end.

---
*Data for educational/research purposes. Not affiliated with the NFL.*
