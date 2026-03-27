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
    from {{ source('raw_dbd', 'raw_match_completed') }}
    {{ incremental_filter('load_ts') }}
),

parsed as (
    select
        raw_data:event_id::varchar                     as event_id,
        raw_data:match_id::varchar                     as match_id,
        raw_data:timestamp::timestamp_ntz              as event_timestamp,
        raw_data:duration_seconds::int                 as duration_seconds,
        raw_data:map_id::varchar                       as map_id,
        raw_data:game_mode::varchar                    as game_mode,

        -- Killer fields
        raw_data:killer.player_id::varchar             as killer_player_id,
        raw_data:killer.character_id::varchar           as killer_character_id,
        raw_data:killer.perks::array                   as killer_perks,
        raw_data:killer.kills::int                     as killer_kills,
        raw_data:killer.hooks::int                     as killer_hooks,
        raw_data:killer.score::int                     as killer_score,

        -- Survivors (keep as array for downstream flattening)
        raw_data:survivors::array                      as survivors,

        filename,
        load_ts
    from source
)

select * from parsed
where event_id is not null
qualify row_number() over (partition by event_id order by load_ts desc) = 1
