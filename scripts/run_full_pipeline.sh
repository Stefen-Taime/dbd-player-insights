#!/usr/bin/env bash
# =============================================================================
# Full pipeline: generate -> upload -> dbt
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

echo "=========================================="
echo " DBD Player Insights — Full Pipeline"
echo "=========================================="

# 1. Generate synthetic data
echo ""
echo "==> Step 1/4: Generating synthetic data..."
cd "${PROJECT_DIR}"
python -m generator --players "${PLAYERS:-50000}" --days "${DAYS:-90}" --target "${TARGET:-s3}"

# 2. Wait for Snowpipe ingestion (if S3 target)
if [ "${TARGET:-s3}" = "s3" ]; then
    echo ""
    echo "==> Step 2/4: Waiting 120s for Snowpipe ingestion..."
    sleep 120
else
    echo ""
    echo "==> Step 2/4: Skipping Snowpipe wait (local target)"
fi

# 3. Run dbt
echo ""
echo "==> Step 3/4: Running dbt pipeline..."
cd "${PROJECT_DIR}/dbt"
dbt deps
dbt seed
dbt run
dbt test
dbt docs generate

# 4. Summary
echo ""
echo "==> Step 4/4: Pipeline complete!"
echo ""
echo "Next steps:"
echo "  - View dbt docs:    cd dbt && dbt docs serve"
echo "  - Launch dashboard: cd dashboard && streamlit run app.py"
echo "  - Check Airflow:    cd airflow && docker compose up -d"
