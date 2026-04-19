"""Elo-based power rankings for all 32 NFL teams."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.espn import get_all_teams, get_standings
from utils.predictor import get_all_elos

st.set_page_config(page_title="Power Rankings | NFL Predictor", page_icon="📊", layout="wide")
st.title("📊 Power Rankings")
st.caption("Teams ranked by Elo rating — updated as game results are processed.")

# Load data
elos = get_all_elos()
standings = get_standings()
all_teams = get_all_teams()

team_info = {t["abbr"]: t for t in all_teams} if all_teams else {}
standings_map = {t["abbr"]: t for t in standings} if standings else {}

# Build rankings table
rows = []
for abbr, elo in sorted(elos.items(), key=lambda x: -x[1]):
    info = team_info.get(abbr, {})
    s = standings_map.get(abbr, {})
    rows.append({
        "abbr": abbr,
        "name": info.get("name", abbr),
        "elo": elo,
        "delta": elo - 1500,
        "wins": s.get("wins", 0),
        "losses": s.get("losses", 0),
        "ties": s.get("ties", 0),
        "pf": s.get("pf", 0),
        "pa": s.get("pa", 0),
        "conference": s.get("conference", ""),
        "color": info.get("color", "#444"),
    })

df = pd.DataFrame(rows).reset_index(drop=True)
df.index = df.index + 1  # Rank starts at 1

# ── Tier indicators ────────────────────────────────────────────────────────────
def tier(rank: int) -> str:
    if rank <= 4:   return "🔥 Elite"
    if rank <= 12:  return "✅ Contender"
    if rank <= 22:  return "⚠️ Average"
    return "🔻 Rebuilding"

df["tier"] = [tier(i) for i in range(1, len(df) + 1)]
df["record"] = df.apply(lambda r: f"{r['wins']}–{r['losses']}" + (f"–{r['ties']}" if r["ties"] else ""), axis=1)
df["elo_disp"] = df["elo"].round(0).astype(int)
df["delta_disp"] = df["delta"].apply(lambda d: f"+{d:.0f}" if d >= 0 else f"{d:.0f}")

# ── Rankings table ─────────────────────────────────────────────────────────────
st.subheader("All 32 Teams — Ranked")

conf_filter = st.selectbox("Filter by Conference", ["All", "AFC", "NFC"])
filtered = df if conf_filter == "All" else df[df["conference"] == conf_filter]

display = filtered[["abbr", "name", "record", "elo_disp", "delta_disp", "tier"]].copy()
display.columns = ["Team", "Full Name", "Record", "Elo", "vs Average", "Tier"]

st.dataframe(
    display,
    use_container_width=True,
    column_config={
        "Elo": st.column_config.ProgressColumn(
            "Elo Rating",
            min_value=1350,
            max_value=1700,
            format="%d",
        ),
    },
)

st.divider()

# ── Horizontal bar chart ───────────────────────────────────────────────────────
st.subheader("Elo Ratings — Visual Ranking")

top_n = st.slider("Show top N teams", 8, 32, 16)
chart_df = filtered.head(top_n)

colors = []
for _, row in chart_df.iterrows():
    if row["delta"] > 60:
        colors.append("#2ea043")
    elif row["delta"] > 0:
        colors.append("#388bfd")
    elif row["delta"] > -60:
        colors.append("#d29922")
    else:
        colors.append("#f85149")

fig = go.Figure(go.Bar(
    y=chart_df["abbr"].tolist()[::-1],
    x=chart_df["elo"].tolist()[::-1],
    orientation="h",
    marker_color=colors[::-1],
    text=[f"{v:.0f}" for v in chart_df["elo"].tolist()[::-1]],
    textposition="outside",
))
fig.add_vline(x=1500, line_dash="dash", line_color="#8b949e",
              annotation_text="Average (1500)", annotation_position="top left")
fig.update_layout(
    height=max(300, top_n * 28),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
    xaxis=dict(range=[1350, 1720], gridcolor="#30363d"),
    yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    margin=dict(l=10, r=60, t=20, b=20),
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ── Conference comparison scatter ──────────────────────────────────────────────
st.subheader("Elo vs Win Total")
if standings:
    scatter_df = df[df["wins"] + df["losses"] > 0].copy()
    fig2 = px.scatter(
        scatter_df,
        x="wins",
        y="elo",
        color="conference",
        text="abbr",
        size_max=12,
        labels={"wins": "Wins", "elo": "Elo Rating", "conference": "Conference"},
        color_discrete_map={"AFC": "#D50A0A", "NFC": "#013369"},
        title="Elo Rating vs Wins — 2024 Season",
    )
    fig2.update_traces(textposition="top center", marker=dict(size=10))
    fig2.add_hline(y=1500, line_dash="dot", line_color="#8b949e")
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400,
        xaxis=dict(gridcolor="#30363d"),
        yaxis=dict(gridcolor="#30363d"),
    )
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

st.divider()
st.markdown("""
**About the Elo system:**
- All teams start at a calibrated baseline (range 1410–1620)
- Each game result shifts both teams by K=20 × margin-of-victory multiplier
- Home field = +65 Elo points for win probability calculation
- Load historical data on the **Model** page to update ratings from real game results
""")
