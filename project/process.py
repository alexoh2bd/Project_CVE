from pathlib import Path

import typer
import pandas as pd

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from process_cve import process_cve_batches, merge_batch_results

app = typer.Typer()


@app.command()
def main(
    input_path: Path = RAW_DATA_DIR / "kev20-24.csv",
    output_path: Path = PROCESSED_DATA_DIR,
):

    df = pd.read_csv(input_path)
    print(output_path)
    process_cve_batches(
        df=df,
        column_name="vulnerabilities",
        batch_size=500,
        output_path=output_path,
        n_workers=4,
        incremental_save=True,
    )

    merge_batch_results(output_path)


if __name__ == "__main__":
    app()
