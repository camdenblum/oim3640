"""
2026 NFL Season Hub
- Super Bowl win odds  (live The Odds API + Elo Monte Carlo)
- Player season projections based on CURRENT rosters (ESPN, April 2026)
  with live injury status and free-agency team changes baked in
- Per-game player props for any head-to-head matchup
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from utils.odds import get_super_bowl_futures, elo_championship_probabilities, AFC_TEAMS, NFC_TEAMS
from utils.espn import get_all_teams
from utils.predictor import get_all_elos, predict_game
from utils.roster import merge_projections_with_roster, injury_badge, _std_abbr

st.set_page_config(
    page_title="2026 Season | NFL Predictor",
    page_icon="🏆",
    layout="wide",
)

st.title("🏆 2026 NFL Season")
st.caption(
    "Super Bowl futures · Season projections with **current rosters (April 18, 2026)** "
    "· Live injury status · Free-agency team changes · Per-game player props"
)

# ── Load merged projection + roster data (shared across tabs) ─────────────────
@st.cache_data(ttl=1800, show_spinner="Loading 2024 stats + current rosters + injuries…")
def load_merged() -> pd.DataFrame:
    from utils.nfl_data import get_2026_projections
    proj = get_2026_projections()
    if proj.empty:
        return pd.DataFrame()
    return merge_projections_with_roster(proj)

with st.spinner("Building 2026 projections from current rosters…"):
    merged_df = load_merged()

# Summary metrics strip
if not merged_df.empty:
    on_roster   = merged_df[merged_df["on_roster"]]
    moved       = merged_df[merged_df["team_changed"]]
    injured_cnt = merged_df[merged_df["inj_status"].isin(
        ["Questionable","Doubtful","Out","IR","PUP","Suspended"])
    ]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Players on current rosters", len(on_roster))
    c2.metric("Free-agency/trade moves detected", len(moved))
    c3.metric("Injured / limited players", len(injured_cnt))
    c4.metric("Data freshness", "ESPN live — April 18, 2026")

st.divider()

tab1, tab2, tab3 = st.tabs([
    "🏆 Super Bowl Odds",
    "📊 Player Season Projections",
    "🎯 Matchup Player Props",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — SUPER BOWL ODDS
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("2026 Super Bowl Winner Odds")

    col_a, col_b = st.columns([3, 1])
    with col_b:
        use_sim = st.toggle("Use Elo simulation instead of live odds", value=False)

    with st.spinner("Fetching odds…"):
        futures = elo_championship_probabilities(25_000) if use_sim else get_super_bowl_futures()
        source_label = futures[0]["source"] if futures else "unavailable"

    st.caption(f"📡 Source: **{source_label}**")

    if not futures:
        st.error("Could not load odds data.")
    else:
        top = futures[:16]
        all_teams_info = {t["abbr"]: t for t in (get_all_teams() or [])}
        colors = [all_teams_info.get(r["abbr"], {}).get("color", "#444") for r in top]

        fig = go.Figure(go.Bar(
            y=[r["abbr"] for r in top][::-1],
            x=[r["implied_prob"] * 100 for r in top][::-1],
            orientation="h",
            marker_color=colors[::-1],
            text=[f"{r['implied_prob']*100:.1f}%  ({r['odds_american']})" for r in top][::-1],
            textposition="outside",
        ))
        fig.update_layout(
            title="Top 16 Super Bowl Contenders — Win Probability",
            height=480,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=12),
            xaxis=dict(title="Win Probability %", gridcolor="#30363d",
                       range=[0, max(r["implied_prob"] for r in top) * 135]),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            margin=dict(l=10, r=130, t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        afc_set = set(AFC_TEAMS)
        conf_filter = st.radio("Filter", ["All", "AFC", "NFC"], horizontal=True, key="sb_conf")

        rows = []
        for i, r in enumerate(futures, 1):
            conf = "AFC" if r["abbr"] in afc_set else "NFC"
            if conf_filter != "All" and conf != conf_filter:
                continue
            rows.append({
                "Rank": i, "Team": r["abbr"], "Full Name": r["team_name"],
                "Conf": conf, "Odds": r["odds_american"],
                "Win Prob": f"{r['implied_prob']*100:.2f}%",
                "SB App%": f"{r.get('sb_appearances_pct', r['implied_prob']*1.8)*100:.1f}%" if r.get("sb_appearances_pct") else "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Treemap
        tree_rows = [
            {"team": r["abbr"],
             "conference": "AFC" if r["abbr"] in afc_set else "NFC",
             "prob": round(r["implied_prob"] * 100, 2)}
            for r in futures if r["implied_prob"] > 0.001
        ]
        fig2 = px.treemap(
            pd.DataFrame(tree_rows), path=["conference","team"], values="prob",
            color="prob", color_continuous_scale=["#1a3d1a","#2ea043","#FFB612"],
            title="Super Bowl Win Probability by Conference & Team",
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
                           height=380, margin=dict(l=0,r=0,t=40,b=0),
                           coloraxis_showscale=False)
        fig2.update_traces(textinfo="label+value")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — PLAYER SEASON PROJECTIONS  (current rosters + injuries)
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("2026 Season Player Projections")
    st.caption(
        "Based on 2024 per-game averages × 17 games × 0.95 regression. "
        "**Current team** reflects April 2026 ESPN rosters (free agency, trades). "
        "**Projections are injury-adjusted** using live ESPN injury reports."
    )

    if merged_df.empty:
        st.warning("Could not load projections. Ensure nfl-data-py is installed.")
        st.stop()

    # ── Injury legend ──────────────────────────────────────────────────────────
    with st.expander("Injury adjustment factors used"):
        st.markdown("""
| Status | Projection multiplier | Meaning |
|--------|----------------------|---------|
| 🟢 Active | 100% | Full projection |
| 🟡 Questionable | 88% | May miss 1–2 games |
| 🟠 Doubtful | 45% | Likely misses several games |
| 🔴 Out | 25% | Short-term, may return mid-season |
| ⚫ IR | 12% | Could return on IR-DtR |
| ⚫ PUP | 60% | Misses first 4 games minimum |
        """)

    # ── Filters ───────────────────────────────────────────────────────────────
    f1, f2, f3, f4 = st.columns([1, 1, 1, 2])
    with f1:
        pos_filter = st.selectbox("Position", ["All","QB","RB","WR","TE"], key="p2_pos")
    with f2:
        team_list = ["All"] + sorted(merged_df["current_team"].dropna().unique().tolist())
        team_filter = st.selectbox("Current Team", team_list, key="p2_team")
    with f3:
        inj_options = ["All","Active only","Questionable","Doubtful","Out","IR"]
        inj_filter = st.selectbox("Injury Status", inj_options, key="p2_inj")
    with f4:
        search = st.text_input("Search player", placeholder="e.g. Mahomes, Jefferson…", key="p2_search")

    show_moved = st.checkbox("Show only players who changed teams (free agency / trades)", key="p2_moved")

    filtered = merged_df.copy()
    if pos_filter != "All":
        filtered = filtered[filtered["position"] == pos_filter]
    if team_filter != "All":
        filtered = filtered[filtered["current_team"] == team_filter]
    if inj_filter == "Active only":
        filtered = filtered[filtered["inj_status"].isin(["Active","Healthy"])]
    elif inj_filter not in ("All",):
        filtered = filtered[filtered["inj_status"] == inj_filter]
    if search:
        filtered = filtered[filtered["player_name"].str.contains(search, case=False, na=False)]
    if show_moved:
        filtered = filtered[filtered["team_changed"]]

    st.markdown(f"**{len(filtered)} players** | Use filters to narrow down")

    # ── Position tables ────────────────────────────────────────────────────────
    positions_to_show = [pos_filter] if pos_filter != "All" else ["QB","RB","WR","TE"]

    for pos in positions_to_show:
        pos_data = filtered[filtered["position"] == pos].copy()
        if pos_data.empty:
            continue

        icons = {"QB":"🏈","RB":"🏃","WR":"📡","TE":"🎯"}
        label = {"QB":"Quarterbacks","RB":"Running Backs","WR":"Wide Receivers","TE":"Tight Ends"}[pos]
        n = len(pos_data)

        with st.expander(f"{icons[pos]} {label} — {n} players", expanded=(n <= 30)):
            # Build display table with injury + team-change columns
            disp = pos_data.copy()
            disp["Status"]      = disp["inj_status"].apply(injury_badge)
            disp["Team"]        = disp.apply(
                lambda r: f"**{r['current_team']}** ↗ _(was {r['recent_team']})_"
                          if r["team_changed"] else r["current_team"],
                axis=1,
            )

            if pos == "QB":
                cols_show = {
                    "player_name":      "Player",
                    "Team":             "Team (Current)",
                    "Status":           "Injury",
                    "pass_yards_proj":  "Pass Yds",
                    "pass_tds_proj":    "Pass TDs",
                    "interceptions_proj":"INTs",
                    "comp_pct":         "Comp%",
                    "rush_yards_proj":  "Rush Yds",
                    "fantasy_ppr_proj": "Fant PPR",
                }
            elif pos == "RB":
                cols_show = {
                    "player_name":      "Player",
                    "Team":             "Team (Current)",
                    "Status":           "Injury",
                    "rush_yards_proj":  "Rush Yds",
                    "rush_tds_proj":    "Rush TDs",
                    "ypc":              "YPC",
                    "rec_yards_proj":   "Rec Yds",
                    "receptions_proj":  "Rec",
                    "fantasy_ppr_proj": "Fant PPR",
                }
            else:
                cols_show = {
                    "player_name":      "Player",
                    "Team":             "Team (Current)",
                    "Status":           "Injury",
                    "rec_yards_proj":   "Rec Yds",
                    "receptions_proj":  "Rec",
                    "rec_tds_proj":     "TDs",
                    "catch_pct":        "Catch%",
                    "fantasy_ppr_proj": "Fant PPR",
                }

            available = {k: v for k, v in cols_show.items() if k in disp.columns}
            out = disp[list(available.keys())].rename(columns=available)\
                                              .sort_values("Fant PPR", ascending=False)\
                                              .head(30)
            st.dataframe(out, use_container_width=True, hide_index=True)

    # ── Free Agency / Team changes ─────────────────────────────────────────────
    st.divider()
    st.subheader("🔄 Notable Free Agency & Trade Moves (2024 → 2026)")
    moved_df = merged_df[merged_df["team_changed"] & merged_df["on_roster"]]\
                   .sort_values("fantasy_ppr_proj", ascending=False)

    if not moved_df.empty:
        moved_display = moved_df[[
            "player_name","position","recent_team","current_team","inj_status","fantasy_ppr_proj"
        ]].rename(columns={
            "player_name": "Player", "position": "Pos",
            "recent_team": "2024 Team", "current_team": "2026 Team",
            "inj_status": "Status", "fantasy_ppr_proj": "Proj PPR",
        }).head(40)
        moved_display["Status"] = moved_display["Status"].apply(injury_badge)
        st.dataframe(moved_display, use_container_width=True, hide_index=True)

    # ── Injury report ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🏥 Full Injury Report — Offensive Players")
    inj_df = merged_df[
        merged_df["inj_status"].isin(["Questionable","Doubtful","Out","IR","PUP","Suspended"])
        & merged_df["on_roster"]
    ].sort_values("fantasy_ppr_proj", ascending=False)

    if not inj_df.empty:
        inj_display = inj_df[[
            "player_name","position","current_team","inj_status",
            "inj_factor","inj_desc","fantasy_ppr_proj"
        ]].rename(columns={
            "player_name": "Player", "position": "Pos", "current_team": "Team",
            "inj_status": "Status", "inj_factor": "Proj Factor",
            "inj_desc": "Description", "fantasy_ppr_proj": "Adj. PPR Proj",
        })
        inj_display["Status"]       = inj_display["Status"].apply(injury_badge)
        inj_display["Proj Factor"]  = inj_display["Proj Factor"].apply(lambda x: f"{x*100:.0f}%")
        st.dataframe(inj_display, use_container_width=True, hide_index=True)

    # ── Fantasy leaders chart (injury-adjusted) ────────────────────────────────
    st.divider()
    st.subheader("Fantasy PPR Leaders — Injury-Adjusted 2026 Projections")
    scoring_type = st.radio("Scoring", ["PPR","Standard"], horizontal=True, key="t2_scoring")
    score_col = "fantasy_ppr_proj" if scoring_type == "PPR" else "fantasy_std_proj"

    active_only = st.checkbox("Exclude IR / Out players from chart", value=True, key="t2_active")
    chart_data = merged_df[merged_df["on_roster"]].copy()
    if active_only:
        chart_data = chart_data[~chart_data["inj_status"].isin(["IR","Out","PUP","NFI","Suspended"])]

    top30 = chart_data.nlargest(30, score_col)
    pos_colors = {"QB":"#D50A0A","RB":"#2ea043","WR":"#388bfd","TE":"#FFB612"}
    bar_colors = [pos_colors.get(p,"#888") for p in top30["position"]]

    fig_f = go.Figure(go.Bar(
        y=top30["player_name"].tolist()[::-1],
        x=top30[score_col].tolist()[::-1],
        orientation="h",
        marker_color=bar_colors[::-1],
        text=[f"{v:.0f}" for v in top30[score_col].tolist()[::-1]],
        textposition="outside",
        customdata=top30[["current_team","position","inj_status"]].values[::-1],
        hovertemplate=(
            "<b>%{y}</b><br>Team: %{customdata[0]}<br>"
            "Pos: %{customdata[1]}<br>Status: %{customdata[2]}<br>"
            "Proj: %{x:.0f} pts<extra></extra>"
        ),
    ))
    for pos, color in pos_colors.items():
        fig_f.add_trace(go.Bar(x=[None], y=[None], marker_color=color, name=pos, orientation="h"))
    fig_f.update_layout(
        height=max(420, len(top30) * 22),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11),
        xaxis=dict(title=f"Projected Fantasy Points ({scoring_type})", gridcolor="#30363d"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", y=1.02, x=0),
        margin=dict(l=10, r=80, t=40, b=20),
        barmode="overlay",
    )
    st.plotly_chart(fig_f, use_container_width=True, config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — MATCHUP PLAYER PROPS (current rosters)
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Matchup Player Props")
    st.caption(
        "Player props based on **current team rosters** (April 2026 free agency complete). "
        "Projections are injury-adjusted. Players who changed teams appear under their new team."
    )

    if merged_df.empty:
        st.info("Load projections first (visit Tab 2).")
        st.stop()

    all_team_abbrs = sorted(set(merged_df["current_team"].dropna().tolist()))
    mc1, mc2 = st.columns(2)
    with mc1:
        away_team = st.selectbox("Away Team", all_team_abbrs,
            index=all_team_abbrs.index("KC") if "KC" in all_team_abbrs else 0,
            key="t3_away")
    with mc2:
        home_opts = [t for t in all_team_abbrs if t != away_team]
        home_team = st.selectbox("Home Team 🏠", home_opts,
            index=home_opts.index("SF") if "SF" in home_opts else 0,
            key="t3_home")

    pred = predict_game(home_team, away_team)

    # Game prediction banner
    gb1, gb2, gb3 = st.columns([2,1,2])
    with gb1:
        st.metric(f"{away_team} (Away)", f"{pred['away_win_prob']*100:.0f}% win prob")
    with gb2:
        st.markdown(
            f"<div style='text-align:center;padding:12px 0'>"
            f"<div style='font-size:1.3rem;font-weight:800'>"
            f"{pred['predicted_away_score']:.0f} – {pred['predicted_home_score']:.0f}"
            f"</div><div style='color:#8b949e;font-size:0.75rem'>Projected score</div>"
            f"<div style='color:#8b949e;font-size:0.75rem'>"
            f"O/U {pred['predicted_total']:.1f} · Spread {abs(pred['predicted_spread']):.1f}"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with gb3:
        st.metric(f"{home_team} 🏠", f"{pred['home_win_prob']*100:.0f}% win prob")

    st.markdown("---")

    def render_team_props(team_abbr: str, df: pd.DataFrame):
        team_players = df[df["current_team"] == team_abbr].copy()
        if team_players.empty:
            st.info(f"No projection data for {team_abbr}.")
            return

        for pos, icon, label in [
            ("QB","🏈","Quarterbacks"), ("RB","🏃","Running Backs"),
            ("WR","📡","Wide Receivers"), ("TE","🎯","Tight Ends"),
        ]:
            pp = team_players[team_players["position"] == pos]\
                     .sort_values("fantasy_ppr_proj", ascending=False).head(3)
            if pp.empty:
                continue
            st.markdown(f"**{icon} {label}**")

            for _, p in pp.iterrows():
                inj = p.get("inj_status","Active")
                badge = injury_badge(inj)
                moved = p.get("team_changed", False)
                move_note = f" ↗ *from {p['recent_team']}*" if moved else ""

                with st.container(border=True):
                    name_line = f"**{p['player_name']}**{move_note}  {badge}"
                    if inj in ("IR","Out","PUP"):
                        name_line = f"~~{p['player_name']}~~{move_note}  {badge}  *(projection heavily discounted)*"
                    st.markdown(name_line)

                    if inj in ("IR","Out","PUP","NFI"):
                        st.markdown(f"*{p.get('inj_desc','No details available')}*")
                        continue

                    s1, s2, s3, s4 = st.columns(4)
                    if pos == "QB":
                        s1.metric("Pass Yds/G",  f"{p.get('pass_yards_pg',0):.0f}",
                                  f"Proj {p.get('pass_yards_proj',0):.0f} season")
                        s2.metric("Pass TDs/G",  f"{p.get('pass_tds_pg',0):.1f}")
                        s3.metric("INTs/G",       f"{p.get('interceptions_pg',0):.1f}")
                        s4.metric("Fant PPR/G",   f"{p.get('fantasy_ppr_pg',0):.1f}",
                                  f"Proj {p.get('fantasy_ppr_proj',0):.0f} pts")
                    elif pos == "RB":
                        s1.metric("Rush Yds/G",  f"{p.get('rush_yards_pg',0):.0f}",
                                  f"Proj {p.get('rush_yards_proj',0):.0f}")
                        s2.metric("Rush TDs/G",  f"{p.get('rush_tds_pg',0):.1f}")
                        s3.metric("Rec Yds/G",   f"{p.get('rec_yards_pg',0):.0f}")
                        s4.metric("Fant PPR/G",   f"{p.get('fantasy_ppr_pg',0):.1f}",
                                  f"Proj {p.get('fantasy_ppr_proj',0):.0f} pts")
                    else:
                        s1.metric("Rec Yds/G",   f"{p.get('rec_yards_pg',0):.0f}",
                                  f"Proj {p.get('rec_yards_proj',0):.0f}")
                        s2.metric("Rec/G",        f"{p.get('receptions_pg',0):.1f}")
                        s3.metric("TDs/G",        f"{p.get('rec_tds_pg',0):.1f}")
                        s4.metric("Fant PPR/G",   f"{p.get('fantasy_ppr_pg',0):.1f}",
                                  f"Proj {p.get('fantasy_ppr_proj',0):.0f} pts")

                    if moved and inj == "Active":
                        st.caption(
                            f"ℹ️ Moved from **{p['recent_team']}** — 2024 stats carried over "
                            "as projection baseline. Scheme fit not yet modeled."
                        )
                    if inj not in ("Active","Healthy") and p.get("inj_desc"):
                        st.caption(f"🏥 {p['inj_desc']}")

    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown(f"### {away_team}")
        render_team_props(away_team, merged_df)
    with pc2:
        st.markdown(f"### {home_team} 🏠")
        render_team_props(home_team, merged_df)

    # ── Comparison chart ───────────────────────────────────────────────────────
    st.divider()
    st.subheader("Head-to-Head Fantasy Projection")

    away_top = merged_df[merged_df["current_team"] == away_team]\
                   .sort_values("fantasy_ppr_proj", ascending=False).head(8)
    home_top = merged_df[merged_df["current_team"] == home_team]\
                   .sort_values("fantasy_ppr_proj", ascending=False).head(8)

    if not away_top.empty and not home_top.empty:
        fig_p = go.Figure()
        for df_t, name, color in [
            (away_top, away_team, "#D50A0A"),
            (home_top, home_team, "#013369"),
        ]:
            fig_p.add_trace(go.Bar(
                name=name,
                x=df_t["player_name"],
                y=df_t["fantasy_ppr_pg"],
                marker_color=color,
                text=[f"{v:.1f}" for v in df_t["fantasy_ppr_pg"]],
                textposition="outside",
                customdata=df_t[["current_team","position","inj_status"]].values,
                hovertemplate=(
                    "<b>%{x}</b><br>%{customdata[0]} %{customdata[1]}<br>"
                    "Status: %{customdata[2]}<br>Proj: %{y:.1f} pts/g<extra></extra>"
                ),
            ))
        fig_p.update_layout(
            title=f"Per-Game Fantasy PPR — {away_team} vs {home_team}",
            barmode="group",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white", size=11),
            height=340,
            yaxis=dict(title="Avg Fantasy Pts / Game", gridcolor="#30363d"),
            xaxis=dict(gridcolor="#30363d", tickangle=-30),
            legend=dict(orientation="h", y=1.05),
            margin=dict(l=0, r=0, t=60, b=60),
        )
        st.plotly_chart(fig_p, use_container_width=True, config={"displayModeBar": False})

    st.info(
        "**Methodology:** Per-game projections use each player's 2024 stat averages "
        "as the base, adjusted for their **current team** (April 2026 rosters) and "
        "**current injury status** from ESPN. Once the 2026 schedule releases (May 2026), "
        "opponent-strength adjustments will layer on top."
    )
