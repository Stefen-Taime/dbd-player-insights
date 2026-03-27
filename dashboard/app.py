"""
DBD Player Insights -- Streamlit Dashboard
Multi-page entry point.
"""

import streamlit as st

st.set_page_config(
    page_title="DBD Player Insights",
    page_icon=":knife:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("DBD Player Insights")

st.markdown("""
Tableau de bord analytique pour **Dead by Daylight**.
Les donnees sont ingérées depuis S3, transformées par **dbt** dans **Snowflake**,
orchestrées par **Airflow**, et visualisées ici avec **Plotly**.

---

### Pages disponibles

| Page | Description |
|------|-------------|
| **Player KPIs** | DAU / MAU / WAU, stickiness, retention par cohorte, segments de churn, LTV |
| **Match Analytics** | Kill rate par killer, balance des maps, meta des perks, distribution MMR |
| **Revenue** | Revenu quotidien, ARPDAU / ARPPU, breakdown par categorie, funnel de conversion |
| **Cost Monitor** | Credits Snowflake consommes, tendance par warehouse, requetes couteuses |

---
*Pipeline: S3 (raw JSON) -> Snowflake (staging) -> dbt (marts) -> Streamlit + Grafana*
""")
