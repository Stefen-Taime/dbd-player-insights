# -----------------------------------------------------------------------------
# Snowflake Storage Integration + External Stage
# -----------------------------------------------------------------------------

resource "snowflake_storage_integration" "s3" {
  name    = "S3_INTEGRATION"
  type    = "EXTERNAL_STAGE"
  enabled = true

  storage_allowed_locations = ["s3://${var.s3_bucket_name}/"]
  storage_provider          = "S3"

  storage_aws_role_arn = "arn:aws:iam::role/snowflake-s3-access" # placeholder — updated after IAM role creation
  comment              = "Cross-account access to dbd-telemetry-raw S3 bucket"
}

resource "snowflake_stage" "telemetry" {
  database            = snowflake_database.raw.name
  schema              = snowflake_schema.raw.name
  name                = "S3_TELEMETRY_STAGE"
  url                 = "s3://${var.s3_bucket_name}/"
  storage_integration = snowflake_storage_integration.s3.name
  file_format         = "DATABASE = ${snowflake_database.raw.name} SCHEMA = ${snowflake_schema.raw.name} FORMAT_NAME = ${snowflake_file_format.json_events.name}"
  comment             = "External stage pointing to S3 telemetry landing zone"
}
