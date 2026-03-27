#!/usr/bin/env bash
# =============================================================================
# Upload generated data to S3 telemetry bucket
# Credentials from AWS CLI profile — never hardcoded
# =============================================================================
set -euo pipefail

BUCKET="${S3_BUCKET_NAME:-dbd-telemetry-raw}"
LOCAL_DATA_DIR="${1:-./data/output}"

if [ ! -d "${LOCAL_DATA_DIR}" ]; then
    echo "ERROR: Data directory '${LOCAL_DATA_DIR}' not found."
    echo "Run: python -m generator --players 50000 --days 90 --target local"
    exit 1
fi

echo "==> Uploading data from ${LOCAL_DATA_DIR} to s3://${BUCKET}/"
aws s3 sync "${LOCAL_DATA_DIR}" "s3://${BUCKET}/" \
    --exclude "*.DS_Store" \
    --exclude "__pycache__/*"

echo "==> Upload complete. File count:"
aws s3 ls "s3://${BUCKET}/" --recursive --summarize | tail -2
