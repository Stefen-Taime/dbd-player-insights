{#
    Macro: retention_cohort
    Calculates retention rates for player cohorts at day N.
    Args:
        activity_table: ref to a model with player_id + activity_date
        cohort_table:   ref to a model with player_id + cohort_date (first seen)
        day_n:          number of days after cohort_date to check retention
#}
{% macro retention_cohort(activity_table, cohort_table, day_n) %}

with cohort as (
    select
        player_id,
        cohort_date
    from {{ cohort_table }}
),

activity as (
    select distinct
        player_id,
        activity_date
    from {{ activity_table }}
),

retention as (
    select
        c.cohort_date,
        count(distinct c.player_id) as cohort_size,
        count(distinct a.player_id) as retained_players
    from cohort c
    left join activity a
        on c.player_id = a.player_id
        and a.activity_date = dateadd(day, {{ day_n }}, c.cohort_date)
    group by 1
)

select
    cohort_date,
    cohort_size,
    retained_players,
    round(retained_players / nullif(cohort_size, 0), 4) as retention_rate
from retention

{% endmacro %}
