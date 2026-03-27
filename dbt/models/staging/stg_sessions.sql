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
    from {{ source('raw_dbd', 'raw_session_event') }}
    {{ incremental_filter('load_ts') }}
),

parsed as (
    select
        raw_data:event_id::varchar              as event_id,
        raw_data:timestamp::timestamp_ntz       as event_timestamp,
        raw_data:player_id::varchar             as player_id,
        raw_data:session_id::varchar            as session_id,
        raw_data:action::varchar                as action,
        raw_data:platform::varchar              as platform,
        raw_data:region::varchar                as region,
        raw_data:client_version::varchar        as client_version,
        filename,
        load_ts
    from source
)

select * from parsed
where event_id is not null
qualify row_number() over (partition by event_id order by load_ts desc) = 1
