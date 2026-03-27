# -----------------------------------------------------------------------------
# Snowflake Warehouses — sized for a POC/trial account
# -----------------------------------------------------------------------------

resource "snowflake_warehouse" "loading" {
  name           = "LOADING_WH"
  warehouse_size = "XSMALL"
  auto_suspend   = 60
  auto_resume    = true
  comment        = "Used by Snowpipe for COPY INTO operations"
}

resource "snowflake_warehouse" "transform" {
  name           = "TRANSFORM_WH"
  warehouse_size = "SMALL"
  auto_suspend   = 120
  auto_resume    = true
  comment        = "Used by dbt for transformations (run, test, snapshot)"
}

resource "snowflake_warehouse" "analytics" {
  name           = "ANALYTICS_WH"
  warehouse_size = "SMALL"
  auto_suspend   = 300
  auto_resume    = true
  comment        = "Used by Streamlit/Grafana dashboards and ad-hoc queries"
}
