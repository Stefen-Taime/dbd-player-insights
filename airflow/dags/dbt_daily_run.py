"""
DAG: dbt_daily_run
Schedule: Daily at 06:00 UTC
Runs: dbt deps -> dbt seed -> dbt run -> dbt test -> dbt docs generate
Alerts on failure via Slack webhook.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

from utils.slack_alerts import on_failure_slack

DBT_DIR = "/opt/dbt"
DBT_BIN = "/opt/dbt/venv/bin/dbt" if os.path.exists("/opt/dbt/venv/bin/dbt") else "dbt"
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/home/airflow/.dbt")

default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
    "on_failure_callback": on_failure_slack,
}

with DAG(
    dag_id="dbt_daily_run",
    default_args=default_args,
    description="Daily dbt pipeline: seed -> run -> test -> docs",
    schedule="0 6 * * *",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["dbt", "daily"],
) as dag:

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} deps --profiles-dir {DBT_PROFILES_DIR}",
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} seed --profiles-dir {DBT_PROFILES_DIR}",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} run --profiles-dir {DBT_PROFILES_DIR}",
        execution_timeout=timedelta(minutes=60),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} test --profiles-dir {DBT_PROFILES_DIR}",
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"cd {DBT_DIR} && {DBT_BIN} docs generate --profiles-dir {DBT_PROFILES_DIR}",
    )

    dbt_deps >> dbt_seed >> dbt_run >> dbt_test >> dbt_docs
