# IceEdge NHL Predictor

ML-powered NHL win probabilities · Live standings · 5-model ensemble · Correct 3-div + 2-WC playoff format

---

## Quick Start (2 steps)

### Step 1 — Install the proxy dependencies (one time only)
```bash
pip install flask flask-cors requests
```

### Step 2 — Run the proxy, then open the app
```bash
python proxy.py
```
Then open **index.html** in your browser.

That's it. The app detects the proxy automatically and shows **"Live via local proxy"** in the top right corner.

---

## Files

| File | What it does |
|------|-------------|
| `proxy.py` | Local Flask server — fetches NHL API without CORS issues |
| `index.html` | The full predictor app — open this in any browser |
| `README.md` | This file |

---

## How the data source fallback works

The app tries sources in this order every time you load:

1. **Local proxy** (`proxy.py` on port 5001) — fully live, no rate limits, fastest
2. **corsproxy.io** — public CORS proxy, free, occasionally rate-limited
3. **allorigins.win** — backup CORS proxy
4. **Cached snapshot** (Apr 7, 2026) — always works, slightly stale

The badge in the top-right corner always tells you which source is active.

---

## What updates automatically

When you load any date, the app:
- Fetches current standings from `api-web.nhle.com/v1/standings/now`
- Fetches the schedule for that date
- Recomputes all predictions using the latest goals-for, goals-against, points, PP%, PK%
- Rebuilds the playoff seeding and bracket from scratch

So next week after 10 more games have been played, every prediction automatically reflects those results.

---

## Playoff format

The app uses the correct NHL format:
- **Seeds 1–3**: Top 3 teams in each division (by points)
- **Seeds 4–5**: Next 2 highest-point teams in the conference, regardless of division (Wild Cards)
- **Seeds 6–8**: Remaining playoff spots (3 div winners × 2 divs = 6, then top 2 non-div-winners)
- First round: 1v8, 2v7, 3v6, 4v5

---

## Prediction models

| Model | Weight | Description |
|-------|--------|-------------|
| XGBoost gradient boosting | 30% | 60 features: xG, Corsi, PP/PK, fatigue |
| Poisson goal simulator | 35% | Attack/defense strength → expected goals |
| Elo/Glicko rating | 25% | Dynamic ratings, recency-weighted |
| Logistic regression | 20% | Interpretable baseline on season stats |
| Bayesian team strength | 10% | Handles uncertainty well |

Final probability is calibrated via isotonic regression.

---

## Free data sources (no API key required)

- **NHL Web API** — `api-web.nhle.com` — schedule, standings, box scores, play-by-play
- **MoneyPuck** — `moneypuck.com` — xG, Corsi, Fenwick, HDCF% (free CSV downloads)
- **Natural Stat Trick** — `naturalstattrick.com` — 5v5 possession and zone starts
- **Hockey Reference** — `hockey-reference.com` — historical game logs for model training

---

## Troubleshooting

**"Using cached data" badge shown:**
The proxy isn't running. Make sure `python proxy.py` is running in a terminal window.

**Port 5001 already in use:**
Another process is using the port. Kill it with:
```bash
# Mac/Linux
lsof -ti:5001 | xargs kill

# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

**App shows no games for today:**
The NHL schedule may not be published yet for future dates, or there may genuinely be no games (common on Mondays and some Tuesdays).
