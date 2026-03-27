# =============================================================================
# infra/Makefile — deploy & manage the 2 EC2 instances
# =============================================================================

.PHONY: help tf-init tf-plan tf-apply tf-destroy tf-output \
        ansible-deps ansible-ping ansible-play ansible-play-orch ansible-play-bi \
        inventory ssh-orch ssh-bi clean

SHELL := /bin/bash

TF_DIR   := terraform
ANSIBLE_DIR := ansible

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# -----------------------------------------------------------------------------
# Terraform
# -----------------------------------------------------------------------------
tf-init: ## terraform init
	terraform -chdir=$(TF_DIR) init

tf-plan: ## terraform plan
	terraform -chdir=$(TF_DIR) plan

tf-apply: ## terraform apply (auto-approve)
	terraform -chdir=$(TF_DIR) apply -auto-approve

tf-destroy: ## terraform destroy (auto-approve) — CAREFUL
	terraform -chdir=$(TF_DIR) destroy -auto-approve

tf-output: ## Show terraform outputs
	terraform -chdir=$(TF_DIR) output

# -----------------------------------------------------------------------------
# Generate inventory.ini from terraform outputs
# -----------------------------------------------------------------------------
inventory: ## Generate ansible/inventory.ini from terraform outputs
	@terraform -chdir=$(TF_DIR) output -raw ansible_inventory > $(ANSIBLE_DIR)/inventory.ini
	@echo "inventory.ini generated:"
	@cat $(ANSIBLE_DIR)/inventory.ini

# -----------------------------------------------------------------------------
# Ansible
# -----------------------------------------------------------------------------
ansible-deps: ## Install Ansible Galaxy collections
	ansible-galaxy collection install -r $(ANSIBLE_DIR)/requirements.yml --force

ansible-ping: ## Ping all hosts
	ansible -i $(ANSIBLE_DIR)/inventory.ini all -m ping

ansible-play: ## Run full playbook (all hosts)
	ansible-playbook -i $(ANSIBLE_DIR)/inventory.ini $(ANSIBLE_DIR)/site.yml

ansible-play-orch: ## Run playbook — orchestration host only
	ansible-playbook -i $(ANSIBLE_DIR)/inventory.ini $(ANSIBLE_DIR)/site.yml --limit orchestration

ansible-play-bi: ## Run playbook — BI host only
	ansible-playbook -i $(ANSIBLE_DIR)/inventory.ini $(ANSIBLE_DIR)/site.yml --limit bi

# -----------------------------------------------------------------------------
# SSH shortcuts
# -----------------------------------------------------------------------------
ssh-orch: ## SSH into orchestration instance
	@IP=$$(terraform -chdir=$(TF_DIR) output -raw orchestration_public_ip) && \
	KEY=$$(grep ansible_ssh_private_key_file $(ANSIBLE_DIR)/inventory.ini | head -1 | cut -d= -f2) && \
	ssh -i $$KEY ubuntu@$$IP

ssh-bi: ## SSH into BI instance
	@IP=$$(terraform -chdir=$(TF_DIR) output -raw bi_public_ip) && \
	KEY=$$(grep ansible_ssh_private_key_file $(ANSIBLE_DIR)/inventory.ini | head -1 | cut -d= -f2) && \
	ssh -i $$KEY ubuntu@$$IP

# -----------------------------------------------------------------------------
# Full workflow
# -----------------------------------------------------------------------------
deploy: tf-apply inventory ansible-deps ansible-play ## Full deploy: terraform + ansible

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
clean: ## Remove generated files
	rm -f $(ANSIBLE_DIR)/inventory.ini
	rm -rf $(TF_DIR)/.terraform $(TF_DIR)/.terraform.lock.hcl
