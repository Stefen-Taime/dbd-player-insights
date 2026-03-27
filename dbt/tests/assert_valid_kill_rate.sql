{#
    Test: kill rate must be between 0 and 1 for every killer.
    Returns rows that violate the assertion.
#}

select
    killer_character_id,
    kill_rate
from {{ ref('fct_match_outcomes') }}
where kill_rate < 0 or kill_rate > 1
