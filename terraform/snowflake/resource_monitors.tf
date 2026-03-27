# -----------------------------------------------------------------------------
# Snowflake Resource Monitor — budget alerts for trial/POC
# -----------------------------------------------------------------------------

resource "snowflake_resource_monitor" "monthly_budget" {
  name = "MONTHLY_BUDGET"

  credit_quota = var.credit_quota_monthly

  frequency       = "MONTHLY"
  start_timestamp = "IMMEDIATELY"

  notify_triggers            = [80, 90, 100]
  suspend_triggers           = [100]
  suspend_immediate_triggers = [110]

  comment = "Monthly credit budget monitor — alerts at 80/90/100%, suspend at 100%"
}
