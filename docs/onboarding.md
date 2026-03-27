# Guide de demarrage rapide

## Prerequis

- Python 3.12+
- Docker & Docker Compose v2.14+
- AWS CLI configure (`aws configure`)
- Compte Snowflake (trial 30 jours : signup.snowflake.com)
- Terraform >= 1.5
- Ansible >= 2.15 (pour le deploiement EC2)

## Installation locale

```bash
# 1. Cloner le repo
git clone https://github.com/your-user/dbd-player-insights.git
cd dbd-player-insights

# 2. Setup Python
uv venv && source .venv/bin/activate
uv pip install -e ".[dev,dbt,dashboard]"

# 3. Configurer les variables d'environnement
cp .env.example .env
# Editer .env avec vos credentials

# 4. Provisionner Snowflake + S3
cd terraform && terraform init && terraform apply
cd ..

# 5. Generer des donnees (90 jours, 50k joueurs)
make generate-s3

# 6. Lancer dbt
make dbt-run

# 7. Lancer Airflow
make airflow-up
# UI: http://localhost:8080 (admin/admin)

# 8. Lancer le dashboard
make dashboard
# UI: http://localhost:8501
```

## Deploiement EC2

```bash
cd infra
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
# Editer terraform.tfvars
make deploy  # terraform apply + ansible
```

## Commandes utiles

| Commande | Description |
|---|---|
| `make help` | Liste toutes les commandes |
| `make generate` | Genere 90j de donnees localement |
| `make dbt-run` | seed + run + test |
| `make airflow-up` | Lance Airflow |
| `make dashboard` | Lance Streamlit |
| `make full-pipeline` | Tout d'un coup |
| `make clean` | Reset |
