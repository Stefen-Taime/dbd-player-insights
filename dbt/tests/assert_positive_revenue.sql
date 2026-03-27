{#
    Test: all store transactions must have non-negative revenue.
    Returns rows that violate the assertion (should return 0 rows to pass).
#}

select
    event_id,
    transaction_id,
    amount_usd
from {{ ref('stg_store_transactions') }}
where amount_usd < 0
