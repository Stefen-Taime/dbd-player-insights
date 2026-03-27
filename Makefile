# =============================================================================
# dbd-player-insights — project-level Makefile
# =============================================================================

.PHONY: help install generate upload dbt-run dbt-test dbt-docs \
        airflow-up airflow-down grafana-up grafana-down grafana-logs \
        dashboard full-pipeline clean

SHELL := /bin/bash

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# --- Setup ------------------------------------------------------------------
install: ## Install Python dependencies
	uv venv && source .venv/bin/activate && uv pip install -e ".[dev,dbt,dashboard]"

# --- Generator --------------------------------------------------------------
generate: ## Generate 90 days of synthetic data (50k players)
	python -m generator --players 50000 --days 90 --target local

generate-s3: ## Generate and upload directly to S3
	python -m generator --players 50000 --days 90 --target s3

upload: ## Upload local data to S3
	bash scripts/seed_s3.sh

# --- dbt --------------------------------------------------------------------
dbt-deps: ## Install dbt packages
	cd dbt && dbt deps

dbt-seed: ## Load seed data
	cd dbt && dbt seed

dbt-run: ## Run dbt: seed + run + test
	cd dbt && dbt deps && dbt seed && dbt run && dbt test

dbt-test: ## Run dbt tests only
	cd dbt && dbt test

dbt-docs: ## Generate and serve dbt docs
	cd dbt && dbt docs generate && dbt docs serve

dbt-freshness: ## Check source freshness
	cd dbt && dbt source freshness

# --- Airflow ----------------------------------------------------------------
airflow-up: ## Start Airflow (Docker Compose)
	cd airflow && docker compose up -d

airflow-down: ## Stop Airflow
	cd airflow && docker compose down

airflow-logs: ## Tail Airflow logs
	cd airflow && docker compose logs -f

# --- Grafana ----------------------------------------------------------------
grafana-up: ## Start Grafana (Docker Compose)
	cd grafana && docker compose up -d

grafana-down: ## Stop Grafana
	cd grafana && docker compose down

grafana-logs: ## Tail Grafana logs
	cd grafana && docker compose logs -f

# --- Dashboard (Streamlit) -------------------------------------------------
dashboard: ## Start Streamlit dashboard
	cd dashboard && streamlit run app.py

# --- Full Pipeline ----------------------------------------------------------
full-pipeline: ## Run complete pipeline: generate -> upload -> dbt
	bash scripts/run_full_pipeline.sh

# --- Quality ----------------------------------------------------------------
quality-volume: ## Run volume anomaly check
	python quality/monitors/volume_anomaly.py

quality-schema: ## Run schema drift check
	python quality/monitors/schema_drift.py

# --- Cleanup ----------------------------------------------------------------
clean: ## Reset local data and build artifacts
	rm -rf data/output dbt/target dbt/dbt_packages dbt/logs
	cd airflow && docker compose down -v 2>/dev/null || true
	cd grafana && docker compose down -v 2>/dev/null || true
