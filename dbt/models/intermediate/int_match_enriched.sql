{#
    Enriches match data by flattening the survivors array and joining
    with seed tables for character and perk names.
#}

with matches as (
    select * from {{ ref('stg_matches') }}
),

-- Flatten survivors array: one row per survivor per match
survivors_flat as (
    select
        m.match_id,
        m.event_timestamp,
        m.map_id,
        m.game_mode,
        m.duration_seconds,
        m.killer_player_id,
        m.killer_character_id,
        m.killer_kills,
        m.killer_hooks,
        m.killer_score,
        s.value:player_id::varchar           as survivor_player_id,
        s.value:character_id::varchar        as survivor_character_id,
        s.value:escaped::boolean             as survivor_escaped,
        s.value:generators_completed::int    as generators_completed,
        s.value:score::int                   as survivor_score,
        s.value:perks::array                 as survivor_perks
    from matches m,
    lateral flatten(input => m.survivors) s
),

-- Join with seed killers for display name
enriched as (
    select
        sf.*,
        k.killer_name,
        k.power       as killer_power,
        sv.survivor_name,
        -- Derived metrics
        case when sf.killer_kills = 4 then true else false end as is_4k,
        case when sf.killer_kills = 0 then true else false end as is_0k
    from survivors_flat sf
    left join {{ ref('seed_killers') }} k
        on sf.killer_character_id = k.character_id
    left join {{ ref('seed_survivors') }} sv
        on sf.survivor_character_id = sv.character_id
)

select * from enriched
