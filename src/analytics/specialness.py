"""
Specialness risk scoring.
Produces a 0-100 score per bond reflecting its risk of becoming special
on the repo market, based on free float scarcity, issue size, age,
and maturity bucket.

Inputs: data/processed/free_float.parquet, data/raw/bond_reference.csv
Output: data/processed/specialness_score.parquet
"""

from pathlib import Path
import pandas as pd
from src.analytics.free_float import load_free_float
from src.utils.bond_reference import load_reference


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "data" / "processed" / "specialness_score.parquet"

WEIGHTS = {
    "free_float": 0.40,
    "size": 0.20,
    "age": 0.25,
    "maturity_bucket": 0.15,
}

MATURITY_BUCKET_SCORES = {
    "0-2Y": 60,    
    "2-5Y": 85,    
    "5-10Y": 100,  
    "10Y+": 40,
}


def _score_free_float(free_float_pct):

    raw = (100 - free_float_pct) / 60 * 100

    return raw.clip(lower=0, upper=100).round(1)


def _score_size(outstanding_eur_bn):

    benchmark_size = 50.0
    raw = (1 - outstanding_eur_bn / benchmark_size) * 100

    return raw.clip(lower=0, upper=100).round(1)


def _score_age(years_since_issue):

    raw = (1 - years_since_issue / 5) * 100

    return raw.clip(lower=0, upper=100).round(1)


def _score_maturity_bucket(bucket_series):

    return bucket_series.map(MATURITY_BUCKET_SCORES).fillna(50)


def build_specialness_score():

    """Compute the specialness risk score for each bond in the reference"""

    reference = load_reference()
    free_float = load_free_float()

    df = reference.merge(
        free_float[["isin", "free_float_pct", "free_float_eur_bn"]],
        on="isin",
        how="left",
    )
    
    df["free_float_pct"] = df["free_float_pct"].fillna(90.0)

    df["years_since_issue"] = (
        (pd.Timestamp.today() - df["issue_date"]).dt.days / 365.25
    ).round(2)

    df["score_free_float"] = _score_free_float(df["free_float_pct"])
    df["score_size"] = _score_size(df["outstanding_eur_bn"])
    df["score_age"] = _score_age(df["years_since_issue"])
    df["score_maturity"] = _score_maturity_bucket(df["maturity_bucket"])

    df["specialness_score"] = (
        WEIGHTS["free_float"] * df["score_free_float"]
        + WEIGHTS["size"] * df["score_size"]
        + WEIGHTS["age"] * df["score_age"]
        + WEIGHTS["maturity_bucket"] * df["score_maturity"]
    ).round(1)

    df["risk_tier"] = pd.cut(
        df["specialness_score"],
        bins=[0, 30, 60, 80, 100],
        labels=["Low", "Moderate", "High", "Very High"],
        include_lowest=True,
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    return df


def load_specialness_score():

    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {OUTPUT_PATH}"
        )
    
    return pd.read_parquet(OUTPUT_PATH)

