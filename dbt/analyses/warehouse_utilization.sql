{#
    Warehouse utilization analysis — idle vs active time.
    Helps identify over-provisioned or under-used warehouses.
#}

select
    warehouse_name,
    date_trunc('day', start_time)::date   as usage_date,
    count(*)                               as query_count,
    sum(execution_time) / 1000             as total_execution_seconds,
    avg(execution_time) / 1000             as avg_execution_seconds,
    max(execution_time) / 1000             as max_execution_seconds,
    sum(bytes_scanned) / power(1024, 3)    as total_gb_scanned,
    sum(partitions_scanned)                as total_partitions_scanned,
    sum(partitions_total)                  as total_partitions_total,
    round(
        sum(partitions_scanned) / nullif(sum(partitions_total), 0), 4
    ) as partition_scan_ratio
from snowflake.account_usage.query_history
where start_time >= dateadd(day, -30, current_timestamp())
    and warehouse_name is not null
group by 1, 2
order by 2 desc, 1;
