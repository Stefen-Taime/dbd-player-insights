{#
    Snowflake credit consumption analysis.
    Run this ad-hoc or via the cost monitoring DAG.
    Requires MONITOR role with IMPORTED PRIVILEGES on SNOWFLAKE database.
#}

-- Daily credit consumption by warehouse (last 30 days)
select
    warehouse_name,
    date_trunc('day', start_time)::date   as usage_date,
    sum(credits_used)                     as credits_used,
    sum(credits_used_compute)             as credits_compute,
    sum(credits_used_cloud_services)      as credits_cloud
from snowflake.account_usage.warehouse_metering_history
where start_time >= dateadd(day, -30, current_timestamp())
group by 1, 2
order by 2 desc, 3 desc;

-- 7-day rolling average
select
    usage_date,
    warehouse_name,
    credits_used,
    avg(credits_used) over (
        partition by warehouse_name
        order by usage_date
        rows between 6 preceding and current row
    ) as credits_7d_avg
from (
    select
        warehouse_name,
        date_trunc('day', start_time)::date as usage_date,
        sum(credits_used)                   as credits_used
    from snowflake.account_usage.warehouse_metering_history
    where start_time >= dateadd(day, -37, current_timestamp())
    group by 1, 2
)
order by usage_date desc, warehouse_name;
