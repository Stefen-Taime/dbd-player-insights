"""
Volume anomaly detector.
Alerts if event volume in the last 6 hours is < 80% of the 7-day moving average.
Run as a standalone script or imported by an Airflow PythonOperator.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def check_volume_anomaly(
    event_table: str = "RAW_MATCH_COMPLETED",
    lookback_hours: int = 6,
    threshold_pct: float = 0.80,
) -> dict:
    """
    Compare recent event volume against the 7-day average.
    Returns a dict with the check result.
    """
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        database="DBD_RAW",
        schema="RAW",
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "ANALYTICS_WH"),
        role=os.environ.get("SNOWFLAKE_ROLE", "MONITOR"),
    )

    try:
        cursor = conn.cursor()

        # Recent volume
        cursor.execute(f"""
            SELECT COUNT(*) FROM {event_table}
            WHERE load_ts >= DATEADD(hour, -{lookback_hours}, CURRENT_TIMESTAMP())
        """)
        recent_count = cursor.fetchone()[0]

        # 7-day average for the same hour window
        cursor.execute(f"""
            SELECT COUNT(*) / 7.0 FROM {event_table}
            WHERE load_ts >= DATEADD(day, -7, CURRENT_TIMESTAMP())
              AND EXTRACT(HOUR FROM load_ts) BETWEEN
                  EXTRACT(HOUR FROM DATEADD(hour, -{lookback_hours}, CURRENT_TIMESTAMP()))
                  AND EXTRACT(HOUR FROM CURRENT_TIMESTAMP())
        """)
        avg_count = cursor.fetchone()[0] or 1

        ratio = recent_count / avg_count if avg_count > 0 else 0

        result = {
            "table": event_table,
            "recent_count": recent_count,
            "avg_7d_count": round(avg_count, 1),
            "ratio": round(ratio, 4),
            "threshold": threshold_pct,
            "status": "OK" if ratio >= threshold_pct else "ANOMALY",
        }

        if ratio < threshold_pct:
            logger.warning(
                "VOLUME ANOMALY on %s: %d events (%.0f%% of 7d avg %.0f)",
                event_table, recent_count, ratio * 100, avg_count,
            )
        else:
            logger.info(
                "Volume OK on %s: %d events (%.0f%% of 7d avg %.0f)",
                event_table, recent_count, ratio * 100, avg_count,
            )

        return result

    finally:
        conn.close()


if __name__ == "__main__":
    tables = [
        "RAW_MATCH_COMPLETED",
        "RAW_SESSION_EVENT",
        "RAW_STORE_TRANSACTION",
    ]
    for table in tables:
        result = check_volume_anomaly(event_table=table)
        print(f"{result['table']}: {result['status']} ({result['ratio']:.0%})")
