"""NFL Standings and team detail view."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
from utils.espn import get_standings, get_all_teams, get_team_roster
from utils.predictor import get_all_elos

st.set_page_config(page_title="Teams | NFL Predictor", page_icon="🏟️", layout="wide")
st.title("🏟️ Teams & Standings")

tab1, tab2 = st.tabs(["📊 Standings", "🔍 Team Detail"])

# ── Standings Tab ──────────────────────────────────────────────────────────────
with tab1:
    with st.spinner("Loading standings…"):
        standings = get_standings()

    if not standings:
        st.warning("Could not load standings. ESPN API may be unavailable.")
        st.stop()

    elos = get_all_elos()

    for conf in ["AFC", "NFC"]:
        st.markdown(f"## {conf}")
        conf_teams = [t for t in standings if t["conference"] == conf]

        divisions = sorted(set(t["division"] for t in conf_teams))
        div_cols = st.columns(len(divisions))

        for col, div in zip(div_cols, divisions):
            div_teams = [t for t in conf_teams if t["division"] == div]
            div_teams.sort(key=lambda x: (-x["wins"], x["losses"]))

            with col:
                st.markdown(f"**{div}**")
                for i, t in enumerate(div_teams):
                    win_pct = f"{t['pct']:.3f}"
                    elo = elos.get(t["abbr"], 1500)
                    rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else ""
                    playoff_color = "#2ea043" if i == 0 else "#388bfd" if i == 1 else ""
                    border = f"border-left: 3px solid {playoff_color}; padding-left: 6px;" if playoff_color else "padding-left: 9px;"

                    st.markdown(
                        f"<div style='{border} margin-bottom:6px'>"
                        f"<b>{rank_icon}{t['abbr']}</b> "
                        f"<span style='color:#8b949e;font-size:0.85rem'>{t['wins']}–{t['losses']}"
                        f"{'–'+str(t['ties']) if t['ties'] else ''} | {win_pct}</span><br>"
                        f"<span style='color:#8b949e;font-size:0.75rem'>PF {t['pf']} · PA {t['pa']} · Elo {elo:.0f}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        st.divider()

    # Full standings table
    st.markdown("### Full Standings Table")
    import pandas as pd
    df = pd.DataFrame(standings)
    df["elo"] = df["abbr"].map(lambda a: round(elos.get(a, 1500), 0))
    df["record"] = df.apply(lambda r: f"{r['wins']}–{r['losses']}" + (f"–{r['ties']}" if r["ties"] else ""), axis=1)
    display_cols = ["abbr", "conference", "division", "record", "pct", "pf", "pa", "diff", "streak", "elo"]
    rename = {"abbr": "Team", "conference": "Conf", "division": "Division", "record": "Record",
               "pct": "PCT", "pf": "PF", "pa": "PA", "diff": "Diff", "streak": "Streak", "elo": "Elo"}
    st.dataframe(
        df[display_cols].rename(columns=rename).sort_values(["Conf", "Division", "PCT"], ascending=[True, True, False]),
        use_container_width=True,
        hide_index=True,
    )

# ── Team Detail Tab ────────────────────────────────────────────────────────────
with tab2:
    all_teams = get_all_teams()
    elos = get_all_elos()

    if not all_teams:
        st.info("Loading team data…")
        st.stop()

    team_map = {t["abbr"]: t for t in all_teams}
    selected_abbr = st.selectbox("Select Team", sorted(team_map.keys()))
    team = team_map.get(selected_abbr, {})

    if team:
        c1, c2 = st.columns([1, 4])
        with c1:
            if team.get("logo"):
                st.image(team["logo"], width=100)
        with c2:
            st.markdown(f"## {team['name']}")
            elo = elos.get(selected_abbr, 1500)
            delta = elo - 1500
            st.markdown(
                f"**Elo Rating:** {elo:.0f} "
                f"({'▲' if delta >= 0 else '▼'}{abs(delta):.0f} vs average)"
            )

        st.divider()

        # Roster
        with st.spinner("Loading roster…"):
            roster = get_team_roster(team.get("id", ""))

        if roster:
            import pandas as pd
            df_r = pd.DataFrame(roster)
            st.markdown(f"### Roster ({len(roster)} players)")

            positions = ["All"] + sorted(df_r["position"].dropna().unique().tolist())
            pos_filter = st.selectbox("Filter by position", positions)
            if pos_filter != "All":
                df_r = df_r[df_r["position"] == pos_filter]

            status_colors = {
                "Active": "🟢", "Questionable": "🟡", "Doubtful": "🟠",
                "Out": "🔴", "IR": "⚫", "PUP": "⚫",
            }
            df_r["Status"] = df_r["status"].map(lambda s: f"{status_colors.get(s, '⚪')} {s}")
            df_r = df_r.rename(columns={"name": "Name", "position": "Pos", "jersey": "#", "age": "Age"})
            st.dataframe(
                df_r[["Name", "Pos", "#", "Age", "Status"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Roster data not available for this team.")

        # Elo gauge
        st.divider()
        st.markdown("### Elo Rating Gauge")
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=elo,
            delta={"reference": 1500, "valueformat": ".0f"},
            gauge={
                "axis": {"range": [1350, 1700], "tickwidth": 1},
                "bar": {"color": team.get("color", "#013369")},
                "steps": [
                    {"range": [1350, 1450], "color": "#3d1a1a"},
                    {"range": [1450, 1550], "color": "#2d2d2d"},
                    {"range": [1550, 1700], "color": "#1a3d1a"},
                ],
                "threshold": {"line": {"color": "white", "width": 3}, "thickness": 0.75, "value": 1500},
            },
            title={"text": f"{selected_abbr} Elo Rating"},
            number={"valueformat": ".0f"},
        ))
        fig.update_layout(
            height=280,
            paper_bgcolor="rgba(0,0,0,0)",
            font={"color": "white"},
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
