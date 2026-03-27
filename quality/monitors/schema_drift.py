"""
Schema drift detector.
Compares JSON keys in the latest batch against the expected schema.
Alerts if new keys appear or expected keys are missing.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Expected top-level keys per event type
EXPECTED_SCHEMAS: dict[str, set[str]] = {
    "RAW_MATCH_COMPLETED": {
        "event_type", "event_id", "timestamp", "match_id",
        "duration_seconds", "map_id", "game_mode", "killer", "survivors",
    },
    "RAW_SESSION_EVENT": {
        "event_type", "event_id", "timestamp", "player_id",
        "session_id", "action", "platform", "region", "client_version",
    },
    "RAW_STORE_TRANSACTION": {
        "event_type", "event_id", "timestamp", "player_id",
        "transaction_id", "item_id", "item_type", "currency", "amount", "amount_usd",
    },
}


def check_schema_drift(
    event_table: str = "RAW_MATCH_COMPLETED",
    sample_size: int = 100,
) -> dict:
    """
    Sample recent rows and compare JSON keys against expected schema.
    Returns a dict with new_keys and missing_keys.
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

        cursor.execute(f"""
            SELECT DISTINCT f.key
            FROM {event_table},
                 LATERAL FLATTEN(input => raw_data) f
            WHERE load_ts >= DATEADD(hour, -6, CURRENT_TIMESTAMP())
            LIMIT {sample_size * 20}
        """)

        actual_keys = {row[0] for row in cursor.fetchall()}
        expected_keys = EXPECTED_SCHEMAS.get(event_table, set())

        new_keys = actual_keys - expected_keys
        missing_keys = expected_keys - actual_keys

        result = {
            "table": event_table,
            "actual_keys": sorted(actual_keys),
            "new_keys": sorted(new_keys),
            "missing_keys": sorted(missing_keys),
            "status": "DRIFT" if (new_keys or missing_keys) else "OK",
        }

        if new_keys:
            logger.warning("SCHEMA DRIFT on %s: new keys %s", event_table, new_keys)
        if missing_keys:
            logger.warning("SCHEMA DRIFT on %s: missing keys %s", event_table, missing_keys)
        if not new_keys and not missing_keys:
            logger.info("Schema OK on %s", event_table)

        return result

    finally:
        conn.close()


if __name__ == "__main__":
    for table in EXPECTED_SCHEMAS:
        result = check_schema_drift(event_table=table)
        print(f"{result['table']}: {result['status']} | new={result['new_keys']} missing={result['missing_keys']}")
