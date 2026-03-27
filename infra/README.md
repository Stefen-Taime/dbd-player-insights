# Infrastructure — 2 EC2 instances

Provisioning de l'infra AWS pour le projet DBD Player Insights.

- **Terraform** : VPC, Security Groups, 2 EC2 (gp3, IMDSv2)
- **Ansible** : Docker, Airflow, dbt, Grafana, Streamlit, Nginx

## Architecture

```
┌─────────────────────────────────────────┐
│  ec2-orchestration (t3a.large)          │
│  ├── Docker                             │
│  │   ├── Airflow webserver              │
│  │   ├── Airflow scheduler              │
│  │   ├── Airflow triggerer              │
│  │   └── PostgreSQL (metadata)          │
│  ├── dbt (venv Python, hors Docker)     │
│  ├── CloudWatch Agent                   │
│  └── Slack alerts (webhook Airflow)     │
├─────────────────────────────────────────┤
│  ec2-bi (t3a.large)                     │
│  ├── Docker                             │
│  │   ├── Grafana                        │
│  │   └── Streamlit                      │
│  └── Nginx (reverse proxy)              │
│      ├── /          → Streamlit :8501   │
│      └── /grafana/  → Grafana :3000     │
└─────────────────────────────────────────┘
```

## Prérequis

- Terraform >= 1.5
- Ansible >= 2.15
- AWS CLI configuré (`aws configure`)
- Key pair EC2 existante dans `us-east-1`

## Deploiement rapide

```bash
cd infra

# 1. Terraform
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Editer terraform.tfvars (key_name, allowed_ssh_cidrs)
make tf-init
make tf-apply

# 2. Generer l'inventaire Ansible depuis Terraform
make inventory

# 3. Installer les collections Ansible
make ansible-deps

# 4. Tester la connectivite SSH
make ansible-ping

# 5. Provisionner les 2 instances
make ansible-play
```

Ou en une seule commande :

```bash
make deploy
```

## Variables sensibles

Passer les secrets via `--extra-vars` ou variables d'environnement :

```bash
export AIRFLOW_FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export SNOWFLAKE_ACCOUNT=xxx
export SNOWFLAKE_USER=xxx
export SNOWFLAKE_PASSWORD=xxx
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
export GRAFANA_ADMIN_PASSWORD=changeme
```

## Couts estimes (us-east-1, On-Demand)

| Ressource | Cout/heure | 3h test |
|---|---|---|
| 2x t3a.large | 0.1504 USD/h | ~0.45 USD |
| 2x IPv4 publique | 0.010 USD/h | ~0.03 USD |
| 2x gp3 (40+30 Go) | ~0.0077 USD/h | ~0.02 USD |
| **Total** | **~0.17 USD/h** | **~0.50 USD** |

## Nettoyage

```bash
make tf-destroy
```
