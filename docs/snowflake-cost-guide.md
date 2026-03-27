# Guide d'optimisation des couts Snowflake

## Warehouses

| Warehouse | Taille | Auto-suspend | Usage |
|---|---|---|---|
| LOADING_WH | XSMALL | 60s | Snowpipe COPY INTO |
| TRANSFORM_WH | SMALL | 120s | dbt run, dbt test |
| ANALYTICS_WH | SMALL | 300s | Dashboards, queries ad-hoc |

## Strategies de reduction des couts

### 1. Auto-suspend agressif
Le loading warehouse devrait se suspendre apres 60s car Snowpipe ne l'utilise que brievement.

### 2. Modeles incrementaux dbt
Les tables de staging volumineuses (matches, sessions) utilisent `materialized='incremental'` avec `merge` strategy pour ne traiter que les nouvelles donnees.

### 3. Clustering keys
Ajouter des clustering keys sur `event_timestamp::date` pour les tables incrementales — ameliore le partition pruning.

### 4. Resource Monitor
Le monitor mensuel alerte a 80%, 90%, 100% et suspend a 100% des credits. Configure dans `terraform/snowflake/resource_monitors.tf`.

### 5. Monitoring quotidien
Le DAG `snowflake_cost_monitor` (8h UTC) verifie :
- Consommation credits vs budget mensuel
- Requetes scannant > 1 TB de donnees
- Rapport hebdomadaire Slack

### 6. Requetes d'analyse
Voir `dbt/analyses/` :
- `snowflake_cost_analysis.sql` : credits par warehouse par jour
- `warehouse_utilization.sql` : ratio utilisation/idle
- `query_performance_audit.sql` : top 20 requetes couteuses
