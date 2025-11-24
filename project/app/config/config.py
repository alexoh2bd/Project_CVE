# Config settings  written by Gemini-3 Pro on November 22, 2025
from pydantic_settings import BaseSettings
import logging
import sys

def setup_logging():
    # 1. Create a logger
    logger = logging.getLogger("my_ml_api")
    logger.setLevel(logging.INFO)

    # 2. Create a handler (StreamHandler sends to stdout, which Cloud Run captures)
    handler = logging.StreamHandler(sys.stdout)
    
    # 3. Create a formatter (Optional: JSON formatting is best for GCP, but this is human-readable)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # 4. Add handler to logger
    logger.addHandler(handler)
    
    return logger

# Create a singleton instance
logger = setup_logging()
class Settings(BaseSettings):
    PROJECT_NAME: str = "CVE Prediction API"
    ENVIRONMENT: str = "local"
    # Cloud Run injects PORT, but we rarely need to read it here
    
    class Config:
        env_file = ".env"

SETTINGS = Settings()