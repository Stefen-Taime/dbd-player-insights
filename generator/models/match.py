"""
Match telemetry model — the most complex event type.

Simulates real DBD match data challenges:
- Nested arrays: survivors[4] each with perks[4], items, add_ons[2]
- Killer with perks[4], add_ons[2], offering
- Schema drift: new fields appear mid-chapter (anti_camp_score, etc.)
- Mode exclusions: custom/LTM matches tagged but should be filtered
- Game balance metrics: hooks, chases, gens, pallet stuns, etc.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from generator.config import GAME_MODES, GeneratorConfig, Patch

# ─── Reference data (loaded from seeds in production, hardcoded for generator) ─

KILLERS_BASE = [
    "trapper", "wraith", "hillbilly", "nurse", "shape", "hag", "doctor",
    "huntress", "cannibal", "nightmare", "pig", "clown", "spirit", "legion",
    "plague", "ghostface", "demogorgon", "oni", "deathslinger", "pyramid_head",
    "blight", "twins", "trickster", "nemesis", "cenobite", "artist",
    "onryo", "dredge", "wesker", "knight", "skull_merchant", "singularity",
    "xenomorph", "good_guy", "unknown", "lich", "vecna", "dracula",
]

SURVIVORS_BASE = [
    "dwight", "meg", "claudette", "jake", "nea", "laurie", "ace", "bill",
    "feng", "david", "quentin", "tapp", "kate", "adam", "jeff", "jane",
    "ash", "nancy", "steve", "yui", "zarina", "cheryl", "felix", "elodie",
    "yun_jin", "jill", "leon", "mikaela", "jonah", "yoichi", "haddie",
    "ada", "rebecca", "vittorio", "thalita", "renato", "gabriel", "nicolas",
    "ellen", "alan", "sable", "aestri", "lara",
]

KILLER_PERKS = [
    "hex_ruin", "bbq_and_chilli", "pop_goes_the_weasel", "corrupt_intervention",
    "noed", "bamboozle", "enduring", "spirit_fury", "infectious_fright",
    "thrilling_tremors", "surge", "undying", "tinkerer", "lethal_pursuer",
    "call_of_brine", "eruption", "nowhere_to_hide", "ultimate_weapon",
    "grim_embrace", "dead_man_switch", "pain_resonance", "hex_pentimento",
    "hex_plaything", "scourge_hook_floods", "hex_face_the_darkness",
    "friends_til_the_end", "gearhead", "im_all_ears", "monitor_and_abuse",
]

SURVIVOR_PERKS = [
    "sprint_burst", "adrenaline", "iron_will", "borrowed_time",
    "dead_hard", "decisive_strike", "unbreakable", "windows_of_opportunity",
    "lithe", "prove_thyself", "bond", "kindred", "spine_chill",
    "resilience", "off_the_record", "reassurance", "wiretap",
    "background_player", "made_for_this", "hope", "deliverance",
    "for_the_people", "circle_of_healing", "boon_exponential",
    "boon_shadow_step", "overcome", "lucky_break", "inner_healing",
    "bite_the_bullet", "wicked",
]

ITEMS = ["medkit_green", "medkit_purple", "toolbox_yellow", "toolbox_green",
         "flashlight_yellow", "flashlight_green", "key_purple", "key_pink",
         "map_green", "map_purple", "none"]

ADDONS = ["addon_common_1", "addon_common_2", "addon_uncommon_1", "addon_uncommon_2",
          "addon_rare_1", "addon_rare_2", "addon_very_rare_1", "addon_very_rare_2",
          "addon_ultra_rare_1", "addon_ultra_rare_2", "none"]

OFFERINGS = ["bloody_party_streamers", "bound_envelope", "escape_cake",
             "gruesome_gateau", "survivor_pudding", "ward_offering",
             "map_offering_macmillan", "map_offering_autohaven", "map_offering_coldwind",
             "map_offering_crotus", "none"]

MAPS = [
    "macmillan_coal_tower", "macmillan_suffocation_pit", "macmillan_shelter_woods",
    "autohaven_blood_lodge", "autohaven_gas_heaven", "autohaven_wreckers_yard",
    "coldwind_fractured_cowshed", "coldwind_rancid_abattoir", "coldwind_thompson_house",
    "crotus_disturbed_ward", "crotus_fathers_chapel",
    "haddonfield_lampkin_lane", "backwater_pale_rose", "backwater_grim_pantry",
    "lery_memorial", "red_forest_mothers_dwelling", "red_forest_temple",
    "springwood_badham_1", "gideon_the_game", "ormond_mount_ormond",
    "hawkins_underground", "grave_of_glenvale", "raccoon_city_east",
    "raccoon_city_west", "eyrie_of_crows", "garden_of_joy",
    "shattered_square", "toba_landing", "greenville_square",
    "nostromo_wreckage", "forgotten_ruins",
]


def _pick_loadout(perks_pool: list[str], num_perks: int = 4) -> list[str]:
    """Pick N unique perks from the pool."""
    return random.sample(perks_pool, min(num_perks, len(perks_pool)))


def _pick_addons(n: int = 2) -> list[str]:
    return random.sample(ADDONS, n)


def generate_match_event(
    killer_player,
    survivor_players: list,
    event_time: datetime,
    config: GeneratorConfig,
    active_patch: Patch,
) -> dict:
    """Generate a complete match_completed event with full nested loadouts."""

    match_id = str(uuid.uuid4())
    game_mode = random.choices(
        GAME_MODES,
        weights=[0.65, 0.15, 0.08, 0.05, 0.04, 0.03],
    )[0]

    # Determine available killers/survivors/maps (patch-dependent)
    available_killers = KILLERS_BASE[:]
    available_survivors = SURVIVORS_BASE[:]
    available_maps = MAPS[:]
    for patch in __import__("generator.config", fromlist=["PATCH_TIMELINE"]).PATCH_TIMELINE:
        if event_time >= patch.release_date:
            if patch.new_killer:
                available_killers.append(patch.new_killer)
            if patch.new_survivor:
                available_survivors.append(patch.new_survivor)
            if patch.new_map:
                available_maps.append(patch.new_map)

    # Match duration (seconds)
    duration = random.randint(*config.match_duration_range)

    # Killer loadout
    killer_char = random.choice(available_killers)
    killer_kills = random.choices([0, 1, 2, 3, 4], weights=[0.10, 0.15, 0.30, 0.25, 0.20])[0]
    killer_hooks = min(12, killer_kills * 3 + random.randint(0, 3))

    # Available perks may include patch-specific ones
    available_killer_perks = KILLER_PERKS[:]
    available_survivor_perks = SURVIVOR_PERKS[:]
    for patch in __import__("generator.config", fromlist=["PATCH_TIMELINE"]).PATCH_TIMELINE:
        if event_time >= patch.release_date:
            for perk in patch.new_perks:
                if "hex_" in perk or "lockdown" in perk or "iron_fortress" in perk:
                    available_killer_perks.append(perk)
                else:
                    available_survivor_perks.append(perk)

    killer_data = {
        "player_id": killer_player.bhvr_id,
        "platform_player_id": killer_player.platform_accounts[0].platform_player_id if killer_player.platform_accounts else None,
        "platform": killer_player.primary_platform,
        "character_id": killer_char,
        "perks": _pick_loadout(available_killer_perks),
        "add_ons": _pick_addons(),
        "offering": random.choice(OFFERINGS),
        "kills": killer_kills,
        "hooks": killer_hooks,
        "chases_initiated": random.randint(4, 20),
        "chases_won": random.randint(2, 15),
        "pallets_broken": random.randint(0, 8),
        "generators_damaged": random.randint(0, 5),
        "score": random.randint(12000, 32000),
        "mmr_before": killer_player.mmr_killer,
    }

    # Survivors loadout
    survivors_data = []
    gens_completed_total = random.randint(0, 5)
    for i, surv_player in enumerate(survivor_players[:4]):
        escaped = random.random() < (1 - killer_kills / 4) if killer_kills < 4 else False
        surv_char = random.choice(available_survivors)

        surv = {
            "player_id": surv_player.bhvr_id,
            "platform_player_id": surv_player.platform_accounts[0].platform_player_id if surv_player.platform_accounts else None,
            "platform": surv_player.primary_platform,
            "character_id": surv_char,
            "perks": _pick_loadout(available_survivor_perks),
            "item": random.choice(ITEMS),
            "add_ons": _pick_addons(),
            "offering": random.choice(OFFERINGS),
            "escaped": escaped,
            "generators_completed": random.randint(0, min(gens_completed_total, 3)),
            "totems_cleansed": random.randint(0, 3),
            "unhooks": random.randint(0, 4),
            "heals": random.randint(0, 5),
            "chased_duration_seconds": random.randint(10, 120),
            "score": random.randint(8000, 28000),
            "mmr_before": surv_player.mmr_survivor,
        }
        survivors_data.append(surv)

    # Base event
    event = {
        "event_type": "match_completed",
        "event_id": str(uuid.uuid4()),
        "timestamp": event_time.isoformat() + "Z",
        "match_id": match_id,
        "duration_seconds": duration,
        "map_id": random.choice(available_maps),
        "game_mode": game_mode,
        "client_version": active_patch.version,
        "server_region": random.choice(
            __import__("generator.config", fromlist=["REGIONS"]).REGIONS
        ),
        "killer": killer_data,
        "survivors": survivors_data,
        "generators_completed": gens_completed_total,
        "exit_gates_opened": 1 if gens_completed_total == 5 else 0,
        "hatch_opened": random.random() < 0.15 if killer_kills >= 3 else False,
    }

    # ── Schema drift: conditionally add fields based on patch ──
    added_fields, removed_fields = config.get_available_fields(event_time)

    if "anti_camp_score" in added_fields:
        event["anti_camp_score"] = random.randint(0, 100)

    if "boon_interaction_count" in added_fields:
        event["boon_interaction_count"] = random.randint(0, 6)

    if "pallet_stun_duration_ms" in added_fields:
        event["pallet_stun_duration_ms"] = random.randint(1500, 3000)

    if "generator_regression_events" in added_fields:
        event["generator_regression_events"] = random.randint(0, 12)

    # Remove deprecated fields
    for f in removed_fields:
        event.pop(f, None)

    return event
