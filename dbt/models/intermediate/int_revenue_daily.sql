{#
    Daily revenue aggregated by normalized item type and currency.
    Raw item_types (cosmetic_head, dlc_chapter, etc.) are mapped to
    broad categories used by the marts layer.
#}

with transactions as (
    select
        *,
        -- Normalize item_type to broad categories
        case
            when item_type like 'cosmetic%' then 'cosmetic'
            when item_type like 'dlc%'      then 'dlc'
            when item_type = 'rift_pass'    then 'rift_pass'
            when item_type like 'auric%'    then 'auric_cells'
            when item_type = 'bundle'       then 'cosmetic'
            when item_type = 'charm'        then 'cosmetic'
            else 'other'
        end as item_category
    from {{ ref('stg_store_transactions') }}
),

daily_revenue as (
    select
        event_timestamp::date   as revenue_date,
        item_category           as item_type,
        currency,

        count(*)                as transaction_count,
        count(distinct player_id) as unique_buyers,
        coalesce(sum(amount_usd), 0) as total_revenue_usd,
        avg(amount_usd)         as avg_transaction_usd,
        min(amount_usd)         as min_transaction_usd,
        max(amount_usd)         as max_transaction_usd

    from transactions
    group by 1, 2, 3
)

select * from daily_revenue
