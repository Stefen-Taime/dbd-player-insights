# DBD Player Insights Platform

Pipeline de données de télémétrie pour Dead by Daylight — du générateur d'événements synthétiques au dashboard de métriques joueurs, en passant par un data warehouse Snowflake orchestré par Airflow.

> **Contexte** : ce projet démontre une maîtrise end-to-end du stack data utilisé par Behaviour Interactive sur Dead by Daylight (Snowflake, dbt, Airflow, Python, AWS S3). Il simule un pipeline de production traitant ~300 Go/jour de télémétrie gaming avec une architecture medallion (Bronze → Silver → Gold).

---

## Stack technique

| Couche | Technologie | Rôle |
|---|---|---|
| Génération | Python 3.11+, Faker | Données synthétiques réalistes DBD |
| Stockage | AWS S3 | Landing zone partitionnée |
| Ingestion | Snowpipe | Auto-ingest S3 → Snowflake |
| Warehouse | Snowflake | Entrepôt de données (trial account OK) |
| Transformation | dbt-core + dbt-snowflake | Modèles medallion + tests + docs |
| Orchestration | Apache Airflow 2.x | DAGs de scheduling et monitoring |
| Dashboard | Streamlit | KPIs joueurs, rétention, revenus |
| Cost monitoring | SQL + Streamlit | Suivi des crédits Snowflake |
| IaC | Terraform (Snowflake provider) | Provisioning reproductible |
| CI/CD | GitHub Actions | Linting, tests dbt, deploy |
| Dev local | Docker Compose | Airflow + Postgres metadata |

---

## Structure du répertoire (~95 fichiers)

```
dbd-player-insights/
│
├── README.md
├── LICENSE
├── Makefile                          # Commandes: make generate, make dbt-run, make deploy...
├── .env.example                      # Variables d'environnement template
├── .gitignore
├── pyproject.toml                    # Python project config (uv/poetry)
│
├── docs/
│   ├── architecture.md               # Diagramme d'architecture détaillé
│   ├── data-dictionary.md            # Dictionnaire des événements DBD
│   ├── snowflake-cost-guide.md       # Guide d'optimisation des coûts
│   └── onboarding.md                 # Guide de démarrage rapide
│
├── generator/                        # 🎮 Générateur de données synthétiques
│   ├── __init__.py
│   ├── config.py                     # Paramètres de simulation (nb joueurs, dates, etc.)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── player.py                 # Profils joueurs (platform, region, MMR, rank)
│   │   ├── match.py                  # Events de match (killer/survivor, perks, score)
│   │   ├── session.py                # Sessions de jeu (login, duration, actions)
│   │   ├── store.py                  # Transactions store (Auric Cells, cosmetics, DLC)
│   │   ├── mmr.py                    # Updates MMR post-match
│   │   └── progression.py            # Bloodpoints, prestige, perk unlocks
│   ├── publishers/
│   │   ├── __init__.py
│   │   ├── s3_publisher.py           # Upload vers S3 (partitionné event_type/yyyy/mm/dd)
│   │   ├── local_publisher.py        # Mode local (fichiers JSON pour dev)
│   │   └── base.py                   # Interface publisher abstraite
│   ├── cli.py                        # CLI: python -m generator --events 100000 --days 90
│   └── tests/
│       ├── test_player.py
│       ├── test_match.py
│       ├── test_store.py
│       └── test_publishers.py
│
├── terraform/                        # 🏗️ Infrastructure as Code
│   ├── main.tf                       # Provider Snowflake + AWS
│   ├── variables.tf
│   ├── outputs.tf
│   ├── snowflake/
│   │   ├── databases.tf              # DBD_RAW, DBD_ANALYTICS
│   │   ├── schemas.tf                # raw, staging, intermediate, marts
│   │   ├── warehouses.tf             # LOADING_WH (XS), TRANSFORM_WH (S), ANALYTICS_WH (S)
│   │   ├── roles.tf                  # LOADER, TRANSFORMER, ANALYST, MONITOR
│   │   ├── stages.tf                 # External stage → S3
│   │   ├── pipes.tf                  # Snowpipe definitions (1 par event type)
│   │   ├── file_formats.tf           # JSON file format
│   │   └── resource_monitors.tf      # Alertes budget crédits
│   └── aws/
│       ├── s3.tf                     # Bucket + lifecycle policies
│       ├── iam.tf                    # Rôle cross-account Snowflake → S3
│       └── sns.tf                    # Notifications S3 → Snowpipe
│
├── dbt/                              # 📊 Transformations dbt
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   ├── packages.yml                  # dbt-utils, dbt-expectations, dbt-date
│   │
│   ├── macros/
│   │   ├── generate_schema_name.sql  # Custom schema naming
│   │   ├── cents_to_dollars.sql      # Conversion monétaire
│   │   ├── date_spine.sql            # Génération de séries de dates
│   │   ├── retention_cohort.sql      # Macro de calcul de cohortes
│   │   └── incremental_filter.sql    # Filtre incrémental réutilisable
│   │
│   ├── models/
│   │   ├── sources.yml               # Sources declaration (RAW_DBD.*)
│   │   │
│   │   ├── staging/                  # ── Silver: nettoyage, typage, dédup ──
│   │   │   ├── _staging__models.yml  # Tests + descriptions
│   │   │   ├── stg_matches.sql       # Parse JSON match events → colonnes typées
│   │   │   ├── stg_sessions.sql      # Parse JSON session events
│   │   │   ├── stg_store_transactions.sql
│   │   │   ├── stg_mmr_updates.sql
│   │   │   ├── stg_players.sql       # Déduplication profils joueurs
│   │   │   └── stg_progression.sql
│   │   │
│   │   ├── intermediate/             # ── Logique métier intermédiaire ──
│   │   │   ├── _intermediate__models.yml
│   │   │   ├── int_match_enriched.sql        # Match + killer/survivor stats + perks
│   │   │   ├── int_player_daily_activity.sql # Activité quotidienne par joueur
│   │   │   ├── int_session_metrics.sql       # Métriques de session (durée, actions/min)
│   │   │   ├── int_revenue_daily.sql         # Revenue quotidien par type
│   │   │   └── int_player_first_last.sql     # Dates first/last seen par joueur
│   │   │
│   │   └── marts/                    # ── Gold: métriques business ──
│   │       ├── _marts__models.yml
│   │       │
│   │       ├── player/
│   │       │   ├── fct_player_retention.sql      # Rétention D1/D7/D30 par cohorte
│   │       │   ├── fct_player_lifetime.sql       # LTV, total sessions, total spend
│   │       │   ├── dim_players.sql               # SCD Type 2 joueurs
│   │       │   └── fct_dau_mau.sql               # DAU/MAU/WAU quotidien
│   │       │
│   │       ├── match/
│   │       │   ├── fct_match_outcomes.sql        # Win rates killer/survivor
│   │       │   ├── fct_perk_performance.sql      # Win rate par perk
│   │       │   ├── fct_map_balance.sql           # Kill rate par map
│   │       │   └── fct_mmr_distribution.sql      # Distribution MMR par segment
│   │       │
│   │       └── revenue/
│   │           ├── fct_daily_revenue.sql         # Revenue journalier
│   │           ├── fct_arpdau.sql                # Average Revenue Per DAU
│   │           └── fct_store_conversion.sql      # Funnel store: view → purchase
│   │
│   ├── seeds/
│   │   ├── seed_killers.csv          # Référentiel des killers DBD (nom, power, chapter)
│   │   ├── seed_survivors.csv        # Référentiel des survivors
│   │   ├── seed_perks.csv            # Référentiel des perks (nom, type, tier)
│   │   ├── seed_maps.csv             # Référentiel des maps (nom, realm, size)
│   │   └── seed_store_items.csv      # Catalogue store (cosmetics, DLC, prix)
│   │
│   ├── snapshots/
│   │   └── snap_player_mmr.sql       # SCD Type 2 sur le MMR joueur
│   │
│   ├── tests/
│   │   ├── assert_positive_revenue.sql
│   │   ├── assert_valid_kill_rate.sql       # Kill rate entre 0 et 1
│   │   └── assert_retention_bounds.sql      # Rétention entre 0% et 100%
│   │
│   └── analyses/
│       ├── snowflake_cost_analysis.sql      # Requêtes de suivi des crédits
│       ├── warehouse_utilization.sql        # Utilisation des warehouses
│       └── query_performance_audit.sql      # Top 20 requêtes les plus coûteuses
│
├── airflow/                          # 🔄 Orchestration
│   ├── docker-compose.yml            # Airflow + Postgres + Redis (CeleryExecutor)
│   ├── Dockerfile                    # Image custom avec dbt + providers
│   ├── requirements.txt
│   ├── dags/
│   │   ├── dbt_daily_run.py          # DAG principal: dbt run + test (schedule: 6h UTC)
│   │   ├── dbt_freshness_check.py    # DAG: source freshness (schedule: toutes les 2h)
│   │   ├── snowflake_cost_monitor.py # DAG: alertes si crédits > seuil (schedule: 8h UTC)
│   │   ├── data_generator_backfill.py # DAG: génération de données historiques
│   │   └── utils/
│   │       ├── dbt_operator.py       # Wrapper BashOperator pour dbt
│   │       ├── slack_alerts.py       # Callbacks d'alerte Slack/email
│   │       └── snowflake_checks.py   # Vérifications de santé Snowflake
│   └── config/
│       └── airflow.cfg.override      # Overrides de config
│
├── dashboard/                        # 📈 Streamlit dashboards
│   ├── app.py                        # Entry point (multi-page)
│   ├── requirements.txt
│   ├── pages/
│   │   ├── 01_player_kpis.py         # DAU/MAU, rétention, LTV
│   │   ├── 02_match_analytics.py     # Kill rates, perk meta, map balance
│   │   ├── 03_revenue.py             # ARPDAU, store conversion, daily rev
│   │   └── 04_cost_monitor.py        # Crédits Snowflake, warehouse perf
│   ├── utils/
│   │   ├── snowflake_conn.py         # Connexion Snowflake (cached)
│   │   └── charts.py                 # Helper Plotly/Altair
│   └── .streamlit/
│       └── config.toml
│
├── quality/                          # ✅ Data quality framework
│   ├── expectations/
│   │   ├── raw_matches.yml           # Freshness SLA: < 1h
│   │   ├── raw_sessions.yml          # Freshness SLA: < 1h
│   │   └── raw_store.yml             # Freshness SLA: < 2h
│   ├── sla_config.yml                # Définitions des SLA par source
│   └── monitors/
│       ├── volume_anomaly.py          # Alerte si volume events < 80% de la moyenne
│       └── schema_drift.py            # Détection de changement de schéma JSON
│
├── scripts/                          # 🛠️ Scripts utilitaires
│   ├── setup_snowflake.sh            # Bootstrap Snowflake (si pas Terraform)
│   ├── seed_s3.sh                    # Upload initial de données vers S3
│   ├── run_full_pipeline.sh          # Exécution complète: generate → upload → dbt
│   └── export_lineage.sh             # Export du lineage graph dbt
│
└── .github/
    └── workflows/
        ├── dbt_ci.yml                # PR: dbt compile + test sur staging
        ├── dbt_deploy.yml            # Merge main: dbt run --target prod
        └── terraform_plan.yml        # PR: terraform plan (infra changes)
```

---

## Architecture du pipeline

```
┌─────────────────────────┐
│  Python Generator       │  Simule la télémétrie DBD:
│  (Faker + game logic)   │  matches, sessions, store, MMR, progression
└───────────┬─────────────┘
            │ JSON (partitioned: event_type/yyyy/mm/dd/hh)
            ▼
┌─────────────────────────┐
│  AWS S3 Landing Zone    │  Bucket: s3://dbd-telemetry-raw/
│  (Lifecycle: 90d → IA)  │  SNS notification on PUT
└───────────┬─────────────┘
            │ Auto-ingest (event notification)
            ▼
┌─────────────────────────────────────────────────────────┐
│  ❄️  Snowflake                                          │
│                                                         │
│  ┌──────────────────┐                                   │
│  │ Snowpipe         │  1 pipe par event_type            │
│  │ (LOADING_WH, XS) │  COPY INTO raw.{table}           │
│  └────────┬─────────┘                                   │
│           ▼                                             │
│  ┌──────────────────┐  Bronze                           │
│  │ RAW_DBD          │  JSON brut, VARIANT column        │
│  │ raw.*            │  + metadata (file, load_ts)       │
│  └────────┬─────────┘                                   │
│           ▼  dbt run (TRANSFORM_WH, S)                  │
│  ┌──────────────────┐  Silver                           │
│  │ STAGING          │  Colonnes typées, dédupliquées    │
│  │ staging.stg_*    │  Tests: not_null, unique, accepted│
│  └────────┬─────────┘                                   │
│           ▼                                             │
│  ┌──────────────────┐                                   │
│  │ INTERMEDIATE     │  Enrichissements, jointures       │
│  │ intermediate.*   │  Logique métier réutilisable      │
│  └────────┬─────────┘                                   │
│           ▼                                             │
│  ┌──────────────────┐  Gold                             │
│  │ MARTS            │  fct_* (facts), dim_* (dimensions)│
│  │ marts.player.*   │  Métriques: DAU, rétention, LTV   │
│  │ marts.match.*    │  Kill rates, perk meta, MMR dist   │
│  │ marts.revenue.*  │  ARPDAU, conversion, daily rev     │
│  └────────┬─────────┘                                   │
│           │  ANALYTICS_WH (S)                           │
└───────────┼─────────────────────────────────────────────┘
            ▼
┌─────────────────────────┐  ┌──────────────────┐
│  Streamlit Dashboard    │  │  dbt Docs        │
│  KPIs, charts, filters  │  │  Lineage + docs  │
└─────────────────────────┘  └──────────────────┘
```

---

## Modèle de données — événements DBD

Le générateur produit 6 types d'événements JSON qui simulent la télémétrie réelle de Dead by Daylight :

### match_completed

```json
{
  "event_type": "match_completed",
  "event_id": "uuid",
  "timestamp": "2025-03-15T14:32:00Z",
  "match_id": "uuid",
  "duration_seconds": 480,
  "map_id": "macmillan_suffocation_pit",
  "game_mode": "public",
  "killer": {
    "player_id": "uuid",
    "character_id": "trapper",
    "perks": ["hex_ruin", "bbq_and_chilli", "pop_goes_the_weasel", "corrupt_intervention"],
    "kills": 3,
    "hooks": 9,
    "score": 28000
  },
  "survivors": [
    {
      "player_id": "uuid",
      "character_id": "meg_thomas",
      "perks": ["sprint_burst", "adrenaline", "iron_will", "borrowed_time"],
      "escaped": false,
      "generators_completed": 2,
      "score": 14500
    }
  ]
}
```

### session_event

```json
{
  "event_type": "session_event",
  "event_id": "uuid",
  "timestamp": "2025-03-15T14:00:00Z",
  "player_id": "uuid",
  "session_id": "uuid",
  "action": "login|logout|queue_join|match_start|match_end|store_visit",
  "platform": "steam|ps5|xbox|switch|epic",
  "region": "us-east-1|eu-west-1|ap-northeast-1",
  "client_version": "8.4.0"
}
```

### store_transaction

```json
{
  "event_type": "store_transaction",
  "event_id": "uuid",
  "timestamp": "2025-03-15T14:45:00Z",
  "player_id": "uuid",
  "transaction_id": "uuid",
  "item_id": "cosmetic_trapper_mask_04",
  "item_type": "cosmetic|dlc|rift_pass|auric_cells",
  "currency": "auric_cells|iridescent_shards|usd",
  "amount": 500,
  "amount_usd": 4.99
}
```

### mmr_update, player_registration, progression_event

Événements complémentaires pour le MMR post-match, l'inscription de nouveaux joueurs, et la progression (bloodpoints, prestige, perk unlocks).

---

## Métriques clés (marts dbt)

### Joueurs (marts.player.*)

| Métrique | Modèle dbt | Description |
|---|---|---|
| DAU / MAU / WAU | `fct_dau_mau` | Joueurs actifs quotidiens, hebdomadaires, mensuels |
| Stickiness | `fct_dau_mau` | DAU/MAU ratio |
| Rétention D1/D7/D30 | `fct_player_retention` | % joueurs revenant après N jours (par cohorte) |
| LTV | `fct_player_lifetime` | Lifetime value par joueur (spend total + sessions) |
| Churn risk | `fct_player_lifetime` | Jours depuis dernière session |

### Matches (marts.match.*)

| Métrique | Modèle dbt | Description |
|---|---|---|
| Kill rate par killer | `fct_match_outcomes` | % kills moyen par personnage killer |
| Escape rate | `fct_match_outcomes` | % survivors échappés |
| Perk win rate | `fct_perk_performance` | Taux de victoire par perk (killer et survivor) |
| Map balance | `fct_map_balance` | Kill rate par map (< 50% = survivor-sided) |
| MMR distribution | `fct_mmr_distribution` | Histogram MMR par segment (new/casual/core/hardcore) |

### Revenus (marts.revenue.*)

| Métrique | Modèle dbt | Description |
|---|---|---|
| Daily revenue | `fct_daily_revenue` | Revenue total par jour, par type de transaction |
| ARPDAU | `fct_arpdau` | Average Revenue Per Daily Active User |
| Store conversion | `fct_store_conversion` | Funnel: session → store visit → purchase |

---

## Monitoring des coûts Snowflake

L'offre mentionne explicitement le cost monitoring comme responsabilité clé. Le projet inclut :

**Requêtes d'analyse** (`dbt/analyses/`) :
- `snowflake_cost_analysis.sql` — Consommation de crédits par warehouse, par jour, avec trend 7j
- `warehouse_utilization.sql` — Ratio utilisation/idle time par warehouse
- `query_performance_audit.sql` — Top 20 requêtes par temps d'exécution et bytes scannés

**DAG Airflow** (`airflow/dags/snowflake_cost_monitor.py`) :
- Schedule quotidien à 8h UTC
- Alertes si consommation > 80% du budget mensuel
- Alertes si une requête scanne > 1 To de données
- Report hebdomadaire envoyé par email/Slack

**Dashboard Streamlit** (`dashboard/pages/04_cost_monitor.py`) :
- Crédits consommés (quotidien + cumulatif mensuel)
- Breakdown par warehouse (LOADING_WH, TRANSFORM_WH, ANALYTICS_WH)
- Top requêtes coûteuses avec lien vers query history
- Recommandations automatiques (auto-suspend, warehouse sizing)

---

## Qualité des données

### Tests dbt intégrés

Chaque modèle staging a des tests dans `_staging__models.yml` :
- `not_null` sur les colonnes critiques (event_id, player_id, timestamp)
- `unique` sur event_id (après déduplication)
- `accepted_values` sur les enums (platform, game_mode, action)
- `relationships` entre tables (player_id existe dans stg_players)

### Tests custom

- `assert_positive_revenue.sql` — Revenue >= 0 sur toutes les transactions
- `assert_valid_kill_rate.sql` — Kill rate entre 0.0 et 1.0
- `assert_retention_bounds.sql` — Rétention entre 0% et 100%

### Freshness SLA

Définis dans `quality/sla_config.yml` et vérifiés par le DAG `dbt_freshness_check.py` :
- `raw_matches` — Fraîcheur < 1h (warn), < 2h (error)
- `raw_sessions` — Fraîcheur < 1h (warn), < 2h (error)
- `raw_store` — Fraîcheur < 2h (warn), < 4h (error)

### Monitors custom

- `volume_anomaly.py` — Alerte si le volume d'événements dans les 6 dernières heures est < 80% de la moyenne mobile 7j (détection de panne d'ingestion)
- `schema_drift.py` — Compare les clés JSON du dernier batch avec le schéma attendu, alerte si nouvelles clés ou clés manquantes

---

## Démarrage rapide

### Prérequis

- Python 3.11+
- Docker & Docker Compose
- Compte AWS (ou LocalStack pour dev)
- Compte Snowflake (trial 30 jours gratuit : signup.snowflake.com)
- Terraform 1.5+

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/taime/dbd-player-insights.git
cd dbd-player-insights

# 2. Setup Python (uv recommandé)
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Copier et configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos credentials Snowflake + AWS

# 4. Provisionner l'infrastructure Snowflake
cd terraform && terraform init && terraform apply
cd ..

# 5. Générer des données synthétiques (90 jours, 50k joueurs)
python -m generator --players 50000 --days 90 --target s3

# 6. Vérifier l'ingestion Snowpipe
# (les données apparaissent dans RAW_DBD.* en ~1-2 min)

# 7. Installer dbt et lancer les transformations
cd dbt
dbt deps
dbt seed          # Charge les référentiels (killers, maps, perks)
dbt run           # Lance tous les modèles
dbt test          # Exécute tous les tests
dbt docs generate # Génère la documentation + lineage graph
dbt docs serve    # Ouvre le navigateur sur localhost:8080
cd ..

# 8. Lancer Airflow (Docker Compose)
cd airflow
docker compose up -d
# UI: http://localhost:8080 (admin/admin)
cd ..

# 9. Lancer le dashboard Streamlit
cd dashboard
streamlit run app.py
# UI: http://localhost:8501
```

### Raccourcis Makefile

```bash
make generate      # Génère 90 jours de données
make upload        # Upload vers S3
make dbt-run       # dbt seed + run + test
make dbt-docs      # Génère et sert la doc dbt
make airflow-up    # Lance Airflow
make dashboard     # Lance Streamlit
make full-pipeline # Tout d'un coup
make clean         # Reset des données locales
```

---

## CI/CD (GitHub Actions)

### dbt_ci.yml (sur chaque PR)

1. Checkout + setup Python + dbt
2. `dbt compile` — Vérifie la syntaxe SQL
3. `dbt test` sur un schéma de staging dédié (PR-123)
4. Commentaire automatique sur la PR avec le résultat des tests

### dbt_deploy.yml (merge sur main)

1. `dbt run --target prod` — Applique les changements en production
2. `dbt test --target prod` — Vérifie les résultats
3. `dbt docs generate` — Met à jour la documentation

### terraform_plan.yml (sur PR touchant terraform/)

1. `terraform plan` — Affiche les changements d'infrastructure
2. Commentaire sur la PR avec le plan

---

## Points de discussion en entrevue

Ce projet est conçu pour alimenter des discussions techniques lors d'une entrevue chez Behaviour Interactive. Voici les angles à préparer :

**Choix de modélisation dbt** — Pourquoi des modèles incrementaux pour stg_matches mais des views pour stg_players ? Comment gérer les late-arriving events ? Pourquoi séparer intermediate et marts ?

**Optimisation Snowflake** — Comment choisir les clustering keys pour fct_player_retention ? Pourquoi 3 warehouses séparés (loading, transform, analytics) ? Comment réduire les coûts de 30% sans impacter les SLA ?

**Qualité des données** — Comment détecter un bug dans le client de jeu qui envoie des events malformés ? Que se passe-t-il si Snowpipe a un retard de 4h ? Comment gérer le schema evolution quand une nouvelle saison ajoute des champs ?

**Scale** — Ce POC simule ~50k joueurs. DBD en a 60M+. Quels changements architecturaux pour 1000x le volume ? (Partitioning strategy, micro-batch vs streaming, warehouse auto-scaling)

**Game-specific** — Comment le MMR influence la rétention ? Pourquoi le kill rate par map est une métrique d'équilibrage critique ? Comment détecter les joueurs qui désinstallent vs ceux qui font une pause ?

---

## Licence

MIT — Projet portfolio personnel. Dead by Daylight est une marque de Behaviour Interactive Inc. Ce projet utilise des données entièrement synthétiques et n'est pas affilié à Behaviour Interactive.
