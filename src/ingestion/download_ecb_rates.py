"""
Download ECB rate series via the public Statistical Data Warehouse API.
Saves raw CSVs to data/raw/ for further cleaning by repo_rates.py
"""

from pathlib import Path
import httpx


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

ECB_API_BASE = "https://data-api.ecb.europa.eu/service/data"

SERIES = {
    "estr_rates.csv": "EST/B.EU000A2X2A25.WT",
    "dfr_rates.csv": "FM/D.U2.EUR.4F.KR.DFR.LEV",
}


def _download_series(series_key, filename):

    """Download ECB series as CSV"""

    url = f"{ECB_API_BASE}/{series_key}?format=csvdata"

    response = httpx.get(url, timeout=60.0, follow_redirects=True)
    response.raise_for_status()

    output_path = RAW_DIR / filename
    output_path.write_bytes(response.content)


def download_all():

    """Download all ECB rate series"""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for filename, series_key in SERIES.items():
        _download_series(series_key, filename)


if __name__ == "__main__":
    download_all()