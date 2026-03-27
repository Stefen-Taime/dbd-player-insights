"""
Configuration for the DBD telemetry data generator.

All chaos parameters are tunable — set CHAOS_ENABLED=False
to generate clean data for baseline testing.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta


# ─── Game constants ───────────────────────────────────────────

PLATFORMS = ["steam", "ps5", "ps4", "xbox_series", "xbox_one", "switch", "epic", "windows_store"]
REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-northeast-1", "ap-southeast-2", "sa-east-1"]
GAME_MODES = ["public", "ranked", "custom", "kill_your_friends", "ltm_lights_out", "ltm_2v8"]
# Modes excluded from analytics (custom + LTMs)
EXCLUDED_MODES = {"custom", "kill_your_friends", "ltm_lights_out", "ltm_2v8"}

CURRENCIES = ["auric_cells", "iridescent_shards", "usd", "eur", "cad", "gbp"]
STORE_ITEM_TYPES = ["cosmetic_head", "cosmetic_body", "cosmetic_weapon", "dlc_chapter", "dlc_killer",
                    "dlc_survivor", "rift_pass", "auric_cells_pack", "bundle", "charm"]

SESSION_ACTIONS = ["login", "logout", "queue_join", "queue_cancel", "match_start", "match_end",
                   "store_visit", "store_purchase", "loadout_change", "friend_invite",
                   "rift_claim", "bloodweb_spend", "settings_change"]

MMR_SEGMENTS = {"new": (0, 500), "casual": (500, 1000), "core": (1000, 1600), "hardcore": (1600, 2200)}


# ─── Chapter / patch timeline ────────────────────────────────
# Simulates ~6-8 week chapter releases with mid-chapter patches

@dataclass
class Patch:
    version: str
    release_date: datetime
    chapter: str | None = None
    added_fields: list[str] = field(default_factory=list)
    removed_fields: list[str] = field(default_factory=list)
    new_killer: str | None = None
    new_survivor: str | None = None
    new_map: str | None = None
    new_perks: list[str] = field(default_factory=list)

def _build_patch_timeline() -> list[Patch]:
    """Build patch timeline relative to today so it always covers the last 90 days."""
    from datetime import timedelta
    now = datetime.now()
    return [
        Patch("8.0.0", now - timedelta(days=85), chapter="Chapter 33 - Descent",
              new_killer="the_lich", new_survivor="elena_voss",
              new_map="catacomb_depths",
              new_perks=["hex_soul_siphon", "dark_pact", "resilient_spirit", "adrenaline_rush_v2"],
              added_fields=[]),
        Patch("8.0.1", now - timedelta(days=70), added_fields=[]),
        Patch("8.1.0", now - timedelta(days=55),
              added_fields=["anti_camp_score"],
              removed_fields=[]),
        Patch("8.2.0", now - timedelta(days=40), chapter="Chapter 34 - Shattered",
              new_killer="the_warden", new_survivor="kai_tanaka",
              new_map="prison_yard",
              new_perks=["iron_fortress", "lockdown", "escape_artist", "quick_reflexes"],
              added_fields=["boon_interaction_count", "pallet_stun_duration_ms"]),
        Patch("8.2.1", now - timedelta(days=25), added_fields=[]),
        Patch("8.3.0", now - timedelta(days=15),
              added_fields=["mmr_confidence_score"],
              removed_fields=["legacy_rank_pips"]),
        Patch("8.4.0", now - timedelta(days=5), chapter="Chapter 35 - Eclipse",
              new_killer="the_phantom", new_survivor="maya_chen",
              new_map="observatory_ruins",
              new_perks=["shadow_step_v2", "spectral_awareness", "night_vision", "sixth_sense"],
              added_fields=["generator_regression_events"]),
    ]

PATCH_TIMELINE = _build_patch_timeline()


# ─── Chaos configuration ─────────────────────────────────────

@dataclass
class ChaosConfig:
    """Controls the rate and type of data quality issues injected."""

    enabled: bool = True

    # Late-arriving events: % of events delayed by 1-48h
    late_event_rate: float = 0.05
    late_event_min_hours: int = 1
    late_event_max_hours: int = 48

    # Exact duplicates: same event_id, same payload
    exact_duplicate_rate: float = 0.03

    # Near-duplicates: same event_id, slightly different timestamp or field
    near_duplicate_rate: float = 0.01

    # Schema drift: new/removed fields based on patch timeline
    schema_drift_enabled: bool = True

    # Null injection: random nulls in non-critical fields
    null_field_rate: float = 0.02

    # Cross-platform identity: % of players with multiple platform accounts
    multi_platform_rate: float = 0.15
    # % of multi-platform players with mismatched display names
    display_name_mismatch_rate: float = 0.30

    # Out-of-order events: % of events with timestamp slightly before their logical predecessor
    out_of_order_rate: float = 0.02

    # Malformed JSON: % of events with an unexpected nested structure
    malformed_nested_rate: float = 0.005

    # Volume anomaly: simulate a 6h ingestion outage once per 30-day window
    volume_outage_enabled: bool = True
    volume_outage_duration_hours: int = 6


# ─── Generator parameters ────────────────────────────────────

@dataclass
class GeneratorConfig:
    """Main generation parameters."""

    # Player pool
    num_players: int = 50_000
    daily_active_pct: float = 0.12          # ~12% DAU/total
    new_player_daily_rate: float = 0.002    # 0.2% new registrations/day
    churn_probability_per_day: float = 0.003

    # Time range
    start_date: datetime = field(default_factory=lambda: datetime.now() - __import__("datetime").timedelta(days=90))
    end_date: datetime = field(default_factory=lambda: datetime.now())

    # Match parameters
    avg_matches_per_session: float = 3.2
    avg_session_duration_minutes: float = 95
    match_duration_range: tuple[int, int] = (180, 900)  # 3-15 min

    # Monetization
    paying_player_pct: float = 0.08         # 8% conversion rate
    avg_monthly_spend_usd: float = 12.50
    whale_pct: float = 0.005               # 0.5% spend 10x average

    # Progression
    avg_bloodpoints_per_match: int = 18_000
    rift_fragment_per_match_range: tuple[int, int] = (1, 5)

    # Output
    output_format: str = "json"             # json | parquet
    partition_by: str = "event_type/yyyy/mm/dd/hh"
    batch_size: int = 10_000

    # Chaos
    chaos: ChaosConfig = field(default_factory=ChaosConfig)

    @property
    def num_days(self) -> int:
        return (self.end_date - self.start_date).days

    def get_active_patch(self, event_time: datetime) -> Patch:
        """Return the patch version active at a given timestamp."""
        active = PATCH_TIMELINE[0]
        for patch in PATCH_TIMELINE:
            if event_time >= patch.release_date:
                active = patch
        return active

    def get_available_fields(self, event_time: datetime) -> tuple[set[str], set[str]]:
        """Return (added_fields, removed_fields) cumulative up to event_time."""
        added = set()
        removed = set()
        for patch in PATCH_TIMELINE:
            if event_time >= patch.release_date:
                added.update(patch.added_fields)
                removed.update(patch.removed_fields)
        return added, removed
