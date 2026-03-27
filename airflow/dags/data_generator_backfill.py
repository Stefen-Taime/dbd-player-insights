"""
DAG: data_generator_backfill
Schedule: Manual trigger only
Generates historical synthetic data and uploads to S3.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

from utils.slack_alerts import on_failure_slack

default_args = {
    "owner": "data-engineering",
    "retries": 0,
    "execution_timeout": timedelta(hours=2),
    "on_failure_callback": on_failure_slack,
}

with DAG(
    dag_id="data_generator_backfill",
    default_args=default_args,
    description="Generate historical synthetic DBD telemetry data",
    schedule=None,  # Manual trigger only
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["generator", "backfill"],
    params={
        "players": 50000,
        "days": 90,
        "target": "s3",
    },
) as dag:

    generate = BashOperator(
        task_id="generate_data",
        bash_command=(
            "cd /opt/app && python -m generator "
            "--players {{ params.players }} "
            "--days {{ params.days }} "
            "--target {{ params.target }}"
        ),
    )

    notify = BashOperator(
        task_id="notify_completion",
        bash_command='echo "Backfill generation completed: {{ params.players }} players, {{ params.days }} days"',
    )

    generate >> notify
