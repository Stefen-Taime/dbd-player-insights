{{
    config(materialized='table')
}}

{#
    Store conversion funnel: session -> store visit -> purchase.
    Daily granularity.
#}

with daily_activity as (
    select * from {{ ref('int_player_daily_activity') }}
),

daily_purchases as (
    select
        event_timestamp::date as purchase_date,
        count(distinct player_id) as purchasers
    from {{ ref('stg_store_transactions') }}
    group by 1
),

funnel as (
    select
        da.activity_date                                    as metric_date,
        count(distinct da.player_id)                        as active_users,
        count(distinct case when da.store_visits > 0
                             then da.player_id end)         as store_visitors,
        coalesce(dp.purchasers, 0)                          as purchasers,

        -- Conversion rates
        round(
            count(distinct case when da.store_visits > 0 then da.player_id end)
            / nullif(count(distinct da.player_id), 0), 4
        ) as visit_rate,

        round(
            coalesce(dp.purchasers, 0)
            / nullif(count(distinct case when da.store_visits > 0 then da.player_id end), 0), 4
        ) as purchase_rate,

        round(
            coalesce(dp.purchasers, 0)
            / nullif(count(distinct da.player_id), 0), 4
        ) as overall_conversion_rate

    from daily_activity da
    left join daily_purchases dp on da.activity_date = dp.purchase_date
    group by 1, dp.purchasers
)

select * from funnel
order by metric_date
