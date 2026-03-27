# -----------------------------------------------------------------------------
# Snowflake File Format — JSON for telemetry events
# -----------------------------------------------------------------------------

resource "snowflake_file_format" "json_events" {
  database  = snowflake_database.raw.name
  schema    = snowflake_schema.raw.name
  name      = "JSON_EVENTS"
  format_type = "JSON"

  comment = "JSON file format for telemetry events from S3"
}
