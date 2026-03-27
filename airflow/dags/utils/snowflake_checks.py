"""
Snowflake health and cost monitoring checks.
Credentials come from environment variables — no hardcoded secrets.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def _get_snowflake_connection():
    """Create a Snowflake connection from environment variables."""
    import snowflake.connector

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database="SNOWFLAKE",
        schema="ACCOUNT_USAGE",
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "ANALYTICS_WH"),
        role=os.environ.get("SNOWFLAKE_ROLE", "MONITOR"),
    )


def check_credit_usage(monthly_budget: float = 10.0, warn_threshold: float = 0.80, **kwargs) -> dict:
    """Check current month credit usage against budget."""
    conn = _get_snowflake_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                SUM(credits_used) as total_credits
            FROM snowflake.account_usage.warehouse_metering_history
            WHERE start_time >= DATE_TRUNC('month', CURRENT_TIMESTAMP())
        """)
        row = cursor.fetchone()
        total_credits = float(row[0]) if row and row[0] else 0.0

        usage_pct = total_credits / monthly_budget if monthly_budget > 0 else 0.0

        result = {
            "total_credits_used": total_credits,
            "monthly_budget": monthly_budget,
            "usage_pct": round(usage_pct, 4),
        }

        if usage_pct >= 1.0:
            logger.error("BUDGET EXCEEDED: %.2f / %.2f credits (%.0f%%)", total_credits, monthly_budget, usage_pct * 100)
            raise Exception(f"Monthly Snowflake budget exceeded: {total_credits:.2f} / {monthly_budget:.2f} credits")
        elif usage_pct >= warn_threshold:
            logger.warning("Budget warning: %.2f / %.2f credits (%.0f%%)", total_credits, monthly_budget, usage_pct * 100)
        else:
            logger.info("Budget OK: %.2f / %.2f credits (%.0f%%)", total_credits, monthly_budget, usage_pct * 100)

        return result

    finally:
        conn.close()


def check_expensive_queries(max_bytes_scanned_tb: float = 1.0, **kwargs) -> list[dict]:
    """Find queries that scanned more than the threshold (in TB)."""
    conn = _get_snowflake_connection()
    try:
        cursor = conn.cursor()
        max_bytes = max_bytes_scanned_tb * (1024 ** 4)

        cursor.execute(f"""
            SELECT
                query_id,
                user_name,
                warehouse_name,
                bytes_scanned,
                total_elapsed_time / 1000 as elapsed_seconds,
                SUBSTR(query_text, 1, 200) as query_preview
            FROM snowflake.account_usage.query_history
            WHERE start_time >= DATEADD(day, -1, CURRENT_TIMESTAMP())
                AND bytes_scanned > {max_bytes}
                AND execution_status = 'SUCCESS'
            ORDER BY bytes_scanned DESC
            LIMIT 10
        """)

        expensive = []
        for row in cursor.fetchall():
            expensive.append({
                "query_id": row[0],
                "user": row[1],
                "warehouse": row[2],
                "gb_scanned": round(float(row[3]) / (1024 ** 3), 2),
                "elapsed_seconds": float(row[4]),
                "preview": row[5],
            })

        if expensive:
            logger.warning("Found %d expensive queries (> %.1f TB scanned)", len(expensive), max_bytes_scanned_tb)
        else:
            logger.info("No queries exceeded %.1f TB scan threshold", max_bytes_scanned_tb)

        return expensive

    finally:
        conn.close()
