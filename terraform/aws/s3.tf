# -----------------------------------------------------------------------------
# S3 Bucket — telemetry landing zone
# Best practices 2026: SSE-S3, public access blocked, versioning, lifecycle
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "telemetry" {
  bucket = var.s3_bucket_name

  tags = { Name = var.s3_bucket_name }
}

# --- Block all public access -------------------------------------------------
resource "aws_s3_bucket_public_access_block" "telemetry" {
  bucket = aws_s3_bucket.telemetry.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- Server-side encryption (SSE-S3, free, automatic) -----------------------
resource "aws_s3_bucket_server_side_encryption_configuration" "telemetry" {
  bucket = aws_s3_bucket.telemetry.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# --- Versioning (required before lifecycle rules) ----------------------------
resource "aws_s3_bucket_versioning" "telemetry" {
  bucket = aws_s3_bucket.telemetry.id

  versioning_configuration {
    status = "Enabled"
  }
}

# --- Lifecycle rules ---------------------------------------------------------
resource "aws_s3_bucket_lifecycle_configuration" "telemetry" {
  bucket = aws_s3_bucket.telemetry.id

  depends_on = [aws_s3_bucket_versioning.telemetry]

  # Transition raw telemetry to IA after 90 days, Glacier after 180, expire at 365
  rule {
    id     = "telemetry-tiered-storage"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 180
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }

    # Clean up old versions
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }

  # Abort incomplete multipart uploads
  rule {
    id     = "abort-incomplete-multipart"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# --- S3 event notification -> SNS (for Snowpipe) ----------------------------
resource "aws_s3_bucket_notification" "snowpipe" {
  bucket = aws_s3_bucket.telemetry.id

  topic {
    topic_arn = aws_sns_topic.snowpipe_notifications.arn
    events    = ["s3:ObjectCreated:*"]
  }
}
