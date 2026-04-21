"""
Free float computation.
Estimates the share of each bond held by the Eurosystem and the remaining
tradeable free float, by applying the national ECB holdings ratio to each bond.

- For Sovereigns / SSA  : uses PSPP + PEPP holdings vs total sovereign debt
- For Covered bonds     : uses CBPP3 holdings vs total Covered market

Inputs:
    data/processed/ecb_holdings.parquet   (PSPP + PEPP)
    data/processed/cbpp3_holdings.parquet (CBPP3 estimated by country)
    data/raw/country_debt.csv             (total sovereign debt per country)
    data/raw/covered_market_size.csv      (total Covered market per country)
    data/raw/bond_reference.csv           (bond reference)
Output:
    data/processed/free_float.parquet

"""

from pathlib import Path

import pandas as pd

from src.ingestion.cbpp3_holdings import load_cbpp3
from src.ingestion.ecb_holdings import load_holdings
from src.utils.bond_reference import load_reference


ROOT = Path(__file__).resolve().parents[2]
COUNTRY_DEBT_PATH = ROOT / "data" / "raw" / "country_debt.csv"
COVERED_MARKET_PATH = ROOT / "data" / "raw" / "covered_market_size.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "free_float.parquet"


def _load_country_debt():
    """Load country-level total sovereign debt."""
    return pd.read_csv(COUNTRY_DEBT_PATH)


def _load_covered_market():

    """Load country-level total Covered market size."""

    return pd.read_csv(COVERED_MARKET_PATH)


def _compute_sovereign_ratios(as_of_date=None):

    """For each country, compute the share of sovereign debt held by Eurosystem (PSPP + PEPP)."""

    holdings = load_holdings()

    if as_of_date is None:
        as_of_date = holdings["date"].max()

    snapshot = (
        holdings[holdings["date"] == as_of_date]
        .groupby("country", as_index=False)["holdings_eur_bn"]
        .sum()
        .rename(columns={"holdings_eur_bn": "ecb_holdings_eur_bn"})
    )

    debt = _load_country_debt()
    merged = snapshot.merge(debt, on="country", how="inner")

    merged["ecb_holding_ratio"] = (
        merged["ecb_holdings_eur_bn"] / merged["total_debt_eur_bn"]
    ).round(4)

    merged["as_of_date"] = as_of_date

    return merged[["country_code", "ecb_holding_ratio", "as_of_date"]]


def _compute_covered_ratios(as_of_date=None):

    """For each country, compute the share of Covered market held by Eurosystem (CBPP3)."""

    cbpp3 = load_cbpp3()

    if as_of_date is None:
        as_of_date = cbpp3["date"].max()

    snapshot = (
        cbpp3[cbpp3["date"] == as_of_date]
        .groupby("country", as_index=False)["holdings_eur_bn"]
        .sum()
        .rename(columns={"holdings_eur_bn": "ecb_holdings_eur_bn"})
    )

    market = _load_covered_market()
    merged = snapshot.merge(market, on="country", how="inner")
    merged["ecb_holding_ratio"] = (
        merged["ecb_holdings_eur_bn"] / merged["total_covered_eur_bn"]
    ).round(4)
    merged["as_of_date"] = as_of_date

    return merged[["country_code", "ecb_holding_ratio", "as_of_date"]]



def build_free_float():

    reference = load_reference()
    sovereign_ratios = _compute_sovereign_ratios()
    covered_ratios = _compute_covered_ratios()

    sovereigns = reference[reference["issuer_type"] == "Sovereign"].copy()
    covered = reference[reference["issuer_type"] == "Covered"].copy()

    df_sov = sovereigns.merge(
        sovereign_ratios,
        left_on="country",
        right_on="country_code",
        how="inner",
    )

    df_cov = covered.merge(
        covered_ratios,
        left_on="country",
        right_on="country_code",
        how="inner",
    )

    df = pd.concat([df_sov, df_cov], ignore_index=True)

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
            "issuer_type",
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
    
    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {OUTPUT_PATH}. Run build_free_float() first."
        )
    

    return pd.read_parquet(OUTPUT_PATH)

