{{
    config(materialized='table')
}}

{#
    Player dimension — current state enriched with lifetime metrics.
    Could be extended to SCD Type 2 via snapshots.
#}

with players as (
    select * from {{ ref('stg_players') }}
),

lifetime as (
    select * from {{ ref('fct_player_lifetime') }}
),

mmr_latest as (
    select
        player_id,
        mmr_after as current_mmr,
        role      as last_role
    from {{ ref('stg_mmr_updates') }}
    qualify row_number() over (partition by player_id order by event_timestamp desc) = 1
)

select
    p.player_id,
    p.username,
    p.platform,
    p.region,
    p.registered_at,

    coalesce(m.current_mmr, 0)         as current_mmr,
    m.last_role,

    -- MMR segments
    case
        when coalesce(m.current_mmr, 0) < 500  then 'new'
        when m.current_mmr < 1000               then 'casual'
        when m.current_mmr < 1500               then 'core'
        else 'hardcore'
    end as mmr_segment,

    lt.lifetime_spend_usd,
    lt.lifetime_sessions,
    lt.total_matches,
    lt.churn_segment,
    lt.days_since_last_seen

from players p
left join lifetime lt on p.player_id = lt.player_id
left join mmr_latest m on p.player_id = m.player_id
