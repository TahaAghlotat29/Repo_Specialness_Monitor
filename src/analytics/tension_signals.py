"""
Money market tension signals.
Computes rolling metrics and regime classification from repo rates
to identify periods of collateral scarcity and funding stress.

Input: data/processed/repo_rates.parquet
Output: data/processed/tension_signals.parquet
"""

from pathlib import Path
import pandas as pd
from src.ingestion.repo_rates import load_repo_rates


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "data" / "processed" / "tension_signals.parquet"
MA_WINDOW = 30
ZSCORE_WINDOW = 252  


def _classify_regime(z):

    """Assign a regime label based on the z-score of the spread"""

    if pd.isna(z):
        return "Insufficient history"
    if z < -2:
        return "Collateral scarcity"
    if z < -1:
        return "Mild tension"
    if z < 1:
        return "Normal"
    if z < 2:
        return "Mild funding stress"
    return "Funding stress"


def build_tension_signals():

    """Build the tension signals dataset and save to Parquet"""

    df = load_repo_rates().copy()

    df["spread_ma30"] = df["estr_dfr_spread_bp"].rolling(
        window=MA_WINDOW, min_periods=MA_WINDOW
    ).mean().round(2)

    rolling_mean = df["estr_dfr_spread_bp"].rolling(
        window=ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW
    ).mean()
    rolling_std = df["estr_dfr_spread_bp"].rolling(
        window=ZSCORE_WINDOW, min_periods=ZSCORE_WINDOW
    ).std()
    df["spread_zscore_1y"] = (
        (df["estr_dfr_spread_bp"] - rolling_mean) / rolling_std
    ).round(2)

    df["regime"] = df["spread_zscore_1y"].apply(_classify_regime)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved {len(df)} rows to {OUTPUT_PATH}")
    return df


def load_tension_signals():

    """Load the pre-built tension signals dataset"""

    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {OUTPUT_PATH}"
        )
    return pd.read_parquet(OUTPUT_PATH)

