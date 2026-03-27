"""
Slack alert callbacks for Airflow DAGs.
Posts to #macie-finds channel via incoming webhook.
Uses SLACK_WEBHOOK_URL environment variable — no credentials in code.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def on_failure_slack(context: dict) -> None:
    """Send a Slack notification when a task fails."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set — skipping Slack alert")
        return

    try:
        from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook

        dag_id = context.get("dag", {}).dag_id if context.get("dag") else "unknown"
        task_id = context.get("task_instance", {}).task_id if context.get("task_instance") else "unknown"
        logical_date = context.get("logical_date", "unknown")
        log_url = context.get("task_instance").log_url if context.get("task_instance") else ""

        message = (
            f":red_circle: *DAG Failed*\n"
            f"*DAG:* `{dag_id}`\n"
            f"*Task:* `{task_id}`\n"
            f"*Date:* `{logical_date}`\n"
            f"*Log:* <{log_url}|View Log>"
        )

        hook = SlackWebhookHook(slack_webhook_conn_id="slack_webhook")
        hook.send(text=message)
        logger.info("Slack alert sent for %s.%s", dag_id, task_id)

    except Exception:
        logger.exception("Failed to send Slack alert")


def on_success_slack(context: dict) -> None:
    """Send a Slack notification when a DAG succeeds (use on dag-level callback)."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        return

    try:
        from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook

        dag_id = context.get("dag", {}).dag_id if context.get("dag") else "unknown"

        message = f":large_green_circle: *DAG Succeeded:* `{dag_id}`"

        hook = SlackWebhookHook(slack_webhook_conn_id="slack_webhook")
        hook.send(text=message)

    except Exception:
        logger.exception("Failed to send Slack success alert")
