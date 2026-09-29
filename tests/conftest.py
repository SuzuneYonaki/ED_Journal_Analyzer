"""Session-wide test setup.

Every addon now ships with enabled_by_default=false (addons/*/addon.json),
so a clean checkout has none of them loaded -- correct for a real release,
but several existing tests exercise addon-provided code paths (TTS, EDSM
sync, Spansh sync, export/import, rarity scoring, exobiology prediction)
and expect them loaded. Rather than relying on the real project's data/
directory (which would leak this "all addons on" state into the
developer's own real app runs on this machine), point addon_manager at a
throwaway settings file before anything imports app.server.api (which is
what actually triggers discover()/load_enabled() at module import time).

This module runs as a pytest conftest, so it executes before test modules
in this directory are collected/imported.
"""
import json
import tempfile
from pathlib import Path

from app.addons import addon_manager

_scratch_dir = Path(tempfile.mkdtemp(prefix="ed_analyzer_test_addons_"))
addon_manager.settings_path = _scratch_dir / "addons_settings.json"

_ALL_ADDON_IDS = [
    "edsm_sync",
    "spansh_sync",
    "tts",
    "export_share",
    "rarity_scorer",
    "exobiology_prediction",
]
addon_manager.settings_path.write_text(
    json.dumps({addon_id: True for addon_id in _ALL_ADDON_IDS}),
    encoding="utf-8",
)
