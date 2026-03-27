{{
    config(materialized='table')
}}

{#
    Player lifetime value: total spend, session count, churn risk score.
#}

with player_info as (
    select * from {{ ref('int_player_first_last') }}
),

spending as (
    select
        player_id,
        sum(amount_usd)          as total_spend_usd,
        count(*)                 as total_transactions
    from {{ ref('stg_store_transactions') }}
    group by 1
),

session_stats as (
    select
        player_id,
        count(distinct session_id)  as total_sessions,
        avg(session_duration_seconds) as avg_session_duration_seconds
    from {{ ref('int_session_metrics') }}
    group by 1
),

match_stats as (
    select
        survivor_player_id as player_id,
        count(*)           as total_matches_survivor,
        avg(survivor_score) as avg_score_survivor
    from {{ ref('int_match_enriched') }}
    group by 1
),

combined as (
    select
        pi.player_id,
        pi.platform,
        pi.region,
        pi.registration_date,
        pi.first_seen_date,
        pi.last_seen_date,
        pi.total_active_days,
        pi.days_since_last_seen,

        coalesce(sp.total_spend_usd, 0)                 as lifetime_spend_usd,
        coalesce(sp.total_transactions, 0)               as lifetime_transactions,
        coalesce(ss.total_sessions, 0)                   as lifetime_sessions,
        coalesce(ss.avg_session_duration_seconds, 0)     as avg_session_duration_seconds,
        coalesce(ms.total_matches_survivor, 0)           as total_matches,

        -- Churn risk: simple heuristic based on recency
        case
            when pi.days_since_last_seen <= 7  then 'active'
            when pi.days_since_last_seen <= 14 then 'at_risk'
            when pi.days_since_last_seen <= 30 then 'dormant'
            else 'churned'
        end as churn_segment

    from player_info pi
    left join spending sp on pi.player_id = sp.player_id
    left join session_stats ss on pi.player_id = ss.player_id
    left join match_stats ms on pi.player_id = ms.player_id
)

select * from combined
