from pathlib import Path
import typer
from extract import ExtractCVE
from dotenv import load_dotenv
import os
from plconfig import RAW_DATA_DIR
import polars as pl
import tqdm


app = typer.Typer()
load_dotenv()


@app.command()
def main(
    CVE_Parquet: Path = RAW_DATA_DIR / "CVE.parquet",
):

    api_key = os.getenv("NVD_API_KEY")
    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0/"

    # # Initialize API processor for a public REST Countries API
    extractor = ExtractCVE(
        base_url=BASE_URL,
    )
    # year range of the cve data we want to pull
    year_range = [2020, 2025]
    # Process the DataFrame
    nvd = extractor.extract(
        dates=year_range,
        endpoint="",
        batch_size=10,
        API_KEY=api_key,
    )
    print("Extracted Nvd data")

    nvd.write_parquet(CVE_Parquet)

    df = pl.read_parquet(CVE_Parquet)
    print(df.head()["vulnerabilities"])


if __name__ == "__main__":
    app()
