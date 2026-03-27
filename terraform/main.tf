terraform {
  required_version = ">= 1.5"

  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# -----------------------------------------------------------------------------
# Providers
# -----------------------------------------------------------------------------
provider "snowflake" {
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  user              = var.snowflake_user
  password          = var.snowflake_password
  role              = "ACCOUNTADMIN"

  preview_features_enabled = [
    "snowflake_file_format_resource",
    "snowflake_table_resource",
    "snowflake_storage_integration_resource",
    "snowflake_stage_resource",
    "snowflake_pipe_resource",
  ]
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "dbd-player-insights"
      ManagedBy = "terraform"
    }
  }
}
