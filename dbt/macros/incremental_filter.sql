{#
    Macro: incremental_filter
    Reusable WHERE clause for incremental models.
    Looks back N days from the max timestamp in the current model.
    Args:
        timestamp_column: the column to filter on (default: 'event_timestamp')
#}
{% macro incremental_filter(timestamp_column='event_timestamp') %}

{% if is_incremental() %}
    where {{ timestamp_column }} >= (
        select dateadd(day, -{{ var('incremental_lookback_days', 3) }}, max({{ timestamp_column }}))
        from {{ this }}
    )
{% endif %}

{% endmacro %}
