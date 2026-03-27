"""
DAG: snowflake_cost_monitor
Schedule: Daily at 08:00 UTC
Checks Snowflake credit consumption and sends alerts if budget thresholds exceeded.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

from utils.slack_alerts import on_failure_slack
from utils.snowflake_checks import check_credit_usage, check_expensive_queries

default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": on_failure_slack,
}

with DAG(
    dag_id="snowflake_cost_monitor",
    default_args=default_args,
    description="Daily Snowflake cost monitoring and alerting",
    schedule="0 8 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["snowflake", "cost", "monitoring"],
) as dag:

    credit_check = PythonOperator(
        task_id="check_credit_usage",
        python_callable=check_credit_usage,
        op_kwargs={
            "monthly_budget": float(os.environ.get("SNOWFLAKE_MONTHLY_BUDGET", "10")),
            "warn_threshold": 0.80,
        },
    )

    expensive_queries = PythonOperator(
        task_id="check_expensive_queries",
        python_callable=check_expensive_queries,
        op_kwargs={
            "max_bytes_scanned_tb": 1.0,
        },
    )

    credit_check >> expensive_queries
