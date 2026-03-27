{{
    config(materialized='table')
}}

{#
    MMR distribution histogram by player segment.
    Used for balance analysis and matchmaking quality assessment.
#}

with latest_mmr as (
    select
        player_id,
        mmr_after as current_mmr,
        role
    from {{ ref('stg_mmr_updates') }}
    qualify row_number() over (partition by player_id order by event_timestamp desc) = 1
),

bucketed as (
    select
        player_id,
        current_mmr,
        role,
        -- 100-point buckets
        floor(current_mmr / 100) * 100 as mmr_bucket,
        case
            when current_mmr < 500  then 'new'
            when current_mmr < 1000 then 'casual'
            when current_mmr < 1500 then 'core'
            else 'hardcore'
        end as mmr_segment
    from latest_mmr
),

distribution as (
    select
        mmr_segment,
        mmr_bucket,
        count(distinct player_id) as player_count,
        avg(current_mmr)          as avg_mmr
    from bucketed
    group by 1, 2
)

select
    mmr_segment,
    mmr_bucket,
    player_count,
    avg_mmr,
    sum(player_count) over (partition by mmr_segment order by mmr_bucket) as cumulative_players,
    round(player_count / nullif(sum(player_count) over (), 0), 4) as pct_of_total
from distribution
order by mmr_bucket
