# -----------------------------------------------------------------------------
# Snowflake
# -----------------------------------------------------------------------------
variable "snowflake_organization_name" {
  description = "Snowflake organization name"
  type        = string
}

variable "snowflake_account_name" {
  description = "Snowflake account name"
  type        = string
}

variable "snowflake_user" {
  description = "Snowflake admin user for Terraform"
  type        = string
  sensitive   = true
}

variable "snowflake_password" {
  description = "Snowflake admin password"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# AWS
# -----------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS region for S3 and SNS"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for raw telemetry data"
  type        = string
  default     = "dbd-telemetry-raw"
}

variable "snowflake_aws_iam_user_arn" {
  description = "Snowflake storage integration IAM user ARN (from DESCRIBE INTEGRATION)"
  type        = string
  default     = ""
}

variable "snowflake_aws_external_id" {
  description = "Snowflake storage integration external ID (from DESCRIBE INTEGRATION)"
  type        = string
  default     = ""
}

# -----------------------------------------------------------------------------
# Budget
# -----------------------------------------------------------------------------
variable "credit_quota_monthly" {
  description = "Monthly credit quota for Snowflake resource monitor"
  type        = number
  default     = 10
}
