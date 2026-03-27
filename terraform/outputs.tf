output "s3_bucket_arn" {
  description = "ARN of the telemetry S3 bucket"
  value       = aws_s3_bucket.telemetry.arn
}

output "s3_bucket_name" {
  description = "Name of the telemetry S3 bucket"
  value       = aws_s3_bucket.telemetry.id
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for S3 -> Snowpipe notifications"
  value       = aws_sns_topic.snowpipe_notifications.arn
}

output "iam_role_arn" {
  description = "ARN of the IAM role for Snowflake cross-account access"
  value       = aws_iam_role.snowflake_s3_access.arn
}

output "snowflake_databases" {
  description = "Snowflake databases created"
  value       = [snowflake_database.raw.name, snowflake_database.analytics.name]
}

output "snowflake_warehouses" {
  description = "Snowflake warehouses created"
  value = [
    snowflake_warehouse.loading.name,
    snowflake_warehouse.transform.name,
    snowflake_warehouse.analytics.name,
  ]
}
