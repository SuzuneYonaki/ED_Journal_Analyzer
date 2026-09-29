from app.config import ADDONS_DIR, DATA_DIR
from app.addons.manager import AddonManager

addon_manager = AddonManager(
    addons_dir=ADDONS_DIR,
    settings_path=DATA_DIR / "addons_settings.json",
)

__all__ = ["addon_manager"]
