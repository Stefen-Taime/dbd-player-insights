{{
    config(materialized='table')
}}

{#
    Average Revenue Per Daily Active User.
    Combines DAU metrics with daily revenue.
#}

with dau as (
    select
        metric_date,
        dau,
        mau
    from {{ ref('fct_dau_mau') }}
),

revenue as (
    select
        revenue_date,
        total_revenue_usd,
        total_unique_buyers
    from {{ ref('fct_daily_revenue') }}
),

combined as (
    select
        d.metric_date,
        d.dau,
        d.mau,
        coalesce(r.total_revenue_usd, 0)    as daily_revenue_usd,
        coalesce(r.total_unique_buyers, 0)   as paying_users,

        -- ARPDAU = revenue / DAU (0 if no DAU)
        coalesce(round(coalesce(r.total_revenue_usd, 0) / nullif(d.dau, 0), 4), 0) as arpdau,

        -- ARPPU = revenue / paying users (0 if no paying users)
        coalesce(round(coalesce(r.total_revenue_usd, 0) / nullif(r.total_unique_buyers, 0), 2), 0) as arppu,

        -- Conversion rate = paying users / DAU (0 if no DAU)
        coalesce(round(coalesce(r.total_unique_buyers, 0) / nullif(d.dau, 0), 4), 0) as payer_conversion_rate

    from dau d
    left join revenue r on d.metric_date = r.revenue_date
)

select * from combined
order by metric_date
