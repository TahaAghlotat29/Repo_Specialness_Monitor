from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = ROOT / "data" / "raw" / "bond_reference.csv"

def load_reference():

    """Load the bond reference universe with derived fields"""

    if not REFERENCE_PATH.exists():
        raise FileNotFoundError(
            f"Bond reference file not found at {REFERENCE_PATH}."
        )

    df = pd.read_csv( REFERENCE_PATH, parse_dates=["maturity_date", "issue_date"],)

    df["years_to_maturity"] = ( (df["maturity_date"] - pd.Timestamp.today()).dt.days / 365.25).round(2)

    df = df[df["years_to_maturity"] > 0].copy()

    df["maturity_bucket"] = df["years_to_maturity"].apply(_bucket_maturity)

    return df

def _bucket_maturity(years):

    """Assign a bond to a standard maturity bucket"""

    if years < 2:
        return "0-2Y"
    if years < 5:
        return "2-5Y"
    if years < 10:
        return "5-10Y"
    return "10Y+"

def filter_by_country(df, country):

    """Filter universe by country code (e.g. 'DE', 'FR', 'EU')"""

    return df[df["country"] == country].copy()


def filter_by_issuer_type(df, issuer_type):

    """Filter by issuer type: 'Sovereign', 'SSA', 'Supranational'"""

    return df[df["issuer_type"] == issuer_type].copy()


def get_bund_universe(df=None):

    """Return German sovereign bonds (Bunds) only"""

    df = df if df is not None else load_reference()
    return df[
        (df["country"] == "DE") & (df["issuer_type"] == "Sovereign")
    ].copy()
