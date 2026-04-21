# Repo Specialness Monitor

**Tracking ECB Quantitative Tightening effects on EUR sovereign repo markets.**

An analytical dashboard built to monitor the impact of ECB's Quantitative Tightening
on free float, money market tension, and bond-level specialness risk across the EUR
sovereign and SSA repo universe.

## Features

- **Macro Overview** — Eurosystem holdings trajectory (APP / PEPP) and country breakdown.
- **Repo Tension Monitor** — €STR vs ECB Deposit Facility Rate, regime classification, historical stress episodes.
- **Specialness Screener** — Bond-by-bond risk scoring with adjustable weights, QT scenario simulator, and side-by-side bond comparator.

## Data sources

- ECB Asset Purchase Programme (PSPP) and PEPP holdings
- ECB €STR and Deposit Facility Rate
- Bond reference data from national treasuries (Finanzagentur, AFT, etc.)

## Methodology

Specialness scoring combines four factors via a weighted composite:
- Free float scarcity 
- Issue size 
- Age since issuance 
- Maturity bucket sensitivity 

Weights are adjustable directly in the dashboard sidebar.

## Running locally

\`\`\`bash
uv sync
uv run streamlit run app/Home.py
\`\`\`

## Live demo

[Link to deployed dashboard](https://repo-specialness-monitor.streamlit.app/)

---
