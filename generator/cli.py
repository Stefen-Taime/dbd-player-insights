"""
CLI for the DBD telemetry data generator.

Usage:
    python -m generator --players 50000 --days 90 --target local
    python -m generator --players 50000 --days 90 --target s3 --bucket dbd-telemetry-raw
    python -m generator --players 1000 --days 7 --chaos-off   # Clean data for testing
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
from datetime import datetime, timedelta

import orjson

from generator.config import ChaosConfig, GeneratorConfig
from generator.models.chaos import apply_chaos, apply_volume_outage
from generator.models.events import (
    generate_mmr_update,
    generate_progression_event,
    generate_session_events,
    generate_store_transaction,
)
from generator.models.match import generate_match_event
from generator.models.player import generate_player_pool
from generator.publishers.local_publisher import LocalPublisher
from generator.publishers.s3_publisher import S3Publisher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_generation(config: GeneratorConfig, publisher) -> dict:
    """
    Main generation loop.

    For each simulated day:
    1. Determine active players (DAU)
    2. Generate sessions → matches → progression → MMR → store
    3. Apply chaos transformations
    4. Publish events in batches

    Returns summary stats.
    """
    logger.info(
        "Starting generation: %d players, %d days, chaos=%s",
        config.num_players, config.num_days, config.chaos.enabled,
    )

    # Generate player pool
    players = generate_player_pool(config)
    logger.info("Generated %d player profiles", len(players))

    # Publish registration events
    reg_events = [p.to_registration_event() for p in players]
    publisher.publish_batch(reg_events, "player_registration")
    logger.info("Published %d registration events", len(reg_events))

    stats = {
        "total_events": len(reg_events),
        "match_events": 0,
        "session_events": 0,
        "store_events": 0,
        "progression_events": 0,
        "mmr_events": 0,
        "chaos_duplicates": 0,
        "chaos_late_events": 0,
        "chaos_outage_events_removed": 0,
    }

    # Determine which day gets the volume outage (1 per 30-day window)
    outage_day_offset = random.randint(10, min(25, config.num_days - 1))

    # Day-by-day simulation
    for day_offset in range(config.num_days):
        current_day = config.start_date + timedelta(days=day_offset)
        active_patch = config.get_active_patch(current_day)

        # Determine today's active players
        active_players = [
            p for p in players
            if p.registration_date <= current_day
            and not p.churned
        ]

        # DAU sampling
        dau_count = int(len(active_players) * config.daily_active_pct)
        dau_count = max(1, min(dau_count, len(active_players)))
        todays_players = random.sample(active_players, dau_count)

        day_events = []

        for player in todays_players:
            # Session time: weighted toward evening hours
            hour = random.choices(
                range(24),
                weights=[1, 0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 1, 2, 3, 3, 3,
                         4, 4, 4, 5, 6, 7, 8, 9, 9, 8, 5, 3],
            )[0]
            session_start = current_day.replace(
                hour=hour,
                minute=random.randint(0, 59),
                second=random.randint(0, 59),
            )

            # ── Session events ──
            session_events = generate_session_events(
                player, session_start, config, active_patch,
            )
            day_events.extend(session_events)
            stats["session_events"] += len(session_events)

            # ── Matches ──
            num_matches = max(1, int(random.gauss(config.avg_matches_per_session, 1.2)))
            match_time = session_start + timedelta(minutes=random.randint(5, 15))

            for _ in range(num_matches):
                # Pick 4 random survivors from today's active pool
                other_players = [p for p in todays_players if p.bhvr_id != player.bhvr_id]
                if len(other_players) < 4:
                    continue

                survivors = random.sample(other_players, 4)

                match_event = generate_match_event(
                    player, survivors, match_time, config, active_patch,
                )

                # Apply chaos to match event
                chaos_results = apply_chaos(match_event, config.chaos, match_time)
                if len(chaos_results) > 1:
                    stats["chaos_duplicates"] += len(chaos_results) - 1
                if "_ingestion_timestamp" in chaos_results[0]:
                    stats["chaos_late_events"] += 1

                day_events.extend(chaos_results)
                stats["match_events"] += 1

                # ── Progression ──
                bp_earned = random.randint(
                    int(config.avg_bloodpoints_per_match * 0.4),
                    int(config.avg_bloodpoints_per_match * 1.8),
                )
                prog_event = generate_progression_event(
                    player, match_time + timedelta(seconds=10),
                    bp_earned, config, active_patch,
                )
                day_events.append(prog_event)
                stats["progression_events"] += 1

                # ── MMR update ──
                kills = match_event.get("killer", {}).get("kills", 0)
                result = "win" if kills >= 3 else ("draw" if kills == 2 else "loss")
                mmr_event = generate_mmr_update(
                    player, match_time + timedelta(seconds=15),
                    "killer", result, config, active_patch,
                )
                day_events.append(mmr_event)
                stats["mmr_events"] += 1

                match_time += timedelta(minutes=random.randint(8, 20))

            # ── Store transaction (paying players only) ──
            if player.is_paying and random.random() < 0.05:
                store_time = session_start + timedelta(
                    minutes=random.randint(10, int(config.avg_session_duration_minutes)),
                )
                store_event = generate_store_transaction(
                    player, store_time, config, active_patch,
                )
                chaos_results = apply_chaos(store_event, config.chaos, store_time)
                day_events.extend(chaos_results)
                stats["store_events"] += 1

            # ── Churn check ──
            if random.random() < config.churn_probability_per_day:
                player.churned = True
                player.churn_date = current_day

            player.last_active = current_day

        # ── Volume outage simulation ──
        if day_offset == outage_day_offset and config.chaos.volume_outage_enabled:
            before_count = len(day_events)
            day_events = apply_volume_outage(day_events, config.chaos, current_day)
            removed = before_count - len(day_events)
            stats["chaos_outage_events_removed"] += removed
            logger.warning(
                "Volume outage on %s: removed %d events (%.0f%% of day)",
                current_day.strftime("%Y-%m-%d"), removed,
                (removed / before_count * 100) if before_count else 0,
            )

        # ── Publish day's events ──
        if day_events:
            publisher.publish_batch(day_events, partition_date=current_day)
            stats["total_events"] += len(day_events)

        if day_offset % 7 == 0:
            active_count = len([p for p in players if not p.churned])
            logger.info(
                "Day %d/%d (%s): %d events, %d active players, patch %s",
                day_offset, config.num_days,
                current_day.strftime("%Y-%m-%d"),
                len(day_events), active_count, active_patch.version,
            )

    logger.info("Generation complete. Stats: %s", stats)
    return stats


def main():
    parser = argparse.ArgumentParser(description="DBD telemetry data generator")
    parser.add_argument("--players", type=int, default=50_000, help="Number of players")
    parser.add_argument("--days", type=int, default=90, help="Number of days to simulate")
    parser.add_argument("--start-date", type=str, default=None, help="Start date (YYYY-MM-DD). Defaults to today minus --days.")
    parser.add_argument("--target", choices=["local", "s3"], default="local", help="Output target")
    parser.add_argument("--bucket", type=str, default="dbd-telemetry-raw", help="S3 bucket name")
    parser.add_argument("--output-dir", type=str, default="./data/raw", help="Local output directory")
    parser.add_argument("--chaos-off", action="store_true", help="Disable chaos injection")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    random.seed(args.seed)

    if args.start_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        # Default: end today, start N days ago
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=args.days)
    chaos = ChaosConfig(enabled=not args.chaos_off)

    config = GeneratorConfig(
        num_players=args.players,
        start_date=start,
        end_date=start + timedelta(days=args.days),
        chaos=chaos,
    )

    if args.target == "s3":
        publisher = S3Publisher(bucket=args.bucket)
    else:
        publisher = LocalPublisher(output_dir=args.output_dir)

    stats = run_generation(config, publisher)
    print(f"\nGeneration complete: {stats['total_events']:,} total events")


if __name__ == "__main__":
    main()
