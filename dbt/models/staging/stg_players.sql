{#
    Deduplicated player profiles — takes the latest registration event per player.
    This is a view (lightweight) since it simply references raw data.
#}

with source as (
    select
        raw_data,
        filename,
        load_ts
    from {{ source('raw_dbd', 'raw_player_registration') }}
),

parsed as (
    select
        raw_data:platform_accounts[0].platform_player_id::varchar as player_id,
        raw_data:bhvr_id::varchar               as bhvr_id,
        raw_data:timestamp::timestamp_ntz       as registered_at,
        raw_data:display_name::varchar          as username,
        raw_data:primary_platform::varchar      as platform,
        raw_data:region::varchar                as region,
        filename,
        load_ts
    from source
)

select * from parsed
where player_id is not null
qualify row_number() over (partition by player_id order by load_ts desc) = 1
