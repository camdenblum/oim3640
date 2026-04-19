"""Full game prediction breakdown with Monte Carlo histogram."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from utils.espn import get_scoreboard, get_all_teams, get_current_week, get_current_season
from utils.predictor import predict_game, get_all_elos

st.set_page_config(page_title="Predictions | NFL Predictor", page_icon="🎯", layout="wide")
st.title("🎯 Game Predictions")
st.caption("Select any matchup to see the full ML prediction breakdown.")

# ── Team selector ─────────────────────────────────────────────────────────────
all_teams = get_all_teams()
abbrs = sorted([t["abbr"] for t in all_teams]) if all_teams else [
    "ARI","ATL","BAL","BUF","CAR","CHI","CIN","CLE","DAL","DEN",
    "DET","GB","HOU","IND","JAX","KC","LV","LAC","LA","MIA",
    "MIN","NE","NO","NYG","NYJ","PHI","PIT","SF","SEA","TB","TEN","WAS",
]

st.subheader("Custom Matchup Predictor")
c1, c2 = st.columns(2)
with c1:
    away = st.selectbox("Away Team", abbrs, index=abbrs.index("KC") if "KC" in abbrs else 0)
with c2:
    home_options = [a for a in abbrs if a != away]
    home = st.selectbox("Home Team 🏠", home_options, index=home_options.index("SF") if "SF" in home_options else 0)

if st.button("Run Prediction", type="primary", use_container_width=True):
    st.session_state["pred_home"] = home
    st.session_state["pred_away"] = away

# Auto-predict if teams selected or button pressed
home_sel = st.session_state.get("pred_home", home)
away_sel = st.session_state.get("pred_away", away)

pred = predict_game(home_sel, away_sel)

st.divider()
st.subheader(f"{away_sel} @ {home_sel}")

# ── Win probability ────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    st.markdown(f"### {away_sel}")
    st.metric("Win Probability", f"{pred['away_win_prob']*100:.1f}%")
    st.metric("Projected Score", f"{pred['predicted_away_score']:.0f}")
    st.metric("Elo Rating", f"{pred['away_elo']:.0f}")

with col2:
    # Big probability bar
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[pred["away_win_prob"] * 100],
        y=[""],
        orientation="h",
        marker_color="#D50A0A",
        showlegend=False,
        text=f"{pred['away_win_prob']*100:.0f}%",
        textposition="inside",
    ))
    fig.add_trace(go.Bar(
        x=[pred["home_win_prob"] * 100],
        y=[""],
        orientation="h",
        base=[pred["away_win_prob"] * 100],
        marker_color="#013369",
        showlegend=False,
        text=f"{pred['home_win_prob']*100:.0f}%",
        textposition="inside",
    ))
    fig.update_layout(
        height=80,
        barmode="stack",
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False),
        yaxis=dict(showgrid=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        title=dict(text="Win Probability", font=dict(size=11), x=0.5),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        f"<div style='text-align:center;font-size:0.85rem;color:#8b949e'>"
        f"Spread: {abs(pred['predicted_spread']):.1f} {'(Home favored)' if pred['predicted_spread']>0 else '(Away favored)'}"
        f"</div>",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(f"### {home_sel} 🏠")
    st.metric("Win Probability", f"{pred['home_win_prob']*100:.1f}%")
    st.metric("Projected Score", f"{pred['predicted_home_score']:.0f}")
    st.metric("Elo Rating", f"{pred['home_elo']:.0f}")

st.divider()

# ── Key metrics row ────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
m1.metric("Predicted Total", f"{pred['predicted_total']:.1f}")
m2.metric("Spread", f"{abs(pred['predicted_spread']):.1f}")
m3.metric("Model Confidence", f"{pred['confidence']:.0f}%")
m4.metric("Elo Difference", f"{abs(pred['home_elo'] - pred['away_elo']):.0f} pts")

st.divider()

# ── Monte Carlo histogram ─────────────────────────────────────────────────────
st.subheader("Monte Carlo Score Distribution (10,000 simulations)")
st.caption("Distribution of combined total scores across simulated games.")

totals = np.array(pred["simulation_totals"])
fig_hist = px.histogram(
    x=totals,
    nbins=50,
    labels={"x": "Combined Total Points"},
    color_discrete_sequence=["#FFB612"],
)
fig_hist.add_vline(
    x=float(np.mean(totals)),
    line_dash="dash",
    line_color="white",
    annotation_text=f"Mean: {np.mean(totals):.1f}",
    annotation_position="top right",
)
fig_hist.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    showlegend=False,
    margin=dict(l=0, r=0, t=20, b=0),
    height=280,
    yaxis=dict(title="Simulations", gridcolor="#30363d"),
    xaxis=dict(gridcolor="#30363d"),
)
st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

# ── Key factors ────────────────────────────────────────────────────────────────
st.subheader("Key Factors")
for i, factor in enumerate(pred["factors"], 1):
    st.markdown(f"**{i}.** {factor}")

st.divider()

# ── This week's games quick-predict ──────────────────────────────────────────
st.subheader(f"Week {get_current_week()} Quick Predictions")
current_season = get_current_season()
games = get_scoreboard(week=get_current_week(), season=current_season)

if games:
    rows = []
    for g in games:
        p = predict_game(g["home_abbr"], g["away_abbr"])
        rows.append({
            "Matchup": f"{g['away_abbr']} @ {g['home_abbr']}",
            "Away Win%": f"{p['away_win_prob']*100:.0f}%",
            "Home Win%": f"{p['home_win_prob']*100:.0f}%",
            "Proj Score": f"{p['predicted_away_score']:.0f}–{p['predicted_home_score']:.0f}",
            "Spread": f"{abs(p['predicted_spread']):.1f} {'H' if p['predicted_spread']>0 else 'A'}",
            "O/U": f"{p['predicted_total']:.1f}",
            "Confidence": f"{p['confidence']:.0f}%",
        })
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No games this week — try the Custom Matchup Predictor above.")
