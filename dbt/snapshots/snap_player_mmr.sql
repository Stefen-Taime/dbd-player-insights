{% snapshot snap_player_mmr %}

{{
    config(
        target_database='DBD_ANALYTICS',
        target_schema='snapshots',
        unique_key='player_id',
        strategy='check',
        check_cols=['current_mmr', 'mmr_segment'],
    )
}}

{#
    SCD Type 2 snapshot of player MMR.
    Captures changes in MMR over time for historical analysis.
#}

with latest_mmr as (
    select
        player_id,
        mmr_after       as current_mmr,
        role            as last_role,
        event_timestamp as mmr_updated_at,
        case
            when mmr_after < 500  then 'new'
            when mmr_after < 1000 then 'casual'
            when mmr_after < 1500 then 'core'
            else 'hardcore'
        end as mmr_segment
    from {{ source('raw_dbd', 'raw_mmr_update') }}
    qualify row_number() over (partition by raw_data:player_id::varchar order by raw_data:timestamp::timestamp_ntz desc) = 1
)

select * from latest_mmr

{% endsnapshot %}
