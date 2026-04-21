# EUR Repo Collateral Monitor

The Eurosystem holds over €4tn of EUR sovereign and Covered bonds through its APP and PEPP programmes. The larger the share of a country's debt held by the ECB, the smaller the free float available for repo, and the more likely specific bonds are to trade special. This project quantifies the link between Eurosystem holdings and bond-level specialness across the EUR sovereign and Covered universe, and exposes the results in an interactive dashboard.

Germany is the most striking case. the Eurosystem still holds more than 40% of marketable Bunds, which structurally compresses free float and explains why German sovereigns dominate the high-risk segment of the dashboard. France sits closer to 25%, Italy and Spain in between, and the Covered market follows yet another pattern with the ECB holding roughly 18% of Pfandbriefe, 16% of French Obligations Foncières and over 20% of Spanish Cédulas. The same QT episode does not unwind the same way across countries.

The €STR-DFR spread is used as a proxy for collateral scarcity. €STR normally trades a few basis points below the DFR because non-bank participants like money market funds and supranationals lend at rates below the ECB facility. When the spread becomes structurally more negative, cash holders are accepting lower rates because they want collateral. The dashboard tracks the rolling z-score of this spread against its one-year history and classifies each trading day into a regime ranging from normal to collateral scarcity.

The bond-level specialness score combines four drivers: free float compression, issue size, age since issuance (on-the-run bonds attract benchmark demand), and maturity bucket sensitivity (CTD zones for Bund futures). Recently issued German Bunds in the 5-10Y zone consistently top the ranking. French Obligations appear in the high tier driven by free float compression. Spanish Cédulas score elevated despite a higher free float because small issue sizes amplify their fragility. The weights are exposed as live sliders, and a QT shock simulator recomputes the entire ranking under arbitrary run-off scenarios.

## Project structure

```
Repo_Specialness_Monitor/
├── app/
│   ├── Home.py                    # Streamlit entry point + horizontal navigation
│   └── sections/                  # Macro Overview, Repo Tension, Specialness
├── src/
│   ├── ingestion/
│   │   ├── ecb_holdings.py        # PSPP + PEPP cleaning and aggregation
│   │   ├── cbpp3_holdings.py      # CBPP3 with country allocation via market shares
│   │   ├── repo_rates.py          # €STR + DFR alignment and spread computation
│   │   └── download_ecb_rates.py  # ECB Data Portal API fetcher
│   ├── analytics/
│   │   ├── free_float.py          # Per-bond free float estimation
│   │   ├── tension_signals.py     # Z-score regime classifier
│   │   └── specialness.py         # Composite scoring and tier classification
│   └── utils/
│       └── bond_reference.py      # Bond reference loader and filters
├── data/
    ├── raw/                       # Raw ECB CSVs, bond reference, market shares
    └── processed/                 # Pre-computed Parquet files
```

## Quick start

uv sync

uv run streamlit run app/Home.py

Live dashboard: https://repo-specialness-monitor.streamlit.app