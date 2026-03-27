{#
    First and last seen dates per player.
    Used for cohort assignment and churn detection.
#}

with sessions as (
    select * from {{ ref('stg_sessions') }}
),

players as (
    select * from {{ ref('stg_players') }}
),

session_bounds as (
    select
        player_id,
        min(event_timestamp::date) as first_session_date,
        max(event_timestamp::date) as last_session_date,
        count(distinct event_timestamp::date) as total_active_days
    from sessions
    group by 1
),

combined as (
    select
        p.player_id,
        p.platform,
        p.region,
        p.registered_at::date                                     as registration_date,
        coalesce(sb.first_session_date, p.registered_at::date)    as first_seen_date,
        sb.last_session_date                                      as last_seen_date,
        sb.total_active_days,
        datediff('day', sb.last_session_date, current_date())     as days_since_last_seen
    from players p
    left join session_bounds sb on p.player_id = sb.player_id
)

select * from combined
