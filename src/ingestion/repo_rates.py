"""
Repo rates ingestion.
Cleans €STR and DFR raw CSVs, aligns them on a single daily time series,
and computes the €STR-DFR spread as a proxy for money market tension.

Sources: data/raw/estr_rates.csv, data/raw/dfr_rates.csv
Output: data/processed/repo_rates.parquet
"""

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ESTR_RAW = ROOT / "data" / "raw" / "estr_rates.csv"
DFR_RAW = ROOT / "data" / "raw" / "dfr_rates.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "repo_rates.parquet"


def _load_and_clean_ecb_csv(path, value_name):

    """Load a raw ECB SDMX CSV and return a clean DataFrame: date, value"""

    df = pd.read_csv(path, usecols=["TIME_PERIOD", "OBS_VALUE"])
    df = df.rename(columns={"TIME_PERIOD": "date", "OBS_VALUE": value_name})
    df["date"] = pd.to_datetime(df["date"])
    df[value_name] = pd.to_numeric(df[value_name], errors="coerce")
    df = df.dropna().sort_values("date").reset_index(drop=True)
    return df


def _align_dfr_to_estr(estr, dfr):

    """Forward-fill the DFR on each €STR date"""

    merged = estr.merge(dfr, on="date", how="left")
    merged["dfr"] = merged["dfr"].ffill()
    return merged


def build_repo_rates():

    """Build the repo rates dataset and save to Parquet"""

    estr = _load_and_clean_ecb_csv(ESTR_RAW, value_name="estr")
    dfr = _load_and_clean_ecb_csv(DFR_RAW, value_name="dfr")

    df = _align_dfr_to_estr(estr, dfr)

    df = df.dropna().reset_index(drop=True)

    df["estr_dfr_spread_bp"] = ((df["estr"] - df["dfr"]) * 100).round(2)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    return df


def load_repo_rates():

    """Load the pre-built repo rates dataset"""

    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {OUTPUT_PATH}"
        )
    return pd.read_parquet(OUTPUT_PATH)


if __name__ == "__main__":
    df = build_repo_rates()

    print(f"\nDate range: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"Rows: {len(df)}")
    print("\nLatest 10 observations:")
    print(df.tail(10).to_string(index=False))
    print("\nSpread summary (bp):")
    print(df["estr_dfr_spread_bp"].describe().round(2))