# -----------------------------------------------------------------------------
# Snowflake Resource Monitor — budget alerts for trial/POC
# Provider v1.0+: singular trigger names, no comment attribute
# -----------------------------------------------------------------------------

resource "snowflake_resource_monitor" "monthly_budget" {
  name = "MONTHLY_BUDGET"

  credit_quota = var.credit_quota_monthly

  frequency       = "MONTHLY"
  start_timestamp = "IMMEDIATELY"

  notify_triggers           = [80, 90, 100]
  suspend_trigger           = 100
  suspend_immediate_trigger = 110
}
