{{
    config(
        materialized='incremental',
        unique_key='revenue_date',
        incremental_strategy='merge'
    )
}}

{#
    Daily revenue aggregated from intermediate model.
#}

with daily as (
    select * from {{ ref('int_revenue_daily') }}
    {% if is_incremental() %}
    where revenue_date >= dateadd(day, -{{ var('incremental_lookback_days', 3) }}, (select max(revenue_date) from {{ this }}))
    {% endif %}
),

pivoted as (
    select
        revenue_date,
        sum(total_revenue_usd)                                              as total_revenue_usd,
        sum(transaction_count)                                              as total_transactions,
        sum(unique_buyers)                                                  as total_unique_buyers,
        sum(case when item_type = 'cosmetic'    then total_revenue_usd else 0 end) as cosmetic_revenue_usd,
        sum(case when item_type = 'dlc'         then total_revenue_usd else 0 end) as dlc_revenue_usd,
        sum(case when item_type = 'rift_pass'   then total_revenue_usd else 0 end) as rift_pass_revenue_usd,
        sum(case when item_type = 'auric_cells' then total_revenue_usd else 0 end) as auric_cells_revenue_usd
    from daily
    group by 1
)

select
    revenue_date,
    total_revenue_usd,
    total_transactions,
    total_unique_buyers,
    cosmetic_revenue_usd,
    dlc_revenue_usd,
    rift_pass_revenue_usd,
    auric_cells_revenue_usd,
    -- 7-day rolling average
    avg(total_revenue_usd) over (order by revenue_date rows between 6 preceding and current row) as revenue_7d_avg
from pivoted
order by revenue_date
