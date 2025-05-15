from pathlib import Path

from loguru import logger
from tqdm import tqdm
import typer
import pandas as pd

import ast
from config import FIGURES_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR

app = typer.Typer()


@app.command()
def main(
    # ---- REPLACE DEFAULT PATHS AS APPROPRIATE ----
    input_path: Path = RAW_DATA_DIR / "kev2020-2024.csv",
    output_path: Path = FIGURES_DIR / "plot.png",
    # -----------------------------------------
):
    # # ---- REPLACE THIS WITH YOUR OWN CODE ----
    # logger.info("Generating plot from data...")
    # for i in tqdm(range(10), total=10):
    #     if i == 5:
    #         logger.info("Something happened for iteration 5.")
    # logger.success("Plot generation complete.")
    # # -----------------------------------------
    df = pd.read_csv(input_path)
    # print(df)
    # print(df["status_code"].value_counts())
    v = ast.literal_eval(df["vulnerabilities"] for i in range(len()))


if __name__ == "__main__":
    app()
