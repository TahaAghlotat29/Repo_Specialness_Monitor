"""
ECB holdings ingestion.
Loads PSPP and PEPP monthly data, computes cumulative holdings per country.
Sources: data/raw/ecb_pspp_holdings.csv, data/raw/ecb_pepp_holdings.csv
Output: data/processed/ecb_holdings.parquet
"""


from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PSPP_RAW = ROOT / "data" / "raw" / "ecb_pspp_holdings.csv"
PEPP_RAW = ROOT / "data" / "raw" / "ecb_pepp_holdings.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "ecb_holdings.parquet"

COUNTRIES_TO_KEEP = [
    "Austria", "Belgium", "Germany", "Spain", "Finland", "France",
    "Ireland", "Italy", "Netherlands", "Portugal", "the Netherlands"]


def _load_and_clean(path, programme, date_format):
    """Load and clean raw ECB CSV files for PSPP and PEPP holdings"""

    df = pd.read_csv(path, skiprows=2)

    df = df.rename(columns={df.columns[0]: "country"})

    df = df.iloc[:, :-1]

    df = df[df["country"].isin(COUNTRIES_TO_KEEP)].copy()

    df = df.drop_duplicates(subset="country", keep="first")

    df["country"] = df["country"].replace({"the Netherlands": "Netherlands"})

    df_long = df.melt(
        id_vars="country",
        var_name="date",
        value_name="net_purchases_eur_m",
    )

    df_long["net_purchases_eur_m"] = pd.to_numeric(
        df_long["net_purchases_eur_m"], errors="coerce"
    ).fillna(0)

    df_long["date"] = pd.to_datetime(df_long["date"], format=date_format)
    df_long["date"] = df_long["date"] + pd.offsets.MonthEnd(0)

    df_long["programme"] = programme

    return df_long

def _compute_holdings(df_long):

    """Convert monthly net purchases into cumulative holdings"""

    df = df_long.sort_values(["country", "programme", "date"]).copy()

    df["holdings_eur_m"] = df.groupby(
        ["country", "programme"]
    )["net_purchases_eur_m"].cumsum()

    df["holdings_eur_bn"] = (df["holdings_eur_m"] / 1000).round(2)

    return df[["date", "country", "programme", "holdings_eur_bn"]]

def build_holdings_dataset():

    """Build the full ECB holdings dataset (PSPP + PEPP) """

    pspp = _load_and_clean(PSPP_RAW, programme="PSPP", date_format="%d/%m/%Y")
    pepp = _load_and_clean(PEPP_RAW, programme="PEPP", date_format="%b-%y")

    combined = pd.concat([pspp, pepp], ignore_index=True)

    holdings = _compute_holdings(combined)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    holdings.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved {len(holdings)} rows to {OUTPUT_PATH}")
    return holdings


def load_holdings():

    """Load the pre-built ECB holdings dataset"""

    if not OUTPUT_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found at {OUTPUT_PATH}"
        )
    return pd.read_parquet(OUTPUT_PATH)

