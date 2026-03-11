# Salesforce Pipeline Health Report (Automated)

## Overview
Automated weekly-style pipeline health reporting from Salesforce:
- Extract Opportunities + Accounts via Salesforce REST API (OAuth refresh token)
- Compute pipeline health KPIs and identify stalled opportunities
- Generate an exec-ready PDF report

## Outputs
- `data/raw/opportunities.csv`, `data/raw/accounts.csv` (local only; not committed)
- `data/processed/*.csv` (local only; not committed)
- `reports/pipeline_health_report.pdf` (sample report output in repo)

## KPIs
- Open pipeline amount & open opp count
- Win rate (closed deals)
- Avg days to close (Closed Won)
- Median days open (open opps)
- Stalled deals (stage-based thresholds using days since last modified)

## Setup
1) Create `.env` based on `.env.example`:
