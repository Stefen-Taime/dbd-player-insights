{{
    config(materialized='table')
}}

{#
    Win rate per perk — for both killer and survivor.
    "Win" for killer = 3+ kills; for survivor = escaped.
#}

with enriched as (
    select * from {{ ref('int_match_enriched') }}
),

-- Killer perks: flatten from stg_matches
killer_perks as (
    select
        m.match_id,
        m.killer_character_id,
        m.killer_kills,
        p.value::varchar as perk_id,
        'killer' as role
    from {{ ref('stg_matches') }} m,
    lateral flatten(input => m.killer_perks) p
),

killer_perk_stats as (
    select
        perk_id,
        role,
        count(*)                                    as times_used,
        avg(killer_kills)                           as avg_kills,
        count_if(killer_kills >= 3) / count(*)::float as win_rate
    from killer_perks
    group by 1, 2
),

-- Survivor perks: from enriched
survivor_perks as (
    select
        match_id,
        survivor_player_id,
        survivor_escaped,
        p.value::varchar as perk_id,
        'survivor' as role
    from enriched,
    lateral flatten(input => survivor_perks) p
),

survivor_perk_stats as (
    select
        perk_id,
        role,
        count(*)                                    as times_used,
        null::float                                 as avg_kills,
        count_if(survivor_escaped) / count(*)::float as win_rate
    from survivor_perks
    group by 1, 2
),

combined as (
    select * from killer_perk_stats
    union all
    select * from survivor_perk_stats
),

-- Join with seed perks for display info
final as (
    select
        c.*,
        pk.perk_name,
        pk.perk_type,
        pk.tier
    from combined c
    left join {{ ref('seed_perks') }} pk
        on c.perk_id = pk.perk_id
)

select * from final
order by role, win_rate desc
