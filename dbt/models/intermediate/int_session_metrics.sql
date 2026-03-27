{#
    Session-level metrics computed from login/logout pairs.
#}

with sessions as (
    select * from {{ ref('stg_sessions') }}
),

logins as (
    select
        player_id,
        session_id,
        platform,
        region,
        client_version,
        event_timestamp as login_at
    from sessions
    where action = 'login'
),

logouts as (
    select
        session_id,
        event_timestamp as logout_at
    from sessions
    where action = 'logout'
),

session_events as (
    select
        session_id,
        count(*) as event_count
    from sessions
    group by 1
),

session_metrics as (
    select
        l.player_id,
        l.session_id,
        l.platform,
        l.region,
        l.client_version,
        l.login_at,
        o.logout_at,
        datediff('second', l.login_at, coalesce(o.logout_at, l.login_at)) as session_duration_seconds,
        e.event_count,
        case
            when datediff('minute', l.login_at, coalesce(o.logout_at, l.login_at)) > 0
            then round(e.event_count / datediff('minute', l.login_at, coalesce(o.logout_at, l.login_at)), 2)
            else 0
        end as actions_per_minute
    from logins l
    left join logouts o on l.session_id = o.session_id
    left join session_events e on l.session_id = e.session_id
)

select * from session_metrics
