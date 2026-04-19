"""
NFL Predictor — Streamlit Dashboard
Run with: streamlit run app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.graph_objects as go
from utils.espn import get_scoreboard, get_standings, get_current_week, get_current_season
from utils.predictor import predict_game, get_all_elos

st.set_page_config(
    page_title="NFL Predictor",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Minimal styling ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    section[data-testid="stSidebar"] { background: #0d1117; }
    .game-box { background: #161b22; border-radius: 12px; padding: 1rem;
                border: 1px solid #30363d; margin-bottom: 0.75rem; }
    .team-name { font-size: 1.1rem; font-weight: 700; }
    .prob-label { font-size: 0.75rem; color: #8b949e; }
    .metric-val { font-size: 1.4rem; font-weight: 800; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("🏈 NFL Predictor")
st.caption("ML-powered game predictions using Elo ratings + Monte Carlo simulation")

# ── Week / Season selector ───────────────────────────────────────────────────
current_week = get_current_week()
current_season = get_current_season()

c1, c2, _ = st.columns([1, 1, 4])
with c1:
    season = st.selectbox("Season", [2025, 2024, 2023, 2022], index=0 if current_season == 2025 else 1)
with c2:
    week = st.slider("Week", 1, 18, current_week)

st.divider()

# ── Fetch games ───────────────────────────────────────────────────────────────
with st.spinner("Fetching games from ESPN…"):
    games = get_scoreboard(week=week, season=season)

if not games:
    st.info(
        "No games found for this week. "
        "The NFL season runs September–February. "
        "Try a different week or season above."
    )
    st.stop()

st.subheader(f"Week {week} — {len(games)} Games")

# ── Game cards ────────────────────────────────────────────────────────────────
cols_per_row = 2
for row_start in range(0, len(games), cols_per_row):
    row_games = games[row_start : row_start + cols_per_row]
    cols = st.columns(cols_per_row)
    for col, game in zip(cols, row_games):
        pred = predict_game(game["home_abbr"], game["away_abbr"])
        with col:
            with st.container(border=True):
                # Status badge
                if game["completed"]:
                    st.caption(f"✅ Final  •  {game['venue']}")
                else:
                    st.caption(f"🕐 {game['status_detail'] or 'Scheduled'}  •  {game['venue']}")

                # Team row
                t1, score_col, t2 = st.columns([3, 2, 3])
                with t1:
                    if game["away_logo"]:
                        st.image(game["away_logo"], width=48)
                    st.markdown(f"**{game['away_abbr']}**")
                    st.caption(game["away_record"])

                with score_col:
                    if game["completed"]:
                        st.markdown(
                            f"<div style='text-align:center;font-size:1.5rem;font-weight:800;padding-top:8px'>"
                            f"{game['away_score']} – {game['home_score']}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            "<div style='text-align:center;font-size:0.8rem;color:#8b949e;padding-top:18px'>vs</div>",
                            unsafe_allow_html=True,
                        )

                with t2:
                    if game["home_logo"]:
                        st.image(game["home_logo"], width=48)
                    st.markdown(f"**{game['home_abbr']}** 🏠")
                    st.caption(game["home_record"])

                st.divider()

                # Win probability bar
                home_p = pred["home_win_prob"]
                away_p = pred["away_win_prob"]

                fig = go.Figure(go.Bar(
                    x=[away_p * 100, home_p * 100],
                    y=[game["away_abbr"], game["home_abbr"]],
                    orientation="h",
                    marker_color=[game["away_color"], game["home_color"]],
                    text=[f"{away_p*100:.0f}%", f"{home_p*100:.0f}%"],
                    textposition="inside",
                    insidetextanchor="middle",
                ))
                fig.update_layout(
                    height=100,
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False),
                    yaxis=dict(showgrid=False),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white"),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                # Predicted score & spread
                m1, m2, m3 = st.columns(3)
                m1.metric("Proj Score", f"{pred['predicted_away_score']:.0f}–{pred['predicted_home_score']:.0f}")
                m2.metric("Spread", f"{abs(pred['predicted_spread']):.1f} {'H' if pred['predicted_spread'] > 0 else 'A'}")
                m3.metric("O/U", f"{pred['predicted_total']:.1f}")

                if game["broadcast"]:
                    st.caption(f"📺 {game['broadcast']}")

# ── Standings snapshot ────────────────────────────────────────────────────────
st.divider()
st.subheader("Current Standings")

with st.spinner("Loading standings…"):
    standings = get_standings()

if standings:
    for conf in ["AFC", "NFC"]:
        st.markdown(f"#### {conf}")
        conf_teams = [t for t in standings if t["conference"] == conf]
        conf_teams.sort(key=lambda x: (-x["wins"], x["losses"]))

        header_cols = st.columns([3, 1, 1, 1, 1, 1, 1])
        for h, label in zip(header_cols, ["Team", "W", "L", "T", "PCT", "PF", "PA"]):
            h.markdown(f"<small style='color:#8b949e'>{label}</small>", unsafe_allow_html=True)

        for t in conf_teams:
            row = st.columns([3, 1, 1, 1, 1, 1, 1])
            row[0].markdown(f"**{t['abbr']}** <small style='color:#8b949e'>{t['division'].replace(conf+' ','')}</small>", unsafe_allow_html=True)
            row[1].markdown(str(t["wins"]))
            row[2].markdown(str(t["losses"]))
            row[3].markdown(str(t["ties"]))
            row[4].markdown(f"{t['pct']:.3f}")
            row[5].markdown(str(t["pf"]))
            row[6].markdown(str(t["pa"]))

        st.markdown("---")

# ── Sidebar links ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏈 NFL Predictor")
    st.markdown("Navigate using the **Pages** menu above.")
    st.markdown("---")
    st.markdown("**Data sources**")
    st.markdown("- ESPN Public API (live)")
    st.markdown("- nfl-data-py (historical)")
    st.markdown("- Elo + Monte Carlo model")
    st.markdown("---")
    st.caption("For educational use only. Not affiliated with the NFL.")
