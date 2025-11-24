from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
import sys

# Load environment variables from .env file if it exists
load_dotenv()

def init_logger(log_dir: Path = Path("logs")):
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()

    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level="INFO",
    )

    logger.add(
        log_dir / "pipeline.log",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )

    return logger



# Paths
PROJ_ROOT = Path(__file__).resolve().parents[2]

LOG_DIR = PROJ_ROOT / "reports" / "logs"

# Initialize immediately when imported
LOGGER = init_logger(LOG_DIR)


DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
MERGED_DATA_DIR = DATA_DIR / "merged"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
TRAIN_TEST_DIR = DATA_DIR / "traintest"

MODELS_DIR = PROJ_ROOT / "models"

API_MODELS_DIR = PROJ_ROOT / "project" / "app"/ "models"


REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    LOGGER.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
