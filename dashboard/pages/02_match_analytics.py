"""
Page 2: Match Analytics -- Kill rates, perk meta, map balance, MMR distribution.
Enhanced with contextual explanations, color-coded balance indicators, and detailed tables.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.snowflake_conn import run_query
from utils.charts import (
    bar_chart, histogram, pie_chart, gauge_chart,
    COLOR_PALETTE, PLOTLY_TEMPLATE, _base_layout,
)

st.header("Match Analytics")
st.caption("Equilibrage des killers, maps et perks -- source: dbt marts")

# ═══════════════════════════════════════════════════════════════════════════════
# Global Stats
# ═══════════════════════════════════════════════════════════════════════════════
df_global = run_query("""
    SELECT
        ROUND(AVG(kill_rate), 3) AS avg_kill_rate,
        SUM(total_matches) AS total_matches,
        COUNT(DISTINCT killer_character_id) AS unique_killers
    FROM marts.fct_match_outcomes
""")

if not df_global.empty:
    g = df_global.iloc[0]
    c1, c2, c3 = st.columns(3)

    kill_rate_pct = float(g["avg_kill_rate"]) * 100
    c1.metric("Kill Rate moyen", f"{kill_rate_pct:.1f}%")
    c2.metric("Total matchs analyses", f"{int(g['total_matches']):,}")
    c3.metric("Killers uniques", f"{int(g['unique_killers'])}")

    # Gauge for balance
    g1, g2 = st.columns([1, 1])
    with g1:
        st.plotly_chart(
            gauge_chart(
                kill_rate_pct,
                "Balance globale (Kill Rate)",
                suffix="%",
                max_val=100,
                thresholds=[
                    {"range": [0, 40], "color": "#457b9d"},      # survivor-sided
                    {"range": [40, 50], "color": "#2a9d8f"},      # balanced
                    {"range": [50, 60], "color": "#e9c46a"},      # slightly killer-sided
                    {"range": [60, 100], "color": "#e63946"},     # killer-sided
                ],
            ),
            use_container_width=True,
        )
    with g2:
        st.markdown("""
        **Equilibre ideal** : ~50% kill rate (2 kills / 2 escapes par match).
        - < 40% : fortement survivor-sided
        - 40-50% : equilibre
        - 50-60% : legerement killer-sided
        - \\> 60% : fortement killer-sided

        *Le kill rate est calcule comme kills / (4 * matchs).*
        """)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Kill Rate by Killer
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Kill Rate par Killer")

df_killers = run_query("""
    SELECT
        COALESCE(killer_name, killer_character_id) AS killer_name,
        kill_rate, escape_rate, total_matches, avg_kills
    FROM marts.fct_match_outcomes
    WHERE total_matches >= 10
    ORDER BY kill_rate DESC
""")

if not df_killers.empty:
    # Custom horizontal bar with color based on kill rate
    fig_k = go.Figure()
    colors = [
        "#e63946" if kr > 0.6 else "#e9c46a" if kr > 0.5 else "#2a9d8f"
        for kr in df_killers["kill_rate"]
    ]
    fig_k.add_trace(go.Bar(
        y=df_killers["killer_name"],
        x=df_killers["kill_rate"],
        orientation="h",
        marker_color=colors,
        text=[f"{kr:.1%}" for kr in df_killers["kill_rate"]],
        textposition="auto",
    ))
    # Add balance line at 50%
    fig_k.add_vline(x=0.5, line_dash="dash", line_color="white", opacity=0.5,
                     annotation_text="50% (equilibre)")
    _base_layout(fig_k, "Kill Rate par Killer (rouge > 60%, jaune 50-60%, vert < 50%)")
    fig_k.update_layout(yaxis=dict(autorange="reversed"), height=max(400, len(df_killers) * 28))
    fig_k.update_xaxes(tickformat=".0%")

    st.plotly_chart(fig_k, use_container_width=True)

    with st.expander("Tableau detaille des killers"):
        st.dataframe(
            df_killers.rename(columns={
                "killer_name": "Killer", "kill_rate": "Kill Rate",
                "escape_rate": "Escape Rate", "total_matches": "Matchs",
                "avg_kills": "Kills Moy",
            }).style.format({
                "Kill Rate": "{:.1%}", "Escape Rate": "{:.1%}",
                "Matchs": "{:,.0f}", "Kills Moy": "{:.1f}",
            }),
            use_container_width=True, hide_index=True,
        )
else:
    st.warning("Aucune donnee killer disponible.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Map Balance
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Equilibre des Maps")

df_maps = run_query("""
    SELECT
        COALESCE(map_name, map_id) AS map_name,
        COALESCE(realm, 'Unknown') AS realm,
        map_size,
        kill_rate, balance_rating, total_matches,
        ROUND(avg_duration_seconds, 0) AS avg_duration_sec
    FROM marts.fct_map_balance
    WHERE total_matches >= 10
    ORDER BY kill_rate DESC
""")

if not df_maps.empty:
    # Horizontal bar with diverging color
    fig_m = go.Figure()
    map_colors = [
        "#e63946" if kr > 0.6 else "#e9c46a" if kr > 0.5 else "#2a9d8f"
        for kr in df_maps["kill_rate"]
    ]
    fig_m.add_trace(go.Bar(
        y=df_maps["map_name"],
        x=df_maps["kill_rate"],
        orientation="h",
        marker_color=map_colors,
        text=[f"{kr:.1%}" for kr in df_maps["kill_rate"]],
        textposition="auto",
    ))
    fig_m.add_vline(x=0.5, line_dash="dash", line_color="white", opacity=0.5,
                     annotation_text="50% (equilibre)")
    _base_layout(fig_m, "Kill Rate par Map")
    fig_m.update_layout(yaxis=dict(autorange="reversed"), height=max(400, len(df_maps) * 28))
    fig_m.update_xaxes(tickformat=".0%")

    st.plotly_chart(fig_m, use_container_width=True)

    with st.expander("Tableau detaille des maps"):
        st.dataframe(
            df_maps.rename(columns={
                "map_name": "Map", "realm": "Realm", "map_size": "Taille",
                "kill_rate": "Kill Rate", "balance_rating": "Rating",
                "total_matches": "Matchs", "avg_duration_sec": "Duree Moy (s)",
            }).style.format({
                "Kill Rate": "{:.1%}", "Matchs": "{:,.0f}", "Duree Moy (s)": "{:.0f}",
            }),
            use_container_width=True, hide_index=True,
        )
else:
    st.warning("Aucune donnee de map disponible.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Perk Meta
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Meta des Perks")

role_filter = st.selectbox("Role", ["killer", "survivor"], key="perk_role")

df_perks = run_query(f"""
    SELECT
        COALESCE(perk_name, perk_id) AS perk_name,
        role, win_rate, times_used
    FROM marts.fct_perk_performance
    WHERE role = '{role_filter}' AND times_used >= 50
    ORDER BY win_rate DESC
    LIMIT 20
""")

if not df_perks.empty:
    # Bubble chart: win_rate vs times_used
    fig_p = px.scatter(
        df_perks,
        x="times_used", y="win_rate",
        size="times_used", color="win_rate",
        hover_name="perk_name",
        color_continuous_scale="RdYlGn",
        title=f"Top 20 Perks {role_filter.title()} -- Win Rate vs Popularite",
        template=PLOTLY_TEMPLATE,
    )
    fig_p.update_yaxes(tickformat=".0%")
    _base_layout(fig_p, f"Top 20 Perks {role_filter.title()} -- Win Rate vs Popularite")
    fig_p.update_layout(
        xaxis_title="Fois utilise",
        yaxis_title="Win Rate",
        coloraxis_colorbar_title="Win Rate",
    )
    st.plotly_chart(fig_p, use_container_width=True)

    # Also show bar chart
    fig_pb = go.Figure()
    fig_pb.add_trace(go.Bar(
        y=df_perks["perk_name"],
        x=df_perks["win_rate"],
        orientation="h",
        marker_color=COLOR_PALETTE[1],
        text=[f"{wr:.1%}" for wr in df_perks["win_rate"]],
        textposition="auto",
    ))
    _base_layout(fig_pb, f"Win Rate par Perk ({role_filter.title()})")
    fig_pb.update_layout(yaxis=dict(autorange="reversed"), height=max(400, len(df_perks) * 25))
    fig_pb.update_xaxes(tickformat=".0%")
    st.plotly_chart(fig_pb, use_container_width=True)

    with st.expander("Tableau detaille"):
        st.dataframe(
            df_perks.rename(columns={
                "perk_name": "Perk", "role": "Role",
                "win_rate": "Win Rate", "times_used": "Utilisations",
            }).style.format({
                "Win Rate": "{:.1%}", "Utilisations": "{:,.0f}",
            }),
            use_container_width=True, hide_index=True,
        )
else:
    st.info("Pas assez de donnees pour les perks avec ce filtre.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# MMR Distribution
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Distribution du MMR")

df_mmr = run_query("""
    SELECT mmr_bucket, mmr_segment, player_count
    FROM marts.fct_mmr_distribution
    ORDER BY mmr_bucket
""")

if not df_mmr.empty:
    m1, m2 = st.columns([2, 1])
    with m1:
        fig_mmr = px.bar(
            df_mmr, x="mmr_bucket", y="player_count",
            color="mmr_segment",
            title="Distribution des joueurs par tranche de MMR",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=COLOR_PALETTE,
        )
        _base_layout(fig_mmr, "Distribution des joueurs par tranche de MMR")
        fig_mmr.update_layout(xaxis_title="MMR", yaxis_title="Nombre de joueurs")
        st.plotly_chart(fig_mmr, use_container_width=True)

    with m2:
        # Pie chart of segments
        df_seg = df_mmr.groupby("mmr_segment")["player_count"].sum().reset_index()
        st.plotly_chart(
            pie_chart(df_seg, "player_count", "mmr_segment", "Segments MMR"),
            use_container_width=True,
        )

    st.markdown("""
    **Segments MMR** :
    - **New** (0-499) : Nouveaux joueurs en phase d'apprentissage
    - **Casual** (500-999) : Joueurs occasionnels
    - **Core** (1000-1499) : Joueurs reguliers et competents
    - **Hardcore** (1500+) : Joueurs experts
    """)
else:
    st.warning("Aucune donnee MMR disponible.")
