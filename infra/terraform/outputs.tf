output "orchestration_public_ip" {
  description = "Public IP of the orchestration instance (Airflow + dbt)"
  value       = aws_instance.orchestration.public_ip
}

output "bi_public_ip" {
  description = "Public IP of the BI instance (Grafana + Streamlit)"
  value       = aws_instance.bi.public_ip
}

output "orchestration_instance_id" {
  description = "Instance ID of the orchestration EC2"
  value       = aws_instance.orchestration.id
}

output "bi_instance_id" {
  description = "Instance ID of the BI EC2"
  value       = aws_instance.bi.id
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "ansible_inventory" {
  description = "Paste this into infra/ansible/inventory.ini after apply"
  value = <<-EOT
    [orchestration]
    ${aws_instance.orchestration.public_ip} ansible_user=ubuntu

    [bi]
    ${aws_instance.bi.public_ip} ansible_user=ubuntu

    [all:vars]
    ansible_ssh_private_key_file=~/.ssh/${var.key_name}.pem
  EOT
}
