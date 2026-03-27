{#
    Top 20 most expensive queries by execution time and bytes scanned.
    Use this to find optimization opportunities.
#}

select
    query_id,
    query_type,
    warehouse_name,
    user_name,
    role_name,
    database_name,
    schema_name,
    execution_status,
    start_time,
    total_elapsed_time / 1000                      as elapsed_seconds,
    execution_time / 1000                          as execution_seconds,
    bytes_scanned / power(1024, 3)                 as gb_scanned,
    rows_produced,
    partitions_scanned,
    partitions_total,
    round(
        partitions_scanned / nullif(partitions_total, 0), 4
    ) as partition_efficiency,
    substr(query_text, 1, 200) as query_preview
from snowflake.account_usage.query_history
where start_time >= dateadd(day, -7, current_timestamp())
    and execution_status = 'SUCCESS'
order by execution_time desc
limit 20;
