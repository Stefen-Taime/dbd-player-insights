# -----------------------------------------------------------------------------
# Snowflake Roles & Grants — least-privilege model
# -----------------------------------------------------------------------------

# --- Roles -------------------------------------------------------------------
resource "snowflake_account_role" "loader" {
  name    = "LOADER"
  comment = "Snowpipe ingestion into DBD_RAW"
}

resource "snowflake_account_role" "transformer" {
  name    = "TRANSFORMER"
  comment = "dbt transformations — read RAW, write ANALYTICS"
}

resource "snowflake_account_role" "analyst" {
  name    = "ANALYST"
  comment = "Dashboard queries — read-only on ANALYTICS marts"
}

resource "snowflake_account_role" "monitor" {
  name    = "MONITOR"
  comment = "Cost monitoring — ACCOUNT_USAGE + RESOURCE_MONITOR"
}

# --- LOADER grants -----------------------------------------------------------
resource "snowflake_grant_privileges_to_account_role" "loader_raw_db" {
  account_role_name = snowflake_account_role.loader.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.raw.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "loader_raw_schema" {
  account_role_name = snowflake_account_role.loader.name
  privileges        = ["USAGE", "CREATE TABLE"]
  on_schema {
    schema_name = "\"${snowflake_database.raw.name}\".\"${snowflake_schema.raw.name}\""
  }
}

resource "snowflake_grant_privileges_to_account_role" "loader_wh" {
  account_role_name = snowflake_account_role.loader.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.loading.name
  }
}

# --- TRANSFORMER grants ------------------------------------------------------
resource "snowflake_grant_privileges_to_account_role" "transformer_raw_db" {
  account_role_name = snowflake_account_role.transformer.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.raw.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "transformer_raw_schema_usage" {
  account_role_name = snowflake_account_role.transformer.name
  privileges        = ["USAGE"]
  on_schema {
    schema_name = "\"${snowflake_database.raw.name}\".\"${snowflake_schema.raw.name}\""
  }
}

resource "snowflake_grant_privileges_to_account_role" "transformer_raw_tables" {
  account_role_name = snowflake_account_role.transformer.name
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "\"${snowflake_database.raw.name}\".\"${snowflake_schema.raw.name}\""
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "transformer_analytics_db" {
  account_role_name = snowflake_account_role.transformer.name
  privileges        = ["USAGE", "CREATE SCHEMA"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.analytics.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "transformer_staging" {
  account_role_name = snowflake_account_role.transformer.name
  all_privileges    = true
  on_schema {
    schema_name = "\"${snowflake_database.analytics.name}\".\"${snowflake_schema.staging.name}\""
  }
}

resource "snowflake_grant_privileges_to_account_role" "transformer_intermediate" {
  account_role_name = snowflake_account_role.transformer.name
  all_privileges    = true
  on_schema {
    schema_name = "\"${snowflake_database.analytics.name}\".\"${snowflake_schema.intermediate.name}\""
  }
}

resource "snowflake_grant_privileges_to_account_role" "transformer_marts" {
  account_role_name = snowflake_account_role.transformer.name
  all_privileges    = true
  on_schema {
    schema_name = "\"${snowflake_database.analytics.name}\".\"${snowflake_schema.marts.name}\""
  }
}

resource "snowflake_grant_privileges_to_account_role" "transformer_wh" {
  account_role_name = snowflake_account_role.transformer.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.transform.name
  }
}

# --- ANALYST grants ----------------------------------------------------------
resource "snowflake_grant_privileges_to_account_role" "analyst_analytics_db" {
  account_role_name = snowflake_account_role.analyst.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = snowflake_database.analytics.name
  }
}

resource "snowflake_grant_privileges_to_account_role" "analyst_marts" {
  account_role_name = snowflake_account_role.analyst.name
  privileges        = ["USAGE"]
  on_schema {
    schema_name = "\"${snowflake_database.analytics.name}\".\"${snowflake_schema.marts.name}\""
  }
}

resource "snowflake_grant_privileges_to_account_role" "analyst_marts_tables" {
  account_role_name = snowflake_account_role.analyst.name
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_schema          = "\"${snowflake_database.analytics.name}\".\"${snowflake_schema.marts.name}\""
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "analyst_marts_views" {
  account_role_name = snowflake_account_role.analyst.name
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "VIEWS"
      in_schema          = "\"${snowflake_database.analytics.name}\".\"${snowflake_schema.marts.name}\""
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "analyst_wh" {
  account_role_name = snowflake_account_role.analyst.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.analytics.name
  }
}

# --- Grant roles to user STEFEN ---------------------------------------------
resource "snowflake_grant_account_role" "stefen_loader" {
  role_name = snowflake_account_role.loader.name
  user_name = var.snowflake_user
}

resource "snowflake_grant_account_role" "stefen_transformer" {
  role_name = snowflake_account_role.transformer.name
  user_name = var.snowflake_user
}

resource "snowflake_grant_account_role" "stefen_analyst" {
  role_name = snowflake_account_role.analyst.name
  user_name = var.snowflake_user
}

resource "snowflake_grant_account_role" "stefen_monitor" {
  role_name = snowflake_account_role.monitor.name
  user_name = var.snowflake_user
}

# --- MONITOR grants ----------------------------------------------------------
resource "snowflake_grant_privileges_to_account_role" "monitor_account_usage" {
  account_role_name = snowflake_account_role.monitor.name
  privileges        = ["IMPORTED PRIVILEGES"]
  on_account_object {
    object_type = "DATABASE"
    object_name = "SNOWFLAKE"
  }
}
