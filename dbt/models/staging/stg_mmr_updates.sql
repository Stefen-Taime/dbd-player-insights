with source as (
    select
        raw_data,
        filename,
        load_ts
    from {{ source('raw_dbd', 'raw_mmr_update') }}
),

parsed as (
    select
        raw_data:event_id::varchar              as event_id,
        raw_data:timestamp::timestamp_ntz       as event_timestamp,
        raw_data:player_id::varchar             as player_id,
        raw_data:match_id::varchar              as match_id,
        raw_data:mmr_before::int                as mmr_before,
        raw_data:mmr_after::int                 as mmr_after,
        raw_data:mmr_after::int - raw_data:mmr_before::int as mmr_change,
        raw_data:role::varchar                  as role,
        filename,
        load_ts
    from source
)

select * from parsed
where event_id is not null
qualify row_number() over (partition by event_id order by load_ts desc) = 1
