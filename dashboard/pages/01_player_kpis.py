"""
Page 1: Player KPIs -- DAU/MAU, retention, LTV, churn segments.
Enhanced with gauge charts, area charts, detailed tables, and contextual info.
"""

import streamlit as st
import pandas as pd

from utils.snowflake_conn import run_query
from utils.charts import (
    line_chart, area_chart, bar_chart, pie_chart,
    gauge_chart, histogram, COLOR_PALETTE,
)

st.header("Player KPIs")
st.caption("Metriques d'engagement, retention et valeur des joueurs -- source: dbt marts")

# ═══════════════════════════════════════════════════════════════════════════════
# DAU / MAU / Stickiness
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Engagement quotidien")

df_dau = run_query("""
    SELECT metric_date, dau, wau, mau, stickiness_ratio
    FROM marts.fct_dau_mau
    ORDER BY metric_date
""")

if not df_dau.empty:
    latest = df_dau.iloc[-1]

    # Compute deltas vs previous day
    if len(df_dau) >= 2:
        prev = df_dau.iloc[-2]
        dau_delta = int(latest["dau"] - prev["dau"])
        mau_delta = int(latest["mau"] - prev["mau"])
        stick_delta = latest["stickiness_ratio"] - prev["stickiness_ratio"]
    else:
        dau_delta = mau_delta = stick_delta = None

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "DAU", f"{int(latest['dau']):,}",
        delta=f"{dau_delta:+,}" if dau_delta is not None else None,
    )
    c2.metric(
        "WAU", f"{int(latest['wau']):,}",
    )
    c3.metric(
        "MAU", f"{int(latest['mau']):,}",
        delta=f"{mau_delta:+,}" if mau_delta is not None else None,
    )
    c4.metric(
        "Stickiness (DAU/MAU)", f"{latest['stickiness_ratio']:.1%}",
        delta=f"{stick_delta:+.1%}" if stick_delta is not None else None,
    )

    # Gauge for stickiness
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(
            gauge_chart(
                round(float(latest["stickiness_ratio"]) * 100, 1),
                "Stickiness Ratio",
                suffix="%",
                max_val=50,
                thresholds=[
                    {"range": [0, 15], "color": "#e63946"},
                    {"range": [15, 25], "color": "#e9c46a"},
                    {"range": [25, 50], "color": "#2a9d8f"},
                ],
            ),
            use_container_width=True,
        )
    with g2:
        st.markdown("""
        **Comment lire ce graphique :**
        - **Stickiness** = DAU / MAU. Mesure quelle fraction des utilisateurs mensuels revient chaque jour.
        - < 15% : faible engagement
        - 15-25% : engagement moyen
        - \\> 25% : excellent (jeux top tier)

        Un stickiness eleve indique que le jeu fait partie de la routine quotidienne des joueurs.
        """)

    # Area chart: DAU / WAU / MAU over time
    st.plotly_chart(
        area_chart(
            df_dau, "metric_date", ["dau", "wau", "mau"],
            "Utilisateurs actifs dans le temps (DAU / WAU / MAU)",
            y_label="Joueurs",
        ),
        use_container_width=True,
    )

    # Stickiness trend
    st.plotly_chart(
        line_chart(
            df_dau, "metric_date", "stickiness_ratio",
            "Evolution du Stickiness (DAU/MAU)",
            y_label="Ratio",
        ),
        use_container_width=True,
    )

    with st.expander("Voir les donnees brutes"):
        st.dataframe(
            df_dau.style.format({
                "dau": "{:,.0f}", "wau": "{:,.0f}", "mau": "{:,.0f}",
                "stickiness_ratio": "{:.2%}",
            }),
            use_container_width=True,
        )
else:
    st.warning("Aucune donnee DAU/MAU disponible.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Retention by Cohort
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Retention par cohorte hebdomadaire")

df_ret = run_query("""
    SELECT cohort_week, cohort_size, retention_d1, retention_d7, retention_d30
    FROM marts.fct_player_retention
    ORDER BY cohort_week
""")

if not df_ret.empty:
    # KPI cards for latest cohort
    latest_ret = df_ret.iloc[-1]
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Cohorte", str(latest_ret["cohort_week"])[:10])
    r2.metric("Retention D1", f"{latest_ret['retention_d1']:.1%}")
    r3.metric("Retention D7", f"{latest_ret['retention_d7']:.1%}")
    r4.metric("Retention D30", f"{latest_ret['retention_d30']:.1%}")

    st.plotly_chart(
        line_chart(
            df_ret, "cohort_week",
            ["retention_d1", "retention_d7", "retention_d30"],
            "Retention D1 / D7 / D30 par cohorte",
            y_label="Taux de retention",
        ),
        use_container_width=True,
    )

    st.markdown("""
    **Benchmarks industrie (F2P)** :
    D1 ~ 30-40%, D7 ~ 15-20%, D30 ~ 5-10%.
    Une retention D1 elevee indique un bon onboarding.
    """)

    with st.expander("Voir les donnees brutes"):
        st.dataframe(
            df_ret.style.format({
                "cohort_size": "{:,.0f}",
                "retention_d1": "{:.2%}", "retention_d7": "{:.2%}", "retention_d30": "{:.2%}",
            }),
            use_container_width=True,
        )
else:
    st.info("Aucune donnee de retention disponible -- les cohortes necessitent au moins 30 jours de donnees.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Churn Segments
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Segments de Churn")

df_churn = run_query("""
    SELECT churn_segment, COUNT(*) as player_count
    FROM marts.fct_player_lifetime
    GROUP BY 1
    ORDER BY
        CASE churn_segment
            WHEN 'active' THEN 1
            WHEN 'at_risk' THEN 2
            WHEN 'dormant' THEN 3
            WHEN 'churned' THEN 4
        END
""")

if not df_churn.empty:
    total_players = int(df_churn["player_count"].sum())

    ch1, ch2 = st.columns([1, 1])
    with ch1:
        st.plotly_chart(
            pie_chart(df_churn, "player_count", "churn_segment", "Repartition des segments de churn"),
            use_container_width=True,
        )
    with ch2:
        st.markdown("**Definitions des segments :**")
        st.markdown("""
        | Segment | Definition |
        |---------|------------|
        | **Active** | Vu dans les 7 derniers jours |
        | **At risk** | Vu entre 8 et 14 jours |
        | **Dormant** | Vu entre 15 et 30 jours |
        | **Churned** | Absent depuis > 30 jours |
        """)
        st.metric("Total joueurs", f"{total_players:,}")

        # Show percentages
        for _, row in df_churn.iterrows():
            pct = row["player_count"] / total_players * 100
            st.progress(pct / 100, text=f"{row['churn_segment'].title()}: {int(row['player_count']):,} ({pct:.1f}%)")
else:
    st.warning("Aucune donnee de churn disponible.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Lifetime Value Distribution
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Distribution de la Lifetime Value (LTV)")

df_ltv = run_query("""
    SELECT
        CASE
            WHEN lifetime_spend_usd = 0 THEN '$0 (Free)'
            WHEN lifetime_spend_usd < 10 THEN '$1 - $9'
            WHEN lifetime_spend_usd < 50 THEN '$10 - $49'
            WHEN lifetime_spend_usd < 100 THEN '$50 - $99'
            ELSE '$100+'
        END AS ltv_bucket,
        COUNT(*) as player_count,
        ROUND(AVG(lifetime_spend_usd), 2) as avg_spend,
        ROUND(AVG(lifetime_sessions), 0) as avg_sessions,
        ROUND(AVG(total_matches), 0) as avg_matches
    FROM marts.fct_player_lifetime
    GROUP BY 1
    ORDER BY MIN(lifetime_spend_usd)
""")

if not df_ltv.empty:
    l1, l2 = st.columns([1, 1])
    with l1:
        st.plotly_chart(
            bar_chart(
                df_ltv, "ltv_bucket", "player_count",
                "Nombre de joueurs par tranche de depense",
                text_auto=False,
            ),
            use_container_width=True,
        )
    with l2:
        st.plotly_chart(
            bar_chart(
                df_ltv, "ltv_bucket", "avg_spend",
                "Depense moyenne par tranche (USD)",
                text_auto=False,
            ),
            use_container_width=True,
        )

    st.dataframe(
        df_ltv.rename(columns={
            "ltv_bucket": "Tranche LTV",
            "player_count": "Nb Joueurs",
            "avg_spend": "Depense Moy ($)",
            "avg_sessions": "Sessions Moy",
            "avg_matches": "Matches Moy",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("""
    **Insight** : Les joueurs qui depensent sont generalement ceux avec le plus de sessions et de matchs.
    La retention de ces joueurs payants est critique pour le revenu long terme.
    """)

    # Top 10 whales
    st.subheader("Top 10 joueurs par LTV")
    df_top = run_query("""
        SELECT player_id, platform, lifetime_spend_usd, lifetime_sessions,
               total_matches, total_active_days, churn_segment
        FROM marts.fct_player_lifetime
        ORDER BY lifetime_spend_usd DESC
        LIMIT 10
    """)
    if not df_top.empty:
        st.dataframe(
            df_top.rename(columns={
                "player_id": "Player ID", "platform": "Platform",
                "lifetime_spend_usd": "LTV ($)", "lifetime_sessions": "Sessions",
                "total_matches": "Matches", "total_active_days": "Jours actifs",
                "churn_segment": "Segment",
            }).style.format({"LTV ($)": "${:,.2f}"}),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.warning("Aucune donnee LTV disponible.")
