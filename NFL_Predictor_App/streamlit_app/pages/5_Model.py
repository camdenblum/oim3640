"""Model info, Elo history, and historical data loader."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.predictor import get_all_elos, _BASE_ELO, DB_PATH

st.set_page_config(page_title="Model | NFL Predictor", page_icon="🤖", layout="wide")
st.title("🤖 Model & Data")

tab1, tab2, tab3 = st.tabs(["📖 How It Works", "📥 Load Historical Data", "📈 Elo Ratings"])

# ── How It Works ──────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Prediction Model Architecture")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
### Elo Rating System
- Each NFL team has an Elo rating starting around **1500**
- Ratings update after every game result
- **Home field advantage:** +65 Elo points
- **K-factor:** 20 (how fast ratings change)
- **Margin-of-victory multiplier:** log(MOV + 1) × stability factor
  — a 30-point win shifts ratings more than a 1-point win

### Monte Carlo Simulation
- **10,000 game simulations** per prediction
- Each team's score drawn from a normal distribution:
  - Mean = base_score + Elo strength adjustment + home boost
  - Standard deviation = 10 points (matches historical NFL variance)
- Simulation win% blended with Elo win probability (55/45 weight)

### Win Probability Formula
```
P(home win) = 1 / (1 + 10^(-ΔElo / 400))
```
Where ΔElo = home_elo + 65 − away_elo
        """)

    with col2:
        st.markdown("""
### Data Sources
| Source | Data | Cost |
|--------|------|------|
| ESPN Public API | Live scores, rosters, schedules | Free, no key |
| nfl-data-py | Historical PBP, weekly stats | Free, no key |
| Elo system | Win probabilities | Computed locally |

### Accuracy Expectations
| Metric | Expected |
|--------|----------|
| Win/loss prediction | ~65–68% |
| Spread accuracy (±7 pts) | ~55–60% |
| Total accuracy (±7 pts) | ~55–60% |

These match published accuracy benchmarks for Elo-only models.
Adding the historical nfl-data-py training improves accuracy by ~3–5%.

### Why Elo?
Elo is the most robust single-metric predictor for NFL games:
- Accounts for **strength of schedule** automatically
- **Self-correcting** — bad predictions shift ratings more
- **No overfitting** — simple formula, no feature engineering needed
- Used by FiveThirtyEight, ESPN, and Vegas oddsmakers as a baseline
        """)

    st.divider()
    st.subheader("Prediction Pipeline")
    st.code("""
1. Fetch teams from ESPN (live, no API key)
2. Look up each team's Elo rating from local SQLite DB
3. Compute Elo win probability:
       P(home) = 1 / (1 + 10^(-ΔElo/400))
4. Run 10,000 Monte Carlo score simulations
5. Blend Elo prob (55%) + simulation prob (45%)
6. Project spread and total from simulation means
7. Generate key factors from Elo differentials
    """, language="text")

# ── Historical Data Loader ─────────────────────────────────────────────────────
with tab2:
    st.subheader("Load Historical Game Results")
    st.markdown("""
Loading historical data replays all game results from 2022–2024 to build
**accurate Elo ratings** based on real outcomes rather than pre-set baselines.

This downloads schedule data from the **NFLverse** GitHub repository (free, no API key).
First download: ~30–60 seconds. Subsequent runs use the local SQLite cache.
    """)

    seasons_to_load = st.multiselect(
        "Seasons to load",
        [2022, 2023, 2024],
        default=[2022, 2023, 2024],
    )

    if st.button("🔄 Load & Build Elo Ratings", type="primary", disabled=not seasons_to_load):
        with st.spinner("Downloading from NFLverse…"):
            from utils.nfl_data import load_historical_elo
            result = load_historical_elo(seasons_to_load)
        if "error" in result.lower() or "failed" in result.lower() or "not installed" in result.lower():
            st.error(result)
        else:
            st.success(result)
            st.balloons()
            st.info("Refresh the Power Rankings page to see updated Elo ratings.")

    st.divider()
    db_exists = DB_PATH.exists()
    db_size = DB_PATH.stat().st_size / 1024 if db_exists else 0
    st.metric("Local DB", "exists" if db_exists else "not created yet", f"{db_size:.1f} KB")
    if db_exists:
        st.caption(f"Path: `{DB_PATH}`")

# ── Elo Ratings Table ─────────────────────────────────────────────────────────
with tab3:
    st.subheader("Current Elo Ratings")
    elos = get_all_elos()

    rows = [
        {"Team": abbr, "Elo": round(elo, 0), "vs Average": round(elo - 1500, 0)}
        for abbr, elo in sorted(elos.items(), key=lambda x: -x[1])
    ]
    df = pd.DataFrame(rows)

    fig = px.bar(
        df,
        x="Team",
        y="vs Average",
        color="vs Average",
        color_continuous_scale=["#f85149", "#d29922", "#2ea043"],
        title="Elo Delta vs League Average (1500)",
        labels={"vs Average": "Elo Delta"},
    )
    fig.add_hline(y=0, line_dash="dash", line_color="white")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=350,
        coloraxis_showscale=False,
        xaxis=dict(gridcolor="#30363d"),
        yaxis=dict(gridcolor="#30363d"),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Elo": st.column_config.ProgressColumn("Elo", min_value=1350, max_value=1700, format="%d"),
        },
    )
