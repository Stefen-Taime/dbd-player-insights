{{
    config(
        materialized='incremental',
        unique_key='event_id',
        incremental_strategy='merge',
        cluster_by=['event_timestamp::date']
    )
}}

with source as (
    select
        raw_data,
        filename,
        load_ts
    from {{ source('raw_dbd', 'raw_store_transaction') }}
    {{ incremental_filter('load_ts') }}
),

parsed as (
    select
        raw_data:event_id::varchar              as event_id,
        raw_data:timestamp::timestamp_ntz       as event_timestamp,
        raw_data:player_id::varchar             as player_id,
        raw_data:transaction_id::varchar        as transaction_id,
        raw_data:item_id::varchar               as item_id,
        raw_data:item_type::varchar             as item_type,
        raw_data:currency::varchar              as currency,
        raw_data:amount::int                    as amount,
        raw_data:amount_usd::number(10,2)       as amount_usd,
        filename,
        load_ts
    from source
)

select * from parsed
where event_id is not null
qualify row_number() over (partition by event_id order by load_ts desc) = 1
