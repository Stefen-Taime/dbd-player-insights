#!/usr/bin/env bash
# =============================================================================
# Bootstrap Snowflake objects (alternative to Terraform)
# Credentials from environment variables — never hardcoded
# =============================================================================
set -euo pipefail

: "${SNOWFLAKE_ACCOUNT:?SNOWFLAKE_ACCOUNT not set}"
: "${SNOWFLAKE_USER:?SNOWFLAKE_USER not set}"
: "${SNOWFLAKE_PASSWORD:?SNOWFLAKE_PASSWORD not set}"

SNOWSQL_OPTS="--accountname ${SNOWFLAKE_ACCOUNT} --username ${SNOWFLAKE_USER} --dbname SNOWFLAKE"

echo "==> Creating databases..."
snowsql ${SNOWSQL_OPTS} -q "
CREATE DATABASE IF NOT EXISTS DBD_RAW COMMENT = 'Raw telemetry data';
CREATE DATABASE IF NOT EXISTS DBD_ANALYTICS COMMENT = 'Transformed data (dbt)';
"

echo "==> Creating schemas..."
snowsql ${SNOWSQL_OPTS} -q "
CREATE SCHEMA IF NOT EXISTS DBD_RAW.RAW;
CREATE SCHEMA IF NOT EXISTS DBD_ANALYTICS.STAGING;
CREATE SCHEMA IF NOT EXISTS DBD_ANALYTICS.INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS DBD_ANALYTICS.MARTS;
CREATE SCHEMA IF NOT EXISTS DBD_ANALYTICS.SNAPSHOTS;
"

echo "==> Creating warehouses..."
snowsql ${SNOWSQL_OPTS} -q "
CREATE WAREHOUSE IF NOT EXISTS LOADING_WH   WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60  AUTO_RESUME = TRUE;
CREATE WAREHOUSE IF NOT EXISTS TRANSFORM_WH  WAREHOUSE_SIZE = 'SMALL'  AUTO_SUSPEND = 120 AUTO_RESUME = TRUE;
CREATE WAREHOUSE IF NOT EXISTS ANALYTICS_WH  WAREHOUSE_SIZE = 'SMALL'  AUTO_SUSPEND = 300 AUTO_RESUME = TRUE;
"

echo "==> Creating roles..."
snowsql ${SNOWSQL_OPTS} -q "
CREATE ROLE IF NOT EXISTS LOADER;
CREATE ROLE IF NOT EXISTS TRANSFORMER;
CREATE ROLE IF NOT EXISTS ANALYST;
CREATE ROLE IF NOT EXISTS MONITOR;
"

echo "==> Done. Run 'terraform apply' for full setup including IAM, S3, and Snowpipe."
