"""
Session, store, progression, and MMR event generators.

Each module produces events that map to real DBD telemetry streams.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from generator.config import (
    CURRENCIES,
    REGIONS,
    SESSION_ACTIONS,
    STORE_ITEM_TYPES,
    GeneratorConfig,
    Patch,
)


# ─── Session events ──────────────────────────────────────────

def generate_session_events(
    player,
    session_start: datetime,
    config: GeneratorConfig,
    active_patch: Patch,
) -> list[dict]:
    """Generate a sequence of session events for a single play session."""
    events = []
    session_id = str(uuid.uuid4())
    current_time = session_start

    # Platform can vary if player has multiple accounts (cross-play scenario)
    platform = player.primary_platform
    if player.platform_accounts and random.random() < 0.1:
        account = random.choice(player.platform_accounts)
        platform = account.platform

    # Login
    events.append(_session_event(
        player, session_id, "login", current_time, platform, active_patch,
    ))

    # Session activity: sequence of actions
    session_minutes = int(random.expovariate(1 / config.avg_session_duration_minutes))
    session_minutes = max(5, min(360, session_minutes))

    num_matches = max(1, int(random.gauss(config.avg_matches_per_session, 1.2)))
    match_gap_minutes = session_minutes / (num_matches + 2)

    for m in range(num_matches):
        # Queue join
        current_time += timedelta(minutes=random.uniform(1, match_gap_minutes))
        events.append(_session_event(
            player, session_id, "queue_join", current_time, platform, active_patch,
        ))

        # Match start
        queue_time_seconds = random.expovariate(1 / 45)  # Avg 45s queue
        current_time += timedelta(seconds=queue_time_seconds)
        events.append(_session_event(
            player, session_id, "match_start", current_time, platform, active_patch,
        ))

        # Match end
        match_duration = random.randint(180, 900)
        current_time += timedelta(seconds=match_duration)
        events.append(_session_event(
            player, session_id, "match_end", current_time, platform, active_patch,
        ))

    # Random mid-session activities
    if random.random() < 0.25:
        current_time += timedelta(minutes=random.uniform(1, 5))
        events.append(_session_event(
            player, session_id, "store_visit", current_time, platform, active_patch,
        ))

    if random.random() < 0.40:
        current_time += timedelta(minutes=random.uniform(0.5, 3))
        events.append(_session_event(
            player, session_id, "bloodweb_spend", current_time, platform, active_patch,
        ))

    if random.random() < 0.15:
        current_time += timedelta(minutes=random.uniform(0.5, 2))
        events.append(_session_event(
            player, session_id, "loadout_change", current_time, platform, active_patch,
        ))

    # Logout
    current_time += timedelta(minutes=random.uniform(0.5, 5))
    events.append(_session_event(
        player, session_id, "logout", current_time, platform, active_patch,
    ))

    return events


def _session_event(
    player, session_id: str, action: str, ts: datetime,
    platform: str, patch: Patch,
) -> dict:
    return {
        "event_type": "session_event",
        "event_id": str(uuid.uuid4()),
        "timestamp": ts.isoformat() + "Z",
        "bhvr_id": player.bhvr_id,
        "player_id": player.platform_accounts[0].platform_player_id
            if player.platform_accounts else player.bhvr_id,
        "session_id": session_id,
        "action": action,
        "platform": platform,
        "region": player.region,
        "client_version": patch.version,
    }


# ─── Store transactions ──────────────────────────────────────

def generate_store_transaction(
    player,
    event_time: datetime,
    config: GeneratorConfig,
    active_patch: Patch,
) -> dict:
    """Generate a store purchase event."""
    item_type = random.choices(
        STORE_ITEM_TYPES,
        weights=[0.20, 0.15, 0.10, 0.12, 0.08, 0.08, 0.10, 0.05, 0.07, 0.05],
    )[0]

    # Price logic based on item type
    price_ranges = {
        "cosmetic_head": (400, 1080),
        "cosmetic_body": (400, 1080),
        "cosmetic_weapon": (200, 540),
        "dlc_chapter": (500, 500),
        "dlc_killer": (500, 500),
        "dlc_survivor": (500, 500),
        "rift_pass": (1000, 1000),
        "auric_cells_pack": (500, 6000),
        "bundle": (1500, 3500),
        "charm": (100, 300),
    }
    lo, hi = price_ranges.get(item_type, (100, 1000))
    auric_amount = random.randint(lo, hi)

    # USD equivalent
    usd_per_cell = 0.01  # ~$1 per 100 Auric Cells
    amount_usd = round(auric_amount * usd_per_cell, 2)

    # Whale multiplier
    if player.is_whale:
        auric_amount = int(auric_amount * random.uniform(2.0, 5.0))
        amount_usd = round(auric_amount * usd_per_cell, 2)

    # Currency: most purchases are Auric Cells, some are Iridescent Shards
    currency = "auric_cells" if random.random() < 0.70 else "iridescent_shards"
    if item_type == "auric_cells_pack":
        currency = random.choice(["usd", "eur", "cad", "gbp"])

    # Promotional context
    is_promo = random.random() < 0.15
    promo_discount_pct = random.choice([10, 15, 20, 25, 30, 50]) if is_promo else 0

    return {
        "event_type": "store_transaction",
        "event_id": str(uuid.uuid4()),
        "timestamp": event_time.isoformat() + "Z",
        "bhvr_id": player.bhvr_id,
        "player_id": player.platform_accounts[0].platform_player_id
            if player.platform_accounts else player.bhvr_id,
        "transaction_id": str(uuid.uuid4()),
        "item_id": f"{item_type}_{uuid.uuid4().hex[:8]}",
        "item_type": item_type,
        "currency": currency,
        "amount": auric_amount,
        "amount_usd": amount_usd,
        "platform": player.primary_platform,
        "client_version": active_patch.version,
        "is_promotional": is_promo,
        "promo_discount_pct": promo_discount_pct,
    }


# ─── Progression events ──────────────────────────────────────

def generate_progression_event(
    player,
    event_time: datetime,
    bloodpoints_earned: int,
    config: GeneratorConfig,
    active_patch: Patch,
) -> dict:
    """Generate a progression event after a match."""
    rift_fragments = random.randint(*config.rift_fragment_per_match_range)

    return {
        "event_type": "progression_event",
        "event_id": str(uuid.uuid4()),
        "timestamp": event_time.isoformat() + "Z",
        "bhvr_id": player.bhvr_id,
        "player_id": player.platform_accounts[0].platform_player_id
            if player.platform_accounts else player.bhvr_id,
        "bloodpoints_earned": bloodpoints_earned,
        "bloodpoints_spent": random.randint(0, bloodpoints_earned) if random.random() < 0.6 else 0,
        "rift_fragments_earned": rift_fragments,
        "rift_tier_current": random.randint(1, 70),
        "prestige_level": random.randint(0, 100),
        "character_id": None,  # Filled by match context
        "perk_unlocked": random.choice([None, None, None, "random_perk_name"]),
        "platform": player.primary_platform,
        "client_version": active_patch.version,
    }


# ─── MMR updates ─────────────────────────────────────────────

def generate_mmr_update(
    player,
    event_time: datetime,
    role: str,  # "killer" or "survivor"
    match_result: str,  # "win", "loss", "draw"
    config: GeneratorConfig,
    active_patch: Patch,
) -> dict:
    """Generate an MMR update event post-match."""
    mmr_before = player.mmr_killer if role == "killer" else player.mmr_survivor

    # MMR delta based on result
    if match_result == "win":
        delta = random.randint(10, 40)
    elif match_result == "loss":
        delta = -random.randint(10, 35)
    else:
        delta = random.randint(-5, 5)

    mmr_after = max(0, min(2200, mmr_before + delta))

    # Update player state
    if role == "killer":
        player.mmr_killer = mmr_after
    else:
        player.mmr_survivor = mmr_after

    event = {
        "event_type": "mmr_update",
        "event_id": str(uuid.uuid4()),
        "timestamp": event_time.isoformat() + "Z",
        "bhvr_id": player.bhvr_id,
        "player_id": player.platform_accounts[0].platform_player_id
            if player.platform_accounts else player.bhvr_id,
        "role": role,
        "mmr_before": mmr_before,
        "mmr_after": mmr_after,
        "mmr_delta": delta,
        "match_result": match_result,
        "platform": player.primary_platform,
        "client_version": active_patch.version,
    }

    # Schema drift: mmr_confidence_score added in patch 8.3.0
    added_fields, _ = config.get_available_fields(event_time)
    if "mmr_confidence_score" in added_fields:
        event["mmr_confidence_score"] = round(random.uniform(0.3, 0.99), 3)

    return event
