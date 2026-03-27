# -----------------------------------------------------------------------------
# Data source — latest Ubuntu 22.04 LTS AMI
# -----------------------------------------------------------------------------
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  ami_id = var.ami_id != "" ? var.ami_id : data.aws_ami.ubuntu.id
}

# -----------------------------------------------------------------------------
# EC2 — Orchestration (Airflow + dbt + Slack alerts)
# -----------------------------------------------------------------------------
resource "aws_instance" "orchestration" {
  ami                    = local.ami_id
  instance_type          = var.orchestration_instance_type
  key_name               = var.key_name
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.orchestration.id]

  root_block_device {
    volume_size = var.orchestration_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  metadata_options {
    http_tokens = "required" # IMDSv2
  }

  tags = {
    Name = "${var.project}-orchestration"
    Role = "orchestration"
  }
}

# -----------------------------------------------------------------------------
# EC2 — BI (Grafana + Streamlit)
# -----------------------------------------------------------------------------
resource "aws_instance" "bi" {
  ami                    = local.ami_id
  instance_type          = var.bi_instance_type
  key_name               = var.key_name
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.bi.id]

  root_block_device {
    volume_size = var.bi_volume_size
    volume_type = "gp3"
    encrypted   = true
  }

  metadata_options {
    http_tokens = "required" # IMDSv2
  }

  tags = {
    Name = "${var.project}-bi"
    Role = "bi"
  }
}
