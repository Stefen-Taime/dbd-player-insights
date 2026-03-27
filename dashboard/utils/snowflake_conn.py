"""
Cached Snowflake connection for Streamlit.
All credentials from environment variables — no hardcoded secrets.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st


@st.cache_resource
def get_connection():
    """Create a cached Snowflake connection."""
    import snowflake.connector

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database=os.environ.get("SNOWFLAKE_DATABASE", "DBD_ANALYTICS"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "ANALYTICS_WH"),
        role=os.environ.get("SNOWFLAKE_ROLE", "ANALYST"),
        schema="MARTS",
    )


@st.cache_data(ttl=300)
def run_query(query: str) -> pd.DataFrame:
    """Execute a query and return results as a DataFrame. Cached for 5 minutes."""
    conn = get_connection()
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df
