"""
CBPP3 (Covered Bond Purchase Programme) holdings ingestion.
The ECB only publishes aggregated CBPP3 holdings (no per-country breakdown).
We estimate per-country holdings using public market share data
(ECBC Covered Bond Fact Book references).

Sources:
    data/raw/ecb_cbpp3_holdings.csv     — Aggregated CBPP3 holdings (ECB)
    data/raw/covered_market_shares.csv  — Country shares of EUR Covered market
Output:
    data/processed/cbpp3_holdings.parquet
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CBPP3_RAW = ROOT / "data" / "raw" / "ecb_cbpp3_holdings.csv"
SHARES_RAW = ROOT / "data" / "raw" / "covered_market_shares.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "cbpp3_holdings.parquet"


def _load_cbpp3_total():
    """Load aggregated CBPP3 holdings, return clean DataFrame: date, total_eur_m."""
    df = pd.read_csv(CBPP3_RAW, skiprows=1)

    df = df.rename(columns={"End of Month": "date", "Total holdings": "total_eur_m"})
    df = df[["date", "total_eur_m"]]

    df = df[df["date"].astype(str).str.match(r"^[A-Za-z]{3}-\d{2}$")].copy()

    df["total_eur_m"] = pd.to_numeric(
        df["total_eur_m"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce",
    )

    df["date"] = pd.to_datetime(df["date"], format="%b-%y")
    df["date"] = df["date"] + pd.offsets.MonthEnd(0)

    return df.dropna().reset_index(drop=True)


def _load_market_shares():
    """Load country shares of the EUR Covered market."""
    return pd.read_csv(SHARES_RAW)


def build_cbpp3_dataset():
    """Estimate per-country CBPP3 holdings via market share allocation."""
    totals = _load_cbpp3_total()
    shares = _load_market_shares()

    totals["key"] = 1
    shares["key"] = 1
    df = totals.merge(shares, on="key").drop(columns="key")

    df["holdings_eur_m"] = (df["total_eur_m"] * df["covered_market_share"]).round(0)
    df["holdings_eur_bn"] = (df["holdings_eur_m"] / 1000).round(2)
    df["programme"] = "CBPP3"

    result = df[["date", "country", "programme", "holdings_eur_bn"]].copy()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(OUTPUT_PATH, index=False)

    return result


def load_cbpp3():
    """Load the pre-built CBPP3 holdings dataset."""
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {OUTPUT_PATH}. Run build_cbpp3_dataset() first."
        )
    return pd.read_parquet(OUTPUT_PATH)

