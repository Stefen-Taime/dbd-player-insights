"""
Reusable helper to create a BashOperator that runs a dbt command.
Keeps DAG code DRY.
"""

from __future__ import annotations

import os
from datetime import timedelta

from airflow.providers.standard.operators.bash import BashOperator

DBT_DIR = os.environ.get("DBT_DIR", "/opt/dbt")
DBT_BIN = os.environ.get("DBT_BIN", "dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/home/airflow/.dbt")


def dbt_task(
    task_id: str,
    dbt_command: str,
    select: str | None = None,
    exclude: str | None = None,
    full_refresh: bool = False,
    execution_timeout: timedelta = timedelta(minutes=30),
    **kwargs,
) -> BashOperator:
    """Create a BashOperator that runs a dbt CLI command."""
    cmd_parts = [
        f"cd {DBT_DIR}",
        f"&& {DBT_BIN} {dbt_command}",
        f"--profiles-dir {DBT_PROFILES_DIR}",
    ]

    if select:
        cmd_parts.append(f"--select {select}")
    if exclude:
        cmd_parts.append(f"--exclude {exclude}")
    if full_refresh:
        cmd_parts.append("--full-refresh")

    return BashOperator(
        task_id=task_id,
        bash_command=" ".join(cmd_parts),
        execution_timeout=execution_timeout,
        **kwargs,
    )
