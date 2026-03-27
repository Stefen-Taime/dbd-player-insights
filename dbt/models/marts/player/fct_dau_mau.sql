{{
    config(
        materialized='incremental',
        unique_key='metric_date',
        incremental_strategy='merge'
    )
}}

{#
    DAU / WAU / MAU and stickiness ratio (DAU/MAU).
    One row per day.
#}

with daily_players as (
    select distinct
        activity_date,
        player_id
    from {{ ref('int_player_daily_activity') }}
    {% if is_incremental() %}
    where activity_date >= dateadd(day, -31, (select max(metric_date) from {{ this }}))
    {% endif %}
),

-- DAU: count distinct players per day
dau as (
    select
        activity_date as metric_date,
        count(distinct player_id) as dau
    from daily_players
    group by 1
),

-- WAU / MAU via cross-join on dates and range filtering
date_spine as (
    select distinct activity_date as metric_date
    from daily_players
),

wau as (
    select
        ds.metric_date,
        count(distinct dp.player_id) as wau
    from date_spine ds
    inner join daily_players dp
        on dp.activity_date between dateadd(day, -6, ds.metric_date) and ds.metric_date
    group by 1
),

mau as (
    select
        ds.metric_date,
        count(distinct dp.player_id) as mau
    from date_spine ds
    inner join daily_players dp
        on dp.activity_date between dateadd(day, -29, ds.metric_date) and ds.metric_date
    group by 1
)

select
    d.metric_date,
    d.dau,
    w.wau,
    m.mau,
    round(d.dau / nullif(m.mau, 0), 4) as stickiness_ratio
from dau d
left join wau w on w.metric_date = d.metric_date
left join mau m on m.metric_date = d.metric_date
order by d.metric_date
