from pathlib import Path

import typer
import pandas as pd
import os
import gc

from config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    MERGED_DATA_DIR,
    EXTERNAL_DATA_DIR,
    TRAIN_TEST_DIR,
    LOGGER,
)
from process_cve import process_cve_batches, merge_batch_results

app = typer.Typer()


@app.command()
def main(
    input_path: Path = RAW_DATA_DIR / "CVE2024.csv",
    process_path: Path = PROCESSED_DATA_DIR,
    output_path: Path = MERGED_DATA_DIR,
):

    
    # Read input path
    df = pd.read_csv(input_path)
    process_cve_batches(
        df=df,
        column_name="vulnerabilities",
        batch_size=1000,
        output_path=process_path,
        n_workers=4,
        incremental_save=True,
    )
    LOGGER.info(f"Processed {len(df)} cve batches")
    merge_batch_results(process_path, output_path)
    LOGGER.info(f"Merged Batch Results to {output_path}")
    LOGGER.info(f"Cleaning Feature Datasets")

    # Merge feature datasets
    kev = pd.read_csv(f"{EXTERNAL_DATA_DIR}/known_exploited_vulnerabilities.csv")
    main = pd.read_csv(f"{MERGED_DATA_DIR}/main_combined1.csv")


    main["exploited"] = main["cve_id"].isin(kev["cveID"]).astype(int)
    affected= pd.read_csv(f"{MERGED_DATA_DIR}/affected_products_combined1.csv")

    main = pd.merge(main, affected, on="cve_id", how= 'left')
    del affected 
    gc.collect()

    cvss_v3= pd.read_csv(f"{MERGED_DATA_DIR}/cvss_v3_combined1.csv")
    main = pd.merge(main, cvss_v3, on="cve_id", how= 'left')
    del cvss_v3
    gc.collect()

    weakness= pd.read_csv(f"{MERGED_DATA_DIR}/weaknesses_combined1.csv", usecols=["cve_id","type", "cwe_id"])
    main = pd.merge(main, weakness, on="cve_id", how= 'left')
    del weakness 
    gc.collect()

    main1=f"{MERGED_DATA_DIR}/Main1.csv"
    # Save to Main1.csv
    drop_cols = ["Unnamed: 0", "Unnamed: 0_x","Unnamed: 0_y","type_y"]
    main.drop(drop_cols, axis=1, inplace=True)
    main.to_csv(main1, index=False)
    LOGGER.info(f"Saved main features to {main1}")

    del main
    del kev
    gc.collect()


if __name__ == "__main__":
    app()
