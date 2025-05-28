from pathlib import Path

import typer
import pandas as pd
import os

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR, MERGED_DATA_DIR, EXTERNAL_DATA_DIR
from process_cve import process_cve_batches, merge_batch_results

app = typer.Typer()


def define_kev(kev_path, main_path):

    kev = pd.read_csv(kev_path)
    nvd = pd.read_csv(main_path)
    nvd["exploited"] = nvd["cve_id"].isin(kev["cveID"]).astype(int)


@app.command()
def main(
    input_path: Path = RAW_DATA_DIR / "CVE2024.csv",
    process_path: Path = PROCESSED_DATA_DIR,
    output_path: Path = MERGED_DATA_DIR,
):

    # Read input path
    df = pd.read_csv(input_path)
    print(process_path)
    process_cve_batches(
        df=df,
        column_name="vulnerabilities",
        batch_size=1000,
        output_path=process_path,
        n_workers=4,
        incremental_save=True,
    )

    merge_batch_results(process_path, output_path)

    kev = pd.read_csv(f"{EXTERNAL_DATA_DIR}/known_exploited_vulnerabilities.csv")
    main = pd.read_csv(f"{MERGED_DATA_DIR}/main_combined1.csv")
    main["exploited"] = main["cve_id"].isin(kev["cveID"]).astype(int)
    main.to_csv(os.path.join(MERGED_DATA_DIR, f"Main.csv"))


if __name__ == "__main__":
    app()


# def define_cwe(weakness_path, cwe_path):
#     cwe = pd.read_csv(cwe_path)
#     weakness= pd.read_csv(weakness_path)
#     # weakness['CWE_Description'] =


# # add Known Exploited Vulnerabilities column to main DataFrame of NVDs
# kev_path = f"{RAW_DATA_DIR}/known_exploited_vulnerabilities.csv"
# main_path = f"{MERGED_DATA_DIR}/main_combined.csv"
# define_kev(kev_path, main_path)  # .to_csv(main_path)

# csv_files = [f for f in os.listdir(process_path)]
# main_files = []
# for file in csv_files:
#     chunk = file.split("_batch")
#     if chunk[0] == "main":
#         main_files.append(file)
# count = 0
# for file in main_files:
#     kev = pd.read_csv(f"{EXTERNAL_DATA_DIR}/known_exploited_vulnerabilities.csv")
#     main = pd.read_csv(f"{PROCESSED_DATA_DIR}/{file}")
#     main["exploited"] = main["cve_id"].isin(kev["cveID"]).astype(int)
#     # result_df = pd.merge(main, kev, on="cveID", how="inner")
#     count += main[main["exploited"] == 1].shape[0]
#     print(main[main["exploited"] == 1].shape[0])
# print(count)
