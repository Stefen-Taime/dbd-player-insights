{{
    config(materialized='table')
}}

{#
    Kill rate and escape rate per killer character.
#}

with matches as (
    select * from {{ ref('stg_matches') }}
),

outcomes as (
    select
        killer_character_id,
        count(distinct match_id)                            as total_matches,
        avg(killer_kills)                                   as avg_kills,
        avg(killer_kills) / 4.0                             as kill_rate,
        1 - (avg(killer_kills) / 4.0)                       as escape_rate,
        avg(duration_seconds)                               as avg_match_duration_seconds,
        avg(killer_score)                                   as avg_killer_score,
        percentile_cont(0.5) within group (order by killer_kills) as median_kills
    from matches
    group by 1
),

enriched as (
    select
        o.*,
        k.killer_name,
        k.power as killer_power,
        k.chapter as killer_chapter
    from outcomes o
    left join {{ ref('seed_killers') }} k
        on o.killer_character_id = k.character_id
)

select * from enriched
order by kill_rate desc
