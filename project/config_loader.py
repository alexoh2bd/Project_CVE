from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@lru_cache(maxsize=1)
def _load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    with config_path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def get_config(section: Optional[str] = None) -> Dict[str, Any]:
    config = _load_config()
    if section:
        return config.get(section, {})
    return config
