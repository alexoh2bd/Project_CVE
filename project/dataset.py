from pathlib import Path
import pandas as pd
from loguru import logger
from tqdm import tqdm
import typer
from batch import PublicAPIBatchProcessor
import requests

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    # ----------------------------------------------
):
    logger.info(RAW_DATA_DIR)
    kev = pd.read_csv(f"{RAW_DATA_DIR}/known_exploited_vulnerabilities.csv")

    # Initialize API processor for a public REST Countries API
    processor = PublicAPIBatchProcessor(
        base_url="https://services.nvd.nist.gov/rest/json/cves/2.0/",
        max_concurrent_requests=10,
        rate_limit_per_minute=120,  # Be respectful of public APIs
    )

    # Process the DataFrame
    nvd = processor.process_dataframe(
        df=kev,
        column_name="cveID",
        endpoint="",  # endpoint that accepts country code
        param_name="cveID",  # parameter name for country code
        batch_size=10,
    )

    nvd["exploited"] = nvd["cveID"].isin(kev["cveID"]).astype(int)
    result_df = pd.merge(nvd, kev, on="cveID", how="inner")

    result_df.to_csv(f"{RAW_DATA_DIR}/kev.csv")


if __name__ == "__main__":
    app()
