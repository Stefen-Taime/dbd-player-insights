{{
    config(materialized='table')
}}

{#
    Kill rate per map.
    Maps with kill_rate < 0.50 are considered survivor-sided.
    Maps with kill_rate > 0.60 are considered killer-sided.
#}

with matches as (
    select * from {{ ref('stg_matches') }}
),

map_stats as (
    select
        map_id,
        count(distinct match_id)                    as total_matches,
        avg(killer_kills)                           as avg_kills,
        avg(killer_kills) / 4.0                     as kill_rate,
        avg(duration_seconds)                       as avg_duration_seconds,
        stddev(killer_kills)                        as stddev_kills
    from matches
    group by 1
),

enriched as (
    select
        ms.*,
        mp.map_name,
        mp.realm,
        mp.map_size,
        case
            when ms.kill_rate < 0.40 then 'strongly_survivor_sided'
            when ms.kill_rate < 0.50 then 'survivor_sided'
            when ms.kill_rate <= 0.60 then 'balanced'
            when ms.kill_rate <= 0.70 then 'killer_sided'
            else 'strongly_killer_sided'
        end as balance_rating
    from map_stats ms
    left join {{ ref('seed_maps') }} mp
        on ms.map_id = mp.map_id
)

select * from enriched
order by kill_rate desc
