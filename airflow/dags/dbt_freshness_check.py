"""
DAG: dbt_freshness_check
Schedule: Every 2 hours
Checks source freshness SLAs defined in dbt sources.yml.
Alerts on failure via Slack webhook.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

from utils.slack_alerts import on_failure_slack

DBT_DIR = "/opt/dbt"
DBT_BIN = os.environ.get("DBT_BIN", "dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/home/airflow/.dbt")

default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=10),
    "on_failure_callback": on_failure_slack,
}

with DAG(
    dag_id="dbt_freshness_check",
    default_args=default_args,
    description="Check dbt source freshness every 2 hours",
    schedule="0 */2 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dbt", "quality"],
) as dag:

    check_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=(
            f"cd {DBT_DIR} && {DBT_BIN} source freshness "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--output /tmp/freshness_output.json"
        ),
    )
