#!/usr/bin/env bash
# =============================================================================
# Export dbt lineage graph as artifacts
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DBT_DIR="$(dirname "${SCRIPT_DIR}")/dbt"

echo "==> Generating dbt docs and lineage..."
cd "${DBT_DIR}"
dbt docs generate

echo "==> Lineage artifacts saved to:"
echo "    ${DBT_DIR}/target/manifest.json"
echo "    ${DBT_DIR}/target/catalog.json"
echo "    ${DBT_DIR}/target/index.html"

echo ""
echo "==> To view: dbt docs serve"
echo "==> To share: copy target/ to a static hosting service"
