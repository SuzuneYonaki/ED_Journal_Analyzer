import json
import threading
from pathlib import Path

from app.addons.manager import AddonManager

ADDON_IDS = ["edsm_sync", "spansh_sync", "tts", "export_share", "rarity_scorer", "exobiology_prediction"]


def _manager(tmp_path: Path) -> AddonManager:
    return AddonManager(addons_dir=tmp_path / "addons", settings_path=tmp_path / "data" / "addons_settings.json")


def _toggle_concurrently(manager: AddonManager, ids, enabled=True):
    gate = threading.Barrier(len(ids))

    def worker(addon_id):
        gate.wait()
        manager.set_enabled(addon_id, enabled)

    threads = [threading.Thread(target=worker, args=(i,)) for i in ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def test_toggling_several_addons_at_once_loses_no_change(tmp_path):
    """The "External Online Access" switch flips EDSM and Spansh together with two concurrent requests."""
    for _ in range(30):
        manager = _manager(tmp_path)
        if manager.settings_path.exists():
            manager.settings_path.unlink()
        _toggle_concurrently(manager, ADDON_IDS)
        restarted = _manager(tmp_path)  # a restart reads the file again
        assert {i: restarted.is_enabled(i) for i in ADDON_IDS} == {i: True for i in ADDON_IDS}


def test_turning_addons_off_concurrently_also_persists(tmp_path):
    manager = _manager(tmp_path)
    _toggle_concurrently(manager, ADDON_IDS, enabled=True)
    _toggle_concurrently(manager, ["edsm_sync", "spansh_sync"], enabled=False)
    restarted = _manager(tmp_path)
    assert not restarted.is_enabled("edsm_sync") and not restarted.is_enabled("spansh_sync")
    assert all(restarted.is_enabled(i) for i in ADDON_IDS if i not in ("edsm_sync", "spansh_sync"))


def test_settings_file_is_replaced_atomically(tmp_path):
    manager = _manager(tmp_path)
    manager.set_enabled("spansh_sync", True)
    assert json.loads(manager.settings_path.read_text(encoding="utf-8")) == {"spansh_sync": True}
    assert not manager.settings_path.with_name(manager.settings_path.name + ".tmp").exists()


def test_api_toggle_requests_sent_together_all_survive_a_restart(tmp_path, monkeypatch):
    """The Settings > Addons switch posts one toggle per network addon at the same time."""
    from fastapi.testclient import TestClient

    from app.addons import addon_manager
    from app.server.api import app

    monkeypatch.setattr(addon_manager, "settings_path", tmp_path / "addons_settings.json")
    client = TestClient(app)
    results = []

    def post(addon_id):
        results.append(client.post(f"/api/addons/{addon_id}/toggle", json={"enabled": True}).status_code)

    for _ in range(10):
        (tmp_path / "addons_settings.json").unlink(missing_ok=True)
        threads = [threading.Thread(target=post, args=(i,)) for i in ("edsm_sync", "spansh_sync")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        saved = json.loads((tmp_path / "addons_settings.json").read_text(encoding="utf-8"))
        assert saved == {"edsm_sync": True, "spansh_sync": True}
    assert set(results) == {200}
