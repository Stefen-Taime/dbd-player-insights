{{
    config(
        materialized='table',
        cluster_by=['cohort_week']
    )
}}

{#
    Retention D1 / D7 / D30 by weekly cohort.
    A player is "retained at D-N" if they have at least one session
    exactly N days after their first seen date.
#}

with player_cohorts as (
    select
        player_id,
        first_seen_date                        as cohort_date,
        date_trunc('week', first_seen_date)    as cohort_week
    from {{ ref('int_player_first_last') }}
),

activity as (
    select distinct
        player_id,
        activity_date
    from {{ ref('int_player_daily_activity') }}
),

retention_calc as (
    select
        c.cohort_week,
        count(distinct c.player_id)                                             as cohort_size,
        count(distinct case when a1.player_id is not null then c.player_id end) as retained_d1,
        count(distinct case when a7.player_id is not null then c.player_id end) as retained_d7,
        count(distinct case when a30.player_id is not null then c.player_id end) as retained_d30
    from player_cohorts c
    left join activity a1
        on c.player_id = a1.player_id
        and a1.activity_date = dateadd(day, 1, c.cohort_date)
    left join activity a7
        on c.player_id = a7.player_id
        and a7.activity_date = dateadd(day, 7, c.cohort_date)
    left join activity a30
        on c.player_id = a30.player_id
        and a30.activity_date = dateadd(day, 30, c.cohort_date)
    group by 1
)

select
    cohort_week,
    cohort_size,
    retained_d1,
    retained_d7,
    retained_d30,
    round(retained_d1  / nullif(cohort_size, 0), 4) as retention_d1,
    round(retained_d7  / nullif(cohort_size, 0), 4) as retention_d7,
    round(retained_d30 / nullif(cohort_size, 0), 4) as retention_d30
from retention_calc
order by cohort_week
