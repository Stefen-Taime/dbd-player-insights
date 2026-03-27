# -----------------------------------------------------------------------------
# SNS Topic — S3 event notifications -> Snowpipe SQS subscription
# -----------------------------------------------------------------------------

resource "aws_sns_topic" "snowpipe_notifications" {
  name = "dbd-snowpipe-s3-notifications"

  tags = { Name = "dbd-snowpipe-s3-notifications" }
}

# Allow S3 to publish to this SNS topic
resource "aws_sns_topic_policy" "allow_s3" {
  arn = aws_sns_topic.snowpipe_notifications.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowS3Publish"
        Effect    = "Allow"
        Principal = { Service = "s3.amazonaws.com" }
        Action    = "SNS:Publish"
        Resource  = aws_sns_topic.snowpipe_notifications.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = aws_s3_bucket.telemetry.arn
          }
        }
      },
      {
        Sid       = "AllowSnowflakeSubscribe"
        Effect    = "Allow"
        Principal = { AWS = "*" }
        Action    = "SNS:Subscribe"
        Resource  = aws_sns_topic.snowpipe_notifications.arn
        Condition = {
          StringLike = {
            "sns:Endpoint" = "arn:aws:sqs:*:*:sf-snowpipe-*"
          }
        }
      }
    ]
  })
}
