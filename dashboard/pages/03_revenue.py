"""
Page 3: Revenue -- ARPDAU, store conversion, daily revenue breakdown.
Enhanced with waterfall charts, funnel visualization, dual-axis charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.snowflake_conn import run_query
from utils.charts import (
    line_chart, area_chart, pie_chart, bar_chart, gauge_chart,
    funnel_chart, waterfall_chart,
    COLOR_PALETTE, PLOTLY_TEMPLATE, _base_layout,
)

st.header("Revenue")
st.caption("Performance monetaire, ARPDAU, ARPPU et funnel de conversion -- source: dbt marts")

# ═══════════════════════════════════════════════════════════════════════════════
# Daily Revenue
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Revenu quotidien")

df_rev = run_query("""
    SELECT
        revenue_date,
        total_revenue_usd,
        cosmetic_revenue_usd,
        dlc_revenue_usd,
        rift_pass_revenue_usd,
        auric_cells_revenue_usd,
        revenue_7d_avg
    FROM marts.fct_daily_revenue
    ORDER BY revenue_date
""")

if not df_rev.empty:
    latest = df_rev.iloc[-1]

    # Deltas
    if len(df_rev) >= 2:
        prev = df_rev.iloc[-2]
        rev_delta = float(latest["total_revenue_usd"] - prev["total_revenue_usd"])
        avg_delta = float(latest["revenue_7d_avg"] - prev["revenue_7d_avg"])
    else:
        rev_delta = avg_delta = None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Revenu du jour",
        f"${float(latest['total_revenue_usd']):,.0f}",
        delta=f"${rev_delta:+,.0f}" if rev_delta is not None else None,
    )
    c2.metric(
        "Moyenne 7j",
        f"${float(latest['revenue_7d_avg']):,.0f}",
        delta=f"${avg_delta:+,.0f}" if avg_delta is not None else None,
    )
    c3.metric(
        "Revenu total (periode)",
        f"${float(df_rev['total_revenue_usd'].sum()):,.0f}",
    )
    c4.metric(
        "Jours de donnees",
        f"{len(df_rev)}",
    )

    # Daily revenue + 7d avg (area + line)
    fig_rev = go.Figure()
    fig_rev.add_trace(go.Scatter(
        x=df_rev["revenue_date"], y=df_rev["total_revenue_usd"],
        fill="tozeroy", name="Revenu quotidien",
        line=dict(color=COLOR_PALETTE[1], width=1),
        fillcolor="rgba(69,123,157,0.3)",
    ))
    fig_rev.add_trace(go.Scatter(
        x=df_rev["revenue_date"], y=df_rev["revenue_7d_avg"],
        name="Moyenne mobile 7j",
        line=dict(color=COLOR_PALETTE[0], width=3),
    ))
    _base_layout(fig_rev, "Revenu quotidien + Moyenne mobile 7 jours", yaxis_title="USD")
    fig_rev.update_xaxes(showgrid=False)
    fig_rev.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)")
    st.plotly_chart(fig_rev, use_container_width=True)

    # Revenue by category (stacked area)
    st.plotly_chart(
        area_chart(
            df_rev, "revenue_date",
            ["cosmetic_revenue_usd", "dlc_revenue_usd", "rift_pass_revenue_usd", "auric_cells_revenue_usd"],
            "Revenu par categorie (empile)",
            y_label="USD",
            stacked=True,
        ),
        use_container_width=True,
    )

    # Waterfall breakdown
    categories = ["Cosmetics", "DLC", "Rift Pass", "Auric Cells"]
    values = [
        float(df_rev["cosmetic_revenue_usd"].sum()),
        float(df_rev["dlc_revenue_usd"].sum()),
        float(df_rev["rift_pass_revenue_usd"].sum()),
        float(df_rev["auric_cells_revenue_usd"].sum()),
    ]

    w1, w2 = st.columns([1, 1])
    with w1:
        st.plotly_chart(
            waterfall_chart(
                list(categories), list(values),
                "Decomposition du revenu total",
            ),
            use_container_width=True,
        )
    with w2:
        df_bd = pd.DataFrame({"category": categories, "revenue_usd": values})
        st.plotly_chart(
            pie_chart(df_bd, "revenue_usd", "category", "Repartition du revenu"),
            use_container_width=True,
        )

    with st.expander("Donnees de revenu detaillees"):
        st.dataframe(
            df_rev.rename(columns={
                "revenue_date": "Date", "total_revenue_usd": "Total ($)",
                "cosmetic_revenue_usd": "Cosmetics ($)", "dlc_revenue_usd": "DLC ($)",
                "rift_pass_revenue_usd": "Rift Pass ($)", "auric_cells_revenue_usd": "Auric ($)",
                "revenue_7d_avg": "Moy 7j ($)",
            }).style.format({
                "Total ($)": "${:,.2f}", "Cosmetics ($)": "${:,.2f}",
                "DLC ($)": "${:,.2f}", "Rift Pass ($)": "${:,.2f}",
                "Auric ($)": "${:,.2f}", "Moy 7j ($)": "${:,.2f}",
            }),
            use_container_width=True,
        )
else:
    st.warning("Aucune donnee de revenu disponible.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# ARPDAU & ARPPU
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("ARPDAU / ARPPU / Conversion")

df_arp = run_query("""
    SELECT metric_date, arpdau, arppu, payer_conversion_rate
    FROM marts.fct_arpdau
    ORDER BY metric_date
""")

if not df_arp.empty:
    # Fill NaN from NULL divisions (e.g. days with 0 paying users)
    df_arp = df_arp.fillna({"arpdau": 0, "arppu": 0, "payer_conversion_rate": 0})
    latest_arp = df_arp.iloc[-1]

    a1, a2, a3 = st.columns(3)
    a1.metric("ARPDAU", f"${float(latest_arp['arpdau']):.4f}")
    a2.metric("ARPPU", f"${float(latest_arp['arppu']):.2f}")
    a3.metric("Taux de conversion payant", f"{float(latest_arp['payer_conversion_rate']):.2%}")

    # Gauges
    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(
            gauge_chart(
                round(float(latest_arp["arpdau"]) * 100, 2),
                "ARPDAU (cents)",
                suffix=" c",
                max_val=20,
                thresholds=[
                    {"range": [0, 5], "color": "#e63946"},
                    {"range": [5, 10], "color": "#e9c46a"},
                    {"range": [10, 20], "color": "#2a9d8f"},
                ],
            ),
            use_container_width=True,
        )
    with g2:
        st.plotly_chart(
            gauge_chart(
                round(float(latest_arp["arppu"]), 2),
                "ARPPU ($)",
                suffix="$",
                max_val=50,
                thresholds=[
                    {"range": [0, 10], "color": "#e63946"},
                    {"range": [10, 25], "color": "#e9c46a"},
                    {"range": [25, 50], "color": "#2a9d8f"},
                ],
            ),
            use_container_width=True,
        )
    with g3:
        st.plotly_chart(
            gauge_chart(
                round(float(latest_arp["payer_conversion_rate"]) * 100, 2),
                "Conversion %",
                suffix="%",
                max_val=10,
                thresholds=[
                    {"range": [0, 2], "color": "#e63946"},
                    {"range": [2, 5], "color": "#e9c46a"},
                    {"range": [5, 10], "color": "#2a9d8f"},
                ],
            ),
            use_container_width=True,
        )

    # Dual axis chart: ARPDAU + ARPPU
    fig_arp = go.Figure()
    fig_arp.add_trace(go.Scatter(
        x=df_arp["metric_date"], y=df_arp["arpdau"],
        name="ARPDAU", yaxis="y",
        line=dict(color=COLOR_PALETTE[0], width=2),
    ))
    fig_arp.add_trace(go.Scatter(
        x=df_arp["metric_date"], y=df_arp["arppu"],
        name="ARPPU", yaxis="y2",
        line=dict(color=COLOR_PALETTE[1], width=2),
    ))
    _base_layout(fig_arp, "ARPDAU vs ARPPU dans le temps")
    fig_arp.update_layout(
        yaxis=dict(title=dict(text="ARPDAU ($)", font=dict(color=COLOR_PALETTE[0]))),
        yaxis2=dict(title=dict(text="ARPPU ($)", font=dict(color=COLOR_PALETTE[1])),
                     overlaying="y", side="right"),
    )
    st.plotly_chart(fig_arp, use_container_width=True)

    # Conversion rate trend
    st.plotly_chart(
        line_chart(df_arp, "metric_date", "payer_conversion_rate",
                   "Taux de conversion payant dans le temps", "Taux"),
        use_container_width=True,
    )

    st.markdown("""
    **Definitions** :
    - **ARPDAU** (Average Revenue Per Daily Active User) = Revenu total / DAU
    - **ARPPU** (Average Revenue Per Paying User) = Revenu total / Nombre de payeurs
    - **Conversion** = Payeurs / DAU

    Benchmarks F2P mobile : ARPDAU $0.05-0.15, Conversion 2-5%, ARPPU $5-25
    """)
else:
    st.warning("Aucune donnee ARPDAU disponible.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# Store Conversion Funnel
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("Funnel de conversion du store")

df_funnel = run_query("""
    SELECT metric_date, active_users, store_visitors, purchasers,
           visit_rate, purchase_rate, overall_conversion_rate
    FROM marts.fct_store_conversion
    ORDER BY metric_date
""")

if not df_funnel.empty:
    latest_f = df_funnel.iloc[-1]

    # Funnel chart
    stages = ["Joueurs actifs", "Visiteurs du store", "Acheteurs"]
    values = [
        float(latest_f["active_users"]),
        float(latest_f["store_visitors"]),
        float(latest_f["purchasers"]),
    ]
    st.plotly_chart(
        funnel_chart(stages, values, "Funnel de conversion (dernier jour)"),
        use_container_width=True,
    )

    # Conversion rates over time
    st.plotly_chart(
        line_chart(
            df_funnel, "metric_date",
            ["visit_rate", "purchase_rate", "overall_conversion_rate"],
            "Taux de conversion dans le temps",
            "Taux",
        ),
        use_container_width=True,
    )

    with st.expander("Donnees du funnel"):
        st.dataframe(
            df_funnel.rename(columns={
                "metric_date": "Date", "active_users": "Actifs",
                "store_visitors": "Visiteurs", "purchasers": "Acheteurs",
                "visit_rate": "Taux visite", "purchase_rate": "Taux achat",
                "overall_conversion_rate": "Conversion globale",
            }).style.format({
                "Actifs": "{:,.0f}", "Visiteurs": "{:,.0f}", "Acheteurs": "{:,.0f}",
                "Taux visite": "{:.2%}", "Taux achat": "{:.2%}", "Conversion globale": "{:.2%}",
            }),
            use_container_width=True,
        )
else:
    st.info("Aucune donnee de funnel store disponible.")
