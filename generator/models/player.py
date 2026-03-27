"""
Player identity model with cross-platform account linking.

Simulates the real DBD identity challenge:
- 1 Behaviour account (bhvr_id) = canonical identity
- N platform accounts (Steam, PSN, Xbox, etc.)
- Some players link accounts (cross-progression)
- Some have display name mismatches across platforms
- Progression sharing varies by currency type
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from faker import Faker

from generator.config import (
    ChaosConfig,
    MMR_SEGMENTS,
    PLATFORMS,
    REGIONS,
    GeneratorConfig,
)

fake = Faker()
Faker.seed(42)


@dataclass
class PlatformAccount:
    platform: str
    platform_player_id: str
    display_name: str
    linked_at: datetime | None = None  # None = not linked to BHVR account
    is_primary: bool = False


@dataclass
class Player:
    bhvr_id: str
    display_name: str
    registration_date: datetime
    primary_platform: str
    region: str
    mmr_killer: int
    mmr_survivor: int
    segment: str
    is_paying: bool
    is_whale: bool
    platform_accounts: list[PlatformAccount] = field(default_factory=list)
    churned: bool = False
    churn_date: datetime | None = None
    last_active: datetime | None = None

    @property
    def canonical_id(self) -> str:
        """The bhvr_id is always the canonical identity key."""
        return self.bhvr_id

    @property
    def all_platform_ids(self) -> dict[str, str]:
        """Map of platform → platform_player_id for identity resolution."""
        return {a.platform: a.platform_player_id for a in self.platform_accounts}

    def to_registration_event(self) -> dict:
        return {
            "event_type": "player_registration",
            "event_id": str(uuid.uuid4()),
            "timestamp": self.registration_date.isoformat() + "Z",
            "bhvr_id": self.bhvr_id,
            "display_name": self.display_name,
            "primary_platform": self.primary_platform,
            "region": self.region,
            "platform_accounts": [
                {
                    "platform": a.platform,
                    "platform_player_id": a.platform_player_id,
                    "display_name": a.display_name,
                    "linked_at": a.linked_at.isoformat() + "Z" if a.linked_at else None,
                    "is_primary": a.is_primary,
                }
                for a in self.platform_accounts
            ],
            "initial_mmr_killer": self.mmr_killer,
            "initial_mmr_survivor": self.mmr_survivor,
        }


def _assign_segment(mmr: int) -> str:
    for seg, (lo, hi) in MMR_SEGMENTS.items():
        if lo <= mmr < hi:
            return seg
    return "hardcore"


def _generate_platform_accounts(
    player_name: str,
    primary_platform: str,
    reg_date: datetime,
    chaos: ChaosConfig,
) -> list[PlatformAccount]:
    """Generate platform accounts, potentially with cross-platform linking."""
    accounts = []

    # Primary account always exists
    accounts.append(PlatformAccount(
        platform=primary_platform,
        platform_player_id=str(uuid.uuid4()),
        display_name=player_name,
        linked_at=reg_date,
        is_primary=True,
    ))

    # Multi-platform: some players have additional platform accounts
    if chaos.enabled and random.random() < chaos.multi_platform_rate:
        num_extra = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
        other_platforms = [p for p in PLATFORMS if p != primary_platform]
        extra_platforms = random.sample(other_platforms, min(num_extra, len(other_platforms)))

        for platform in extra_platforms:
            # Display name mismatch: some players use different names per platform
            if random.random() < chaos.display_name_mismatch_rate:
                alt_name = fake.user_name() + str(random.randint(1, 999))
            else:
                alt_name = player_name

            link_delay_days = random.randint(0, 180)
            accounts.append(PlatformAccount(
                platform=platform,
                platform_player_id=str(uuid.uuid4()),
                display_name=alt_name,
                linked_at=reg_date + __import__("datetime").timedelta(days=link_delay_days),
                is_primary=False,
            ))

    return accounts


def generate_player_pool(config: GeneratorConfig) -> list[Player]:
    """Generate the initial player pool with realistic distributions."""
    players = []

    for i in range(config.num_players):
        # Registration date: spread across the time range with front-loading
        days_offset = int(random.betavariate(2, 5) * config.num_days)
        reg_date = config.start_date + __import__("datetime").timedelta(days=days_offset)

        # MMR follows a normal distribution centered around 1100
        mmr_killer = max(0, min(2200, int(random.gauss(1100, 350))))
        mmr_survivor = max(0, min(2200, int(random.gauss(1050, 380))))

        primary_platform = random.choices(
            PLATFORMS,
            weights=[0.35, 0.18, 0.05, 0.15, 0.04, 0.08, 0.10, 0.05],  # Steam dominant
        )[0]

        display_name = fake.user_name() + str(random.randint(1, 9999))

        # Paying player determination
        is_paying = random.random() < config.paying_player_pct
        is_whale = is_paying and random.random() < (config.whale_pct / config.paying_player_pct)

        player = Player(
            bhvr_id=f"bhvr_{uuid.uuid4().hex[:16]}",
            display_name=display_name,
            registration_date=reg_date,
            primary_platform=primary_platform,
            region=random.choice(REGIONS),
            mmr_killer=mmr_killer,
            mmr_survivor=mmr_survivor,
            segment=_assign_segment(mmr_killer),
            is_paying=is_paying,
            is_whale=is_whale,
        )

        player.platform_accounts = _generate_platform_accounts(
            display_name, primary_platform, reg_date, config.chaos,
        )

        players.append(player)

    return players
