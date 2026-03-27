{#
    Test: retention rates must be between 0% and 100%.
    Returns rows that violate the assertion.
#}

select
    cohort_week,
    retention_d1,
    retention_d7,
    retention_d30
from {{ ref('fct_player_retention') }}
where
    retention_d1 < 0 or retention_d1 > 1
    or retention_d7 < 0 or retention_d7 > 1
    or retention_d30 < 0 or retention_d30 > 1
