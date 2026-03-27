"""
Chaos injection layer — injects realistic data quality problems.

This is the module that differentiates this POC from toy projects.
Each chaos function maps to a real production problem that the
dbt layer must solve.

Usage:
    event = generate_match_event(...)
    event = apply_chaos(event, config.chaos, event_time)
"""

from __future__ import annotations

import copy
import random
import uuid
from datetime import datetime, timedelta


def apply_chaos(event: dict, chaos, event_time: datetime) -> list[dict]:
    """
    Apply chaos transformations to an event.

    Returns a LIST of events because:
    - Duplicates produce 2+ copies
    - Most transforms produce exactly 1 event

    The caller should flatten all results into the output batch.
    """
    if not chaos.enabled:
        return [event]

    results = [event]

    # ── 1. Late-arriving events ──
    # Shift the timestamp forward but keep event_id the same.
    # In production, this means the event arrives in a later S3 partition
    # than its logical timestamp suggests.
    if random.random() < chaos.late_event_rate:
        delay_hours = random.uniform(chaos.late_event_min_hours, chaos.late_event_max_hours)
        event["_ingestion_timestamp"] = (
            event_time + timedelta(hours=delay_hours)
        ).isoformat() + "Z"
        # The event's logical timestamp stays the same — this is what makes
        # late-arriving events tricky (they land in "today's" partition but
        # belong to "yesterday's" data)

    # ── 2. Exact duplicates ──
    # Same event_id, same payload — happens when the game client
    # retries a failed telemetry POST.
    if random.random() < chaos.exact_duplicate_rate:
        results.append(copy.deepcopy(event))

    # ── 3. Near-duplicates ──
    # Same event_id but slightly different timestamp or a minor field diff.
    # Happens with client-side clock skew or retry with stale state.
    if random.random() < chaos.near_duplicate_rate:
        near_dupe = copy.deepcopy(event)
        # Shift timestamp by a few seconds
        ts = datetime.fromisoformat(near_dupe["timestamp"].rstrip("Z"))
        ts += timedelta(seconds=random.randint(1, 30))
        near_dupe["timestamp"] = ts.isoformat() + "Z"
        # Occasionally flip a minor field
        if "killer" in near_dupe and random.random() < 0.5:
            near_dupe["killer"]["score"] += random.randint(-500, 500)
        results.append(near_dupe)

    # ── 4. Null injection ──
    # Random nulls in non-critical fields — simulates telemetry client bugs,
    # partial data from crashed game sessions, or platform-specific missing data.
    if random.random() < chaos.null_field_rate:
        nullable_fields = _get_nullable_fields(event)
        if nullable_fields:
            field_to_null = random.choice(nullable_fields)
            _set_nested_null(event, field_to_null)

    # ── 5. Out-of-order events ──
    # Timestamp is slightly before the previous event in the same session.
    # Happens with client-side batching and clock drift.
    if random.random() < chaos.out_of_order_rate:
        ts = datetime.fromisoformat(event["timestamp"].rstrip("Z"))
        ts -= timedelta(seconds=random.randint(1, 120))
        event["timestamp"] = ts.isoformat() + "Z"

    # ── 6. Malformed nested structure ──
    # Instead of survivors being a list, it's a single object.
    # Or perks is a comma-separated string instead of an array.
    if random.random() < chaos.malformed_nested_rate:
        if "survivors" in event and isinstance(event["survivors"], list) and event["survivors"]:
            if random.random() < 0.5:
                # Survivors as single object instead of array
                event["survivors"] = event["survivors"][0]
            else:
                # Perks as comma-separated string instead of array
                for surv in event.get("survivors", []):
                    if isinstance(surv.get("perks"), list):
                        surv["perks"] = ",".join(surv["perks"])

    return results


def apply_volume_outage(
    events: list[dict],
    chaos,
    day: datetime,
    outage_start_hour: int = 3,
) -> list[dict]:
    """
    Simulate a 6h ingestion outage: remove all events within the window.

    This tests the dbt volume_anomaly monitor and Airflow freshness DAG.
    In production, this happens when Kinesis Firehose has a partition issue
    or S3 notifications stop firing.
    """
    if not chaos.enabled or not chaos.volume_outage_enabled:
        return events

    outage_start = day.replace(hour=outage_start_hour, minute=0, second=0)
    outage_end = outage_start + timedelta(hours=chaos.volume_outage_duration_hours)

    return [
        e for e in events
        if not (
            outage_start
            <= datetime.fromisoformat(e["timestamp"].rstrip("Z"))
            < outage_end
        )
    ]


def _get_nullable_fields(event: dict) -> list[str]:
    """Identify non-critical fields that can be set to null."""
    nullable = []
    # Top-level non-critical fields
    for key in ["map_id", "server_region", "client_version",
                "anti_camp_score", "boon_interaction_count",
                "pallet_stun_duration_ms", "generator_regression_events"]:
        if key in event:
            nullable.append(key)

    # Nested: killer/survivor optional fields
    if "killer" in event and isinstance(event["killer"], dict):
        for key in ["offering", "chases_initiated", "chases_won",
                     "pallets_broken", "generators_damaged"]:
            if key in event["killer"]:
                nullable.append(f"killer.{key}")

    if "survivors" in event and isinstance(event["survivors"], list):
        for i, surv in enumerate(event["survivors"]):
            for key in ["offering", "totems_cleansed", "chased_duration_seconds"]:
                if key in surv:
                    nullable.append(f"survivors.{i}.{key}")

    return nullable


def _set_nested_null(event: dict, field_path: str) -> None:
    """Set a nested field to null given a dot-separated path."""
    parts = field_path.split(".")
    obj = event
    for part in parts[:-1]:
        if part.isdigit():
            obj = obj[int(part)]
        else:
            obj = obj[part]
    obj[parts[-1]] = None
