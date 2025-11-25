from pathlib import Path
import pandas as pd
import typer
from batch import PublicAPIBatchProcessor
from dotenv import load_dotenv
import os
from config import RAW_DATA_DIR, LOGGER, PROJ_ROOT
from datetime import date
import calendar

from project.config_loader import get_config


app = typer.Typer()
load_dotenv()

CONFIG = get_config()
DATA_CFG = CONFIG.get("data", {})
INGEST_CFG = CONFIG.get("ingest", {})


def _resolve_path(path_value: str, fallback: Path) -> Path:
    if not path_value:
        return fallback
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJ_ROOT / path
    return path


def get_Dates(start_year, end_year):
    params = []
    for year in range(start_year, end_year + 1):
        # Create the four quarters for each year
        for month in range(1, 13):
            for i in range(0, 6000, 2000):
                _, last_date = calendar.monthrange(year, month)
                start_date = date(year, month, 1)
                end_date = date(year, month, last_date)
                dict = {
                    "pubStartDate": f"{year}-{start_date.strftime('%m')}-01T00:00:00.000",
                    "pubEndDate": f"{year}-{end_date.strftime('%m')}-{last_date}T23:59:59.999",
                    "startIndex": i,
                }
                params.append(dict)
    return params


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = _resolve_path(DATA_CFG.get("raw_dataset", ""), RAW_DATA_DIR / "dataset.csv"),
    output_path: Path = _resolve_path(DATA_CFG.get("raw_output", ""), RAW_DATA_DIR / "CVE2024.csv"),
    start_year: int = typer.Option(INGEST_CFG.get("start_year", 2023), help="First year to pull CVEs for."),
    end_year: int = typer.Option(INGEST_CFG.get("end_year", 2024), help="Last year to pull CVEs for."),
    batch_size: int = typer.Option(INGEST_CFG.get("batch_size", 10), help="Number of parameter rows per API call."),
    max_concurrent_requests: int = typer.Option(
        INGEST_CFG.get("max_concurrent_requests", 10), help="Concurrent requests allowed by the API."
    ),
    rate_limit_per_minute: int = typer.Option(
        INGEST_CFG.get("rate_limit_per_minute", 120), help="Maximum calls per minute."
    ),
    # ----------------------------------------------
):

    api_key = os.getenv("NVD_API_KEY")

    params = get_Dates(start_year, end_year)
    dates = pd.DataFrame(params)
    mcr, rate_lim = max_concurrent_requests, rate_limit_per_minute
    LOGGER.info(
        f"Ingesting at {mcr} max concurrent requests per minute and at Rate Limit of {rate_lim} per minute."
    )
    
    # Initialize API processor for a public REST Countries API
    processor = PublicAPIBatchProcessor(
        base_url="https://services.nvd.nist.gov/rest/json/cves/2.0/",
        max_concurrent_requests=mcr,
        rate_limit_per_minute=rate_lim,  # Be respectful of public APIs
    )

    LOGGER.info(f"Processing DataFrame")
    # Process the DataFrame
    nvd = processor.process_dataframe(
        df=dates,
        column_names=["pubStartDate", "pubEndDate", "startIndex"],
        endpoint="",
        param_names=["pubStartDate", "pubEndDate", "startIndex"],
        batch_size=batch_size,
        api_key=api_key,
    )
    nvd.to_csv(output_path)


if __name__ == "__main__":
    app()
