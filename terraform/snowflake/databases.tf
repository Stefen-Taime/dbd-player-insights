# -----------------------------------------------------------------------------
# Snowflake Databases
# DBD_RAW      — Bronze layer: raw JSON ingested by Snowpipe
# DBD_ANALYTICS — Silver + Gold layers: dbt transformations
# -----------------------------------------------------------------------------

resource "snowflake_database" "raw" {
  name    = "DBD_RAW"
  comment = "Raw telemetry data ingested from S3 via Snowpipe"
}

resource "snowflake_database" "analytics" {
  name    = "DBD_ANALYTICS"
  comment = "Transformed data (staging, intermediate, marts) managed by dbt"
}
