# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

# --- Orchestration (Airflow + dbt) -------------------------------------------
resource "aws_security_group" "orchestration" {
  name        = "${var.project}-orchestration-sg"
  description = "Airflow UI + SSH"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${var.project}-orchestration-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "orch_ssh" {
  security_group_id = aws_security_group.orchestration.id
  description       = "SSH"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
  cidr_ipv4         = var.allowed_ssh_cidrs[0]
}

resource "aws_vpc_security_group_ingress_rule" "orch_airflow_ui" {
  security_group_id = aws_security_group.orchestration.id
  description       = "Airflow webserver"
  from_port         = 8080
  to_port           = 8080
  ip_protocol       = "tcp"
  cidr_ipv4         = var.allowed_ssh_cidrs[0]
}

resource "aws_vpc_security_group_egress_rule" "orch_all_out" {
  security_group_id = aws_security_group.orchestration.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}

# --- BI (Grafana + Streamlit) ------------------------------------------------
resource "aws_security_group" "bi" {
  name        = "${var.project}-bi-sg"
  description = "Grafana + Streamlit + SSH"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${var.project}-bi-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "bi_ssh" {
  security_group_id = aws_security_group.bi.id
  description       = "SSH"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
  cidr_ipv4         = var.allowed_ssh_cidrs[0]
}

resource "aws_vpc_security_group_ingress_rule" "bi_http" {
  security_group_id = aws_security_group.bi.id
  description       = "HTTP (Nginx reverse proxy)"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "bi_https" {
  security_group_id = aws_security_group.bi.id
  description       = "HTTPS"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "bi_grafana" {
  security_group_id = aws_security_group.bi.id
  description       = "Grafana direct (dev fallback)"
  from_port         = 3000
  to_port           = 3000
  ip_protocol       = "tcp"
  cidr_ipv4         = var.allowed_ssh_cidrs[0]
}

resource "aws_vpc_security_group_ingress_rule" "bi_streamlit" {
  security_group_id = aws_security_group.bi.id
  description       = "Streamlit direct (dev fallback)"
  from_port         = 8501
  to_port           = 8501
  ip_protocol       = "tcp"
  cidr_ipv4         = var.allowed_ssh_cidrs[0]
}

resource "aws_vpc_security_group_egress_rule" "bi_all_out" {
  security_group_id = aws_security_group.bi.id
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
