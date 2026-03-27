# -----------------------------------------------------------------------------
# Snowpipe — one pipe per event type for auto-ingest from S3
# -----------------------------------------------------------------------------

locals {
  event_types = [
    "match_completed",
    "session_event",
    "store_transaction",
    "mmr_update",
    "player_registration",
    "progression_event",
  ]
}

# Raw tables (one per event type) — VARIANT column for JSON
resource "snowflake_table" "raw_events" {
  for_each = toset(local.event_types)

  database = snowflake_database.raw.name
  schema   = snowflake_schema.raw.name
  name     = upper("RAW_${each.value}")

  column {
    name = "RAW_DATA"
    type = "VARIANT"
  }

  column {
    name    = "FILENAME"
    type    = "VARCHAR"
    comment = "Source S3 file path"
  }

  column {
    name    = "LOAD_TS"
    type    = "TIMESTAMP_NTZ"
    default {
      expression = "CURRENT_TIMESTAMP()"
    }
    comment = "Timestamp when the row was loaded by Snowpipe"
  }

  comment = "Raw ${each.value} events ingested from S3"
}

# Snowpipe definitions
resource "snowflake_pipe" "events" {
  for_each = toset(local.event_types)

  database = snowflake_database.raw.name
  schema   = snowflake_schema.raw.name
  name     = upper("PIPE_${each.value}")

  auto_ingest = true

  copy_statement = <<-SQL
    COPY INTO "${snowflake_database.raw.name}"."${snowflake_schema.raw.name}"."${snowflake_table.raw_events[each.value].name}"
    (RAW_DATA, FILENAME)
    FROM (
      SELECT
        $1,
        METADATA$FILENAME
      FROM @"${snowflake_database.raw.name}"."${snowflake_schema.raw.name}"."${snowflake_stage.telemetry.name}"/${each.value}/
    )
    FILE_FORMAT = (FORMAT_NAME = '"${snowflake_database.raw.name}"."${snowflake_schema.raw.name}"."${snowflake_file_format.json_events.name}"')
  SQL

  aws_sns_topic_arn = var.sns_topic_arn

  comment = "Auto-ingest pipe for ${each.value} events"
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for Snowpipe notifications (set after AWS module)"
  type        = string
  default     = ""
}
