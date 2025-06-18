from pathlib import Path

from loguru import logger
from tqdm import tqdm
import typer
import pandas as pd

from project.pdpipeline.config import PROCESSED_DATA_DIR

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "features.csv",
    # -----------------------------------------
):
    df = pd.read_csv("")


if __name__ == "__main__":
    app()
