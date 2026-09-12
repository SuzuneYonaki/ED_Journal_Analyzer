"""
Real-time telemetry reader for Elite Dangerous (Status.json & live flight state).
Provides immediate coordinates, SRV mode, and planetary body tracking.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

class TelemetryTracker:
    def __init__(self, journal_dir: Optional[str] = None):
        self.journal_dir = Path(journal_dir) if journal_dir else None
        self.last_status: Dict[str, Any] = {}

    def set_journal_dir(self, journal_dir: str):
        self.journal_dir = Path(journal_dir) if journal_dir else None

    def _resolve_journal_dir(self) -> Optional[Path]:
        if self.journal_dir and self.journal_dir.exists():
            return self.journal_dir
        try:
            from app.config import DEFAULT_JOURNAL_DIR
            if DEFAULT_JOURNAL_DIR.exists():
                return DEFAULT_JOURNAL_DIR
        except Exception:
            pass
        cfg_path = Path("Data/config.json")
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("journal_dir") and Path(cfg["journal_dir"]).exists():
                        return Path(cfg["journal_dir"])
            except Exception:
                pass
        return None

    def read_status_json(self) -> Dict[str, Any]:
        """
        Safely reads the current Status.json file from the journal directory.
        Returns parsed dictionary, or empty dict if unavailable.
        """
        target_dir = self._resolve_journal_dir()
        if not target_dir or not target_dir.exists():
            return {}

        status_file = target_dir / "Status.json"
        if not status_file.exists():
            return {}

        try:
            with open(status_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    self.last_status = data
                    return data
        except Exception:
            # File might be mid-write by the game engine; return last known state
            return self.last_status

        return {}

    def get_coordinates(self) -> tuple[Optional[float], Optional[float]]:
        """
        Returns (latitude, longitude) if currently on/near a planet surface.
        Returns (None, None) otherwise.
        """
        status = self.read_status_json()
        lat = status.get("Latitude")
        lon = status.get("Longitude")
        if lat is not None and lon is not None:
            return round(float(lat), 6), round(float(lon), 6)
        return None, None

    def is_in_srv(self) -> bool:
        """
        Checks if the CMDR is currently driving an SRV based on Status.json flags.
        Flag 26 (0x04000000) represents 'In SRV'.
        """
        status = self.read_status_json()
        flags = status.get("Flags", 0)
        return bool(flags & 0x04000000)

telemetry_tracker = TelemetryTracker()
