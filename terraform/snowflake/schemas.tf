# -----------------------------------------------------------------------------
# Snowflake Schemas
# -----------------------------------------------------------------------------

# --- DBD_RAW schemas ---------------------------------------------------------
resource "snowflake_schema" "raw" {
  database = snowflake_database.raw.name
  name     = "RAW"
  comment  = "Raw JSON event tables (loaded by Snowpipe)"
}

# --- DBD_ANALYTICS schemas ---------------------------------------------------
resource "snowflake_schema" "staging" {
  database = snowflake_database.analytics.name
  name     = "STAGING"
  comment  = "Silver layer — cleaned, typed, deduplicated (dbt)"
}

resource "snowflake_schema" "intermediate" {
  database = snowflake_database.analytics.name
  name     = "INTERMEDIATE"
  comment  = "Business logic joins and enrichments (dbt)"
}

resource "snowflake_schema" "marts" {
  database = snowflake_database.analytics.name
  name     = "MARTS"
  comment  = "Gold layer — facts and dimensions for analytics (dbt)"
}
