from pathlib import Path
import pandas as pd
import typer
from batch import PublicAPIBatchProcessor
from dotenv import load_dotenv
import os
from config import RAW_DATA_DIR,  LOGGER
from datetime import date
import calendar


app = typer.Typer()
load_dotenv()

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
                    "pubStartDate": f"{year}-{start_date.strftime("%m")}-01T00:00:00.000",
                    "pubEndDate": f"{year}-{end_date.strftime("%m")}-{last_date}T23:59:59.999",
                    "startIndex": i,
                }
                params.append(dict)
    return params


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "dataset.csv",
    output_path: Path = RAW_DATA_DIR / "CVE2024.csv",
    # ----------------------------------------------
):

    api_key = os.getenv("NVD_API_KEY")

    params = get_Dates(2023, 2024)
    dates = pd.DataFrame(params)
    mcr, rate_lim=10, 120
    LOGGER.info(f"Ingesting at {mcr} max concurrent requests per minute and at Rate Limit of {rate_lim} per minute.")
    
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
        batch_size=10,
        api_key=api_key,
    )
    nvd.to_csv(output_path)


if __name__ == "__main__":
    app()
