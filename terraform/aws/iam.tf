# -----------------------------------------------------------------------------
# IAM Role — Snowflake cross-account access to S3
# Best practice: use storage integration (not direct IAM credentials, deprecated)
# The trust policy allows Snowflake's IAM user to assume this role.
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

locals {
  # Pre-compute the role ARN to avoid chicken-and-egg with storage integration
  snowflake_role_name = "snowflake-s3-access"
  snowflake_role_arn  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${local.snowflake_role_name}"
}

resource "aws_iam_role" "snowflake_s3_access" {
  name = local.snowflake_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = var.snowflake_aws_iam_user_arn != "" ? var.snowflake_aws_iam_user_arn : data.aws_caller_identity.current.account_id
        }
        Action = "sts:AssumeRole"
        Condition = var.snowflake_aws_external_id != "" ? {
          StringEquals = {
            "sts:ExternalId" = var.snowflake_aws_external_id
          }
        } : {}
      }
    ]
  })

  tags = { Name = local.snowflake_role_name }
}

resource "aws_iam_role_policy" "snowflake_s3_read" {
  name = "snowflake-s3-read-policy"
  role = aws_iam_role.snowflake_s3_access.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
        ]
        Resource = "${aws_s3_bucket.telemetry.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
        ]
        Resource = aws_s3_bucket.telemetry.arn
      },
    ]
  })
}
