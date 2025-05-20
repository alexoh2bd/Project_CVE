from pathlib import Path

import typer
import pandas as pd

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, MERGED_DATA_DIR
from process_cve import process_cve_batches, merge_batch_results
import ast

app = typer.Typer()


def define_kev(kev_path, main_path):

    kev = pd.read_csv(kev_path)
    nvd = pd.read_csv(main_path)
    nvd["exploited"] = nvd["cve_id"].isin(kev["cveID"]).astype(int)
    print(sum(nvd["cve_id"] == 1))
    # result_df = pd.merge(nvd, kev, left_on="cve_id", how="inner", right_index=True)
    # return nvd


# def define_cwe(weakness_path, cwe_path):
#     cwe = pd.read_csv(cwe_path)
#     weakness= pd.read_csv(weakness_path)
#     # weakness['CWE_Description'] =


@app.command()
def main(
    input_path: Path = RAW_DATA_DIR / "CVE2020.csv",
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

    merge_batch_results(process_path, output_path)

    # add Known Exploited Vulnerabilities column to main DataFrame of NVDs
    kev_path = f"{RAW_DATA_DIR}/known_exploited_vulnerabilities.csv"
    main_path = f"{MERGED_DATA_DIR}/main_combined.csv"
    define_kev(kev_path, main_path)  # .to_csv(main_path)


if __name__ == "__main__":
    app()
