import json
from typing import Any

import app.config as config


def read_app_setting(key: str, default: Any = None) -> Any:
    """One value from app_settings.json (read fresh, so a change in Settings applies immediately)."""
    try:
        with open(config.DATA_DIR / "app_settings.json", "r", encoding="utf-8") as f:
            return json.load(f).get(key, default)
    except (OSError, ValueError):
        return default
