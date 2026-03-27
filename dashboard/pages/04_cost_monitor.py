"""
Page 4: Snowflake Cost Monitor -- credit usage, warehouse performance, expensive queries.
Enhanced with cumulative charts, warehouse breakdown, and actionable recommendations.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.snowflake_conn import run_query
from utils.charts import (
    line_chart, area_chart, bar_chart, pie_chart, gauge_chart,
    COLOR_PALETTE, PLOTLY_TEMPLATE, _base_layout,
)

st.header("Snowflake Cost Monitor")
st.caption("Suivi des credits, performance des warehouses et requetes couteuses")

# ═══════════════════════════════════════════════════════════════════════════════
# Credit Consumption
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Consommation de credits (30 derniers jours)")

df_credits = run_query("""
    SELECT
        DATE_TRUNC('day', start_time)::date AS usage_date,
        warehouse_name,
        ROUND(SUM(credits_used), 4) AS credits_used
    FROM snowflake.account_usage.warehouse_metering_history
    WHERE start_time >= DATEADD(day, -30, CURRENT_TIMESTAMP())
    GROUP BY 1, 2
    ORDER BY 1
""")

if not df_credits.empty:
    daily_total = df_credits.groupby("usage_date")["credits_used"].sum().reset_index()
    daily_total["cumulative_credits"] = daily_total["credits_used"].cumsum()
    total_credits = float(daily_total["credits_used"].sum())
    today_credits = float(daily_total.iloc[-1]["credits_used"]) if not daily_total.empty else 0

    # KPIs
    BUDGET = 50.0  # monthly budget in credits
    pct_used = total_credits / BUDGET * 100 if BUDGET > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Credits totaux (30j)", f"{total_credits:.2f}")
    c2.metric("Credits aujourd'hui", f"{today_credits:.4f}")
    c3.metric("Budget mensuel", f"{BUDGET:.0f} credits")
    c4.metric("Budget utilise", f"{pct_used:.1f}%")

    # Gauge
    g1, g2 = st.columns([1, 2])
    with g1:
        st.plotly_chart(
            gauge_chart(
                round(pct_used, 1),
                "Budget utilise",
                suffix="%",
                max_val=150,
                thresholds=[
                    {"range": [0, 70], "color": "#2a9d8f"},
                    {"range": [70, 90], "color": "#e9c46a"},
                    {"range": [90, 150], "color": "#e63946"},
                ],
            ),
            use_container_width=True,
        )

    with g2:
        # Daily + cumulative chart
        fig_c = go.Figure()
        fig_c.add_trace(go.Bar(
            x=daily_total["usage_date"], y=daily_total["credits_used"],
            name="Credits / jour",
            marker_color=COLOR_PALETTE[0],
            opacity=0.7,
        ))
        fig_c.add_trace(go.Scatter(
            x=daily_total["usage_date"], y=daily_total["cumulative_credits"],
            name="Cumul",
            line=dict(color=COLOR_PALETTE[1], width=3),
            yaxis="y2",
        ))
        # Budget line
        fig_c.add_hline(y=BUDGET, line_dash="dash", line_color="red",
                         annotation_text=f"Budget ({BUDGET})", yref="y2")
        _base_layout(fig_c, "Credits quotidiens + Cumul vs Budget")
        fig_c.update_layout(
            yaxis=dict(title="Credits / jour"),
            yaxis2=dict(title="Cumul", overlaying="y", side="right"),
        )
        st.plotly_chart(fig_c, use_container_width=True)

    # Breakdown by warehouse
    st.subheader("Repartition par Warehouse")

    wh_totals = df_credits.groupby("warehouse_name")["credits_used"].sum().reset_index()
    wh_totals = wh_totals.sort_values("credits_used", ascending=False)

    w1, w2 = st.columns([1, 1])
    with w1:
        st.plotly_chart(
            pie_chart(wh_totals, "credits_used", "warehouse_name",
                      "Credits par Warehouse"),
            use_container_width=True,
        )
    with w2:
        st.plotly_chart(
            bar_chart(wh_totals, "warehouse_name", "credits_used",
                      "Credits consommes par Warehouse", text_auto=False),
            use_container_width=True,
        )

    # Stacked area by warehouse over time
    wh_pivot = df_credits.pivot_table(
        values="credits_used", index="usage_date", columns="warehouse_name", aggfunc="sum"
    ).fillna(0).reset_index()

    wh_cols = [c for c in wh_pivot.columns if c != "usage_date"]
    if wh_cols:
        st.plotly_chart(
            area_chart(
                wh_pivot, "usage_date", wh_cols,
                "Tendance quotidienne par Warehouse (empile)",
                y_label="Credits",
                stacked=True,
            ),
            use_container_width=True,
        )

    with st.expander("Donnees detaillees"):
        st.dataframe(
            daily_total.rename(columns={
                "usage_date": "Date", "credits_used": "Credits",
                "cumulative_credits": "Cumul",
            }).style.format({"Credits": "{:.4f}", "Cumul": "{:.4f}"}),
            use_container_width=True,
        )
else:
    st.info("Aucune donnee de metering disponible sur les 30 derniers jours.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Storage
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Stockage")

df_storage = run_query("""
    SELECT
        usage_date,
        ROUND(STORAGE_BYTES / POWER(1024, 3), 2) AS database_gb,
        ROUND(STAGE_BYTES / POWER(1024, 3), 2) AS stage_gb,
        ROUND(FAILSAFE_BYTES / POWER(1024, 3), 2) AS failsafe_gb
    FROM snowflake.account_usage.storage_usage
    WHERE usage_date >= DATEADD(day, -30, CURRENT_DATE())
    ORDER BY usage_date
""")

if not df_storage.empty:
    latest_s = df_storage.iloc[-1]
    s1, s2, s3 = st.columns(3)
    s1.metric("Database", f"{float(latest_s['database_gb']):.2f} GB")
    s2.metric("Stage", f"{float(latest_s['stage_gb']):.2f} GB")
    s3.metric("Failsafe", f"{float(latest_s['failsafe_gb']):.2f} GB")

    st.plotly_chart(
        area_chart(
            df_storage, "usage_date",
            ["database_gb", "stage_gb", "failsafe_gb"],
            "Tendance du stockage (30 jours)",
            y_label="GB",
            stacked=True,
        ),
        use_container_width=True,
    )
else:
    st.info("Aucune donnee de stockage disponible.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Top Expensive Queries
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Top 10 requetes les plus couteuses (7 derniers jours)")

df_queries = run_query("""
    SELECT
        query_id,
        warehouse_name,
        user_name,
        ROUND(total_elapsed_time / 1000, 1) AS elapsed_seconds,
        ROUND(bytes_scanned / POWER(1024, 3), 4) AS gb_scanned,
        ROUND(credits_used_cloud_services, 6) AS credits,
        SUBSTR(query_text, 1, 150) AS query_preview,
        start_time
    FROM snowflake.account_usage.query_history
    WHERE start_time >= DATEADD(day, -7, CURRENT_TIMESTAMP())
        AND execution_status = 'SUCCESS'
        AND warehouse_name IS NOT NULL
    ORDER BY bytes_scanned DESC NULLS LAST
    LIMIT 10
""")

if not df_queries.empty:
    st.dataframe(
        df_queries.rename(columns={
            "query_id": "Query ID", "warehouse_name": "Warehouse",
            "user_name": "User", "elapsed_seconds": "Duree (s)",
            "gb_scanned": "GB scannes", "credits": "Credits",
            "query_preview": "Requete", "start_time": "Debut",
        }).style.format({
            "Duree (s)": "{:.1f}", "GB scannes": "{:.4f}",
            "Credits": "{:.6f}",
        }),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Aucune requete trouvee sur les 7 derniers jours.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Recommendations
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Recommandations d'optimisation")

st.markdown("""
| Categorie | Recommandation | Impact |
|-----------|---------------|--------|
| **Auto-suspend** | Configurer `AUTO_SUSPEND` a 60-300s sur tous les warehouses | Economie de credits en heures creuses |
| **Sizing** | Utiliser XSMALL pour le loading, SMALL pour les transformations | Reduction des couts unitaires |
| **Clustering** | Ajouter des clustering keys sur les colonnes de date | Reduction du scan partitions |
| **Requetes** | Examiner les requetes avec `partition_scan_ratio > 0.5` | Optimisation des performances |
| **Monitoring** | Configurer des alertes Snowflake sur le seuil de credits | Prevention des depassements |
""")
