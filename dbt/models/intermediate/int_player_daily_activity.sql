{#
    Aggregates daily activity per player from session events.
    Used downstream for DAU/MAU and retention calculations.
#}

with sessions as (
    select * from {{ ref('stg_sessions') }}
),

daily_activity as (
    select
        player_id,
        event_timestamp::date   as activity_date,
        platform,
        region,

        count(*)                                                as total_events,
        count_if(action = 'login')                              as login_count,
        count_if(action = 'match_start')                        as matches_started,
        count_if(action = 'match_end')                          as matches_ended,
        count_if(action = 'store_visit')                        as store_visits,
        min(event_timestamp)                                    as first_event_at,
        max(event_timestamp)                                    as last_event_at,
        datediff('minute', min(event_timestamp), max(event_timestamp)) as active_minutes

    from sessions
    group by 1, 2, 3, 4
)

select * from daily_activity
