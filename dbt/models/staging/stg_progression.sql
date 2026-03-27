with source as (
    select
        raw_data,
        filename,
        load_ts
    from {{ source('raw_dbd', 'raw_progression_event') }}
),

parsed as (
    select
        raw_data:event_id::varchar              as event_id,
        raw_data:timestamp::timestamp_ntz       as event_timestamp,
        raw_data:player_id::varchar             as player_id,
        raw_data:progression_type::varchar      as progression_type,
        raw_data:character_id::varchar          as character_id,
        raw_data:value_before::int              as value_before,
        raw_data:value_after::int               as value_after,
        raw_data:value_after::int - raw_data:value_before::int as value_change,
        filename,
        load_ts
    from source
)

select * from parsed
where event_id is not null
qualify row_number() over (partition by event_id order by load_ts desc) = 1
