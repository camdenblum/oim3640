"""Player stat leaders powered by nfl-data-py."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Players | NFL Predictor", page_icon="👤", layout="wide")
st.title("👤 Player Stats & Leaders")
st.caption("Season statistics from nfl-data-py (free, no API key required).")

season = st.selectbox("Season", [2024, 2023, 2022], index=0)

@st.cache_data(ttl=3600, show_spinner="Loading player stats…")
def load_leaders(s: int):
    try:
        from utils.nfl_data import get_season_leaders
        return get_season_leaders(s)
    except Exception as e:
        return {"error": str(e)}

with st.spinner("Loading stats…"):
    leaders = load_leaders(season)

if not leaders or "error" in leaders:
    err = leaders.get("error", "Unknown error") if leaders else "Unknown"
    st.warning(
        f"Could not load player stats: {err}\n\n"
        "Make sure `nfl-data-py` is installed: `pip install nfl-data-py`"
    )
    st.info(
        "Player stats require an internet connection to download from the NFLverse data repository. "
        "The first load may take 30–60 seconds."
    )
    st.stop()

# ── Passing Leaders ────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏈 Passing", "🏃 Rushing", "📡 Receiving"])

with tab1:
    df = leaders.get("Passing", pd.DataFrame())
    if not df.empty:
        df = df.rename(columns={
            "player_name": "Player", "recent_team": "Team",
            "pass_yards": "Yards", "pass_tds": "TDs",
            "interceptions": "INTs", "completions": "Comp",
            "attempts": "Att", "games": "GP",
        })
        df["Y/G"] = (df["Yards"] / df["GP"]).round(1)
        df["Comp%"] = (df["Comp"] / df["Att"] * 100).round(1)
        cols = ["Player", "Team", "Yards", "Y/G", "TDs", "INTs", "Comp%", "Att", "GP"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)

        import plotly.express as px
        fig = px.bar(
            df.head(10), x="Player", y="Yards", color="Team",
            title="Top 10 — Passing Yards",
            labels={"Yards": "Pass Yards"},
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="white"), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No passing data available.")

with tab2:
    df = leaders.get("Rushing", pd.DataFrame())
    if not df.empty:
        df = df.rename(columns={
            "player_name": "Player", "recent_team": "Team", "position": "Pos",
            "rush_yards": "Yards", "rush_tds": "TDs",
            "carries": "Car", "games": "GP",
        })
        df["Y/G"] = (df["Yards"] / df["GP"]).round(1)
        df["YPC"] = (df["Yards"] / df["Car"].replace(0, 1)).round(1)
        cols = ["Player", "Team", "Pos", "Yards", "Y/G", "YPC", "TDs", "Car", "GP"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)

        import plotly.express as px
        fig = px.bar(
            df.head(10), x="Player", y="Yards", color="Team",
            title="Top 10 — Rushing Yards",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="white"), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No rushing data available.")

with tab3:
    df = leaders.get("Receiving", pd.DataFrame())
    if not df.empty:
        df = df.rename(columns={
            "player_name": "Player", "recent_team": "Team", "position": "Pos",
            "rec_yards": "Yards", "receptions": "Rec",
            "rec_tds": "TDs", "targets": "Tgt", "games": "GP",
        })
        df["Y/G"] = (df["Yards"] / df["GP"]).round(1)
        df["Catch%"] = (df["Rec"] / df["Tgt"].replace(0, 1) * 100).round(1)
        cols = ["Player", "Team", "Pos", "Yards", "Y/G", "Rec", "Tgt", "Catch%", "TDs", "GP"]
        st.dataframe(df[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)

        import plotly.express as px
        fig = px.bar(
            df.head(10), x="Player", y="Yards", color="Team",
            title="Top 10 — Receiving Yards",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="white"), height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No receiving data available.")
