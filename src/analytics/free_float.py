"""
Free float computation.
Estimates the share of each bond held by the Eurosystem and the remaining
tradeable free float, by applying the national ECB holdings ratio to each bond.

Method: for each country, compute the ratio of total ECB holdings (PSPP + PEPP)
to total sovereign debt, then apply that ratio proportionally to each bond.
"""

from pathlib import Path
import pandas as pd
from src.ingestion.ecb_holdings import load_holdings
from src.utils.bond_reference import load_reference


ROOT = Path(__file__).resolve().parents[2]
COUNTRY_DEBT_PATH = ROOT / "data" / "raw" / "country_debt.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "free_float.parquet"


def _load_country_debt():

    """Load the country-level total sovereign debt reference."""

    return pd.read_csv(COUNTRY_DEBT_PATH)


def _compute_country_ratios(as_of_date=None):

    """Compute, for each country, the share of its debt held by the Eurosystem"""

    holdings = load_holdings()

    if as_of_date is None:
        as_of_date = holdings["date"].max()

    snapshot = (
        holdings[holdings["date"] == as_of_date]
        .groupby("country", as_index=False)["holdings_eur_bn"]
        .sum()
        .rename(columns={"holdings_eur_bn": "ecb_total_holdings_eur_bn"})
    )

    debt = _load_country_debt()
    merged = snapshot.merge(debt, on="country", how="inner")

    merged["ecb_holding_ratio"] = (
        merged["ecb_total_holdings_eur_bn"] / merged["total_debt_eur_bn"]
    ).round(4)

    merged["as_of_date"] = as_of_date
    return merged


def build_free_float(as_of_date=None):

    """Compute free float per bond and save to Parquet"""

    ratios = _compute_country_ratios(as_of_date)
    reference = load_reference()

    sovereigns = reference[reference["issuer_type"] == "Sovereign"].copy()

    df = sovereigns.merge(
        ratios[["country_code", "ecb_holding_ratio", "as_of_date"]],
        left_on="country",
        right_on="country_code",
        how="inner",
    )

    df["ecb_holding_eur_bn"] = (
        df["outstanding_eur_bn"] * df["ecb_holding_ratio"]
    ).round(2)
    df["free_float_eur_bn"] = (
        df["outstanding_eur_bn"] - df["ecb_holding_eur_bn"]
    ).round(2)
    df["free_float_pct"] = (
        df["free_float_eur_bn"] / df["outstanding_eur_bn"] * 100
    ).round(1)

    result = df[
        [
            "isin",
            "issuer",
            "country",
            "maturity_date",
            "outstanding_eur_bn",
            "ecb_holding_ratio",
            "ecb_holding_eur_bn",
            "free_float_eur_bn",
            "free_float_pct",
            "as_of_date",
        ]
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(OUTPUT_PATH, index=False)

    return result


def load_free_float():

    """Load the pre-built free float dataset."""

    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {OUTPUT_PATH}. Run build_free_float() first."
        )
    return pd.read_parquet(OUTPUT_PATH)
