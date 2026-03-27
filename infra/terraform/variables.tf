# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "dbd"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "availability_zone" {
  description = "AZ for the single subnet (keep costs down)"
  type        = string
  default     = "us-east-1a"
}

# -----------------------------------------------------------------------------
# EC2 — orchestration (Airflow + dbt)
# -----------------------------------------------------------------------------
variable "orchestration_instance_type" {
  description = "Instance type for the orchestration EC2 (Airflow + dbt)"
  type        = string
  default     = "t3a.large" # option safe: t3a.xlarge
}

variable "orchestration_volume_size" {
  description = "Root EBS volume size in GB for orchestration instance"
  type        = number
  default     = 40
}

# -----------------------------------------------------------------------------
# EC2 — BI (Grafana + Streamlit)
# -----------------------------------------------------------------------------
variable "bi_instance_type" {
  description = "Instance type for the BI EC2 (Grafana + Streamlit)"
  type        = string
  default     = "t3a.large"
}

variable "bi_volume_size" {
  description = "Root EBS volume size in GB for BI instance"
  type        = number
  default     = 30
}

# -----------------------------------------------------------------------------
# SSH
# -----------------------------------------------------------------------------
variable "key_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH into the instances"
  type        = list(string)
  default     = ["0.0.0.0/0"] # restrict in prod
}

# -----------------------------------------------------------------------------
# AMI
# -----------------------------------------------------------------------------
variable "ami_id" {
  description = "AMI ID override. If empty, latest Ubuntu 22.04 is used."
  type        = string
  default     = ""
}
