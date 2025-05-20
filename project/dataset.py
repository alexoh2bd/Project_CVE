from pathlib import Path
import pandas as pd
from loguru import logger
from tqdm import tqdm
import typer
from batch import PublicAPIBatchProcessor
import requests
from dotenv import load_dotenv
import os
from config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from datetime import date
import calendar
import backoff

app = typer.Typer()
load_dotenv()

import asyncio
import concurrent.futures
import requests
from typing import List, Dict, Any, Optional


async def fetch_all_data(
    endpoint: str, parameter_sets: List[Dict[str, Any]], headers: Optional[str] = None
) -> List[Dict]:
    """Fetch data from multiple API endpoints using a thread pool within an async function"""

    @backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        max_tries=20 + 1,
        max_time=600,
    )
    def make_request(params):
        """Function that runs in the thread pool to make a blocking API call"""
        try:
            response = requests.get(endpoint, params=params, headers=headers)
            logger.info(f"Response : {response} {response.text}")
            return response
        except Exception as e:
            return {"error": str(e)}

    # Get the running event loop
    loop = asyncio.get_running_loop()
    # param_names = parameter_sets.keys()
    # zipped_values = list(map(list, zip(*parameter_sets)))
    # logger.info(f"Zipped values: {zipped_values}")

    # Create tasks using run_in_executor
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        tasks = [
            loop.run_in_executor(executor, make_request, params)
            for params in parameter_sets
        ]

        # Gather all results
        results = await asyncio.gather(*tasks)
    return results


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "dataset.csv",
    output_path: Path = RAW_DATA_DIR / "CVE2020.csv",
    # ----------------------------------------------
):

    # Initialize API processor for a public REST Countries API
    processor = PublicAPIBatchProcessor(
        base_url="https://services.nvd.nist.gov/rest/json/cves/2.0/",
        max_concurrent_requests=10,
        rate_limit_per_minute=120,  # Be respectful of public APIs
    )

    api_key = os.getenv("NVD_API_KEY")

    params = []
    start_year, end_year = 2021, 2021
    for year in range(start_year, end_year + 1):
        # Create the four quarters for each year
        quarters = [
            # Q1: Jan-Mar
            {
                "pubStartDate": f"{year}-01-01T00:00:00.000",
                "pubEndDate": f"{year}-03-31T23:59:59.999",
            },
            # Q2: Apr-Jun
            {
                "pubStartDate": f"{year}-04-01T00:00:00.000",
                "pubEndDate": f"{year}-06-30T23:59:59.999",
            },
            # Q3: Jul-Sep
            {
                "pubStartDate": f"{year}-07-01T00:00:00.000",
                "pubEndDate": f"{year}-09-30T23:59:59.999",
            },
            # Q4: Oct-Dec
            {
                "pubStartDate": f"{year}-10-01T00:00:00.000",
                "pubEndDate": f"{year}-12-31T23:59:59.999",
            },
        ]
        params.extend(quarters)

    df = pd.DataFrame(params)

    # Process the DataFrame
    nvd = processor.process_dataframe(
        df=df,
        column_names=["pubStartDate", "pubEndDate"],
        endpoint="",
        param_names=["pubStartDate", "pubEndDate"],
        batch_size=10,
        api_key=api_key,
    )
    nvd.to_csv(output_path)

    """
    kev = pd.read_csv(f"{RAW_DATA_DIR}/known_exploited_vulnerabilities.csv")
    nvd = pd.read_csv('f"{RAW_DATA_DIR}/kev2020-2024.csv"')
    nvd["exploited"] = nvd["cveID"].isin(kev["cveID"]).astype(int)
    result_df = pd.merge(nvd, kev, on="cveID", how="inner")

"""


if __name__ == "__main__":
    app()
