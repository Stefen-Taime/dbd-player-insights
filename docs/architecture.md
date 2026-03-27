# Architecture

## Vue d'ensemble

```
                         ┌──────────────────────┐
                         │  Python Generator     │
                         │  (Faker + game logic)  │
                         └──────────┬─────────────┘
                                    │ JSON partitioned
                                    ▼
                         ┌──────────────────────┐
                         │  AWS S3              │
                         │  dbd-telemetry-raw/  │
                         └──────────┬───────────┘
                                    │ SNS → Snowpipe
                                    ▼
┌───────────────────────────────────────────────────────────────┐
│  Snowflake                                                     │
│  ┌─────────┐   ┌──────────┐   ┌──────────────┐   ┌────────┐  │
│  │ RAW     │──>│ STAGING  │──>│ INTERMEDIATE │──>│ MARTS  │  │
│  │ (Bronze)│   │ (Silver) │   │              │   │ (Gold) │  │
│  └─────────┘   └──────────┘   └──────────────┘   └────┬───┘  │
│   Snowpipe       dbt views    dbt views           dbt tables  │
└──────────────────────────────────────────────────────────┼─────┘
                                                           │
                    ┌──────────────────────────────────────┤
                    ▼                                      ▼
          ┌─────────────────┐                    ┌─────────────────┐
          │  Streamlit      │                    │  Grafana        │
          │  (KPIs, charts) │                    │  (dashboards)   │
          └─────────────────┘                    └─────────────────┘
```

## Infrastructure (2 EC2)

- **ec2-orchestration** (t3a.large) : Airflow 3.x + dbt + CloudWatch + Slack alerts
- **ec2-bi** (t3a.large) : Grafana + Streamlit + Nginx reverse proxy

## Flux de donnees

1. Generator produit des events JSON (match, session, store, MMR, registration, progression)
2. Upload vers S3 partitionne par `event_type/yyyy/mm/dd/hh`
3. SNS notifie Snowpipe -> COPY INTO tables RAW
4. Airflow orchestre dbt : staging -> intermediate -> marts
5. Streamlit/Grafana requetent les marts pour les dashboards
