"""
test_tts_voicevox_save_sync.py - Unit tests for TTS VOICEVOX settings persistence and service synchronization
Elite Dangerous Journal Analyzer
"""
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.server.api import app, TTS_SETTINGS_FILE, sync_tts_settings_to_service
from app.services.tts_service import tts_service


@pytest.fixture
def client():
    return TestClient(app)


def test_tts_settings_persistence_and_service_sync(tmp_path, monkeypatch, client):
    """Verifies that saving via /api/tts_settings preserves all fields and updates tts_service config."""
    test_settings_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr("app.server.api.TTS_SETTINGS_FILE", test_settings_file)

    payload = {
        "enabled": True,
        "engine": "voicevox",
        "voicevoxSpeakerId": "7",
        "voicevoxUrl": "http://127.0.0.1:50021",
        "rate": 1.2,
        "volume": 0.85,
        "customText": "First discover in {system}.",
        "gggConfirmedText": "Confirmed GGG: {variant}",
        "highBioText": "High bio alert: {value}"
    }

    # 1. Post settings
    res = client.post("/api/tts_settings", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "saved"

    # 2. Verify file content on disk
    assert test_settings_file.exists()
    with open(test_settings_file, "r", encoding="utf-8") as f:
        file_data = json.load(f)
    assert file_data["engine"] == "voicevox"
    assert file_data["voicevoxSpeakerId"] == "7"
    assert file_data["gggConfirmedText"] == "Confirmed GGG: {variant}"

    # 3. Verify tts_service was synchronously updated
    service_cfg = tts_service.get_config()
    assert service_cfg["speaker_id"] == 7
    assert service_cfg["voicevox_url"] == "http://127.0.0.1:50021"
    assert service_cfg["speed_scale"] == 1.2
    assert service_cfg["volume_scale"] == 0.85


def test_tts_config_does_not_destroy_settings_file(tmp_path, monkeypatch, client):
    """Verifies that calling /api/tts/config updates matching fields without wiping other UI settings."""
    test_settings_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr("app.server.api.TTS_SETTINGS_FILE", test_settings_file)

    # Initial full settings
    initial_settings = {
        "enabled": True,
        "engine": "voicevox",
        "voicevoxSpeakerId": "3",
        "customText": "Original Custom Text",
        "gggEnabled": True,
        "gggConfirmedText": "Original GGG text"
    }
    with open(test_settings_file, "w", encoding="utf-8") as f:
        json.dump(initial_settings, f)

    # Call /api/tts/config with partial updates
    config_req = {
        "speaker_id": 8,
        "speed_scale": 1.5
    }
    res = client.post("/api/tts/config", json=config_req)
    assert res.status_code == 200

    # Verify that existing keys were NOT deleted
    with open(test_settings_file, "r", encoding="utf-8") as f:
        preserved_data = json.load(f)

    assert preserved_data["engine"] == "voicevox"
    assert preserved_data["customText"] == "Original Custom Text"
    assert preserved_data["gggConfirmedText"] == "Original GGG text"
    assert preserved_data["voicevoxSpeakerId"] == "8"
    assert preserved_data["rate"] == 1.5


def test_ui_settings_modal_close_does_not_save_logic():
    """Verifies in app.js that close buttons do not invoke saveTTSSettings, while Apply button does."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    app_js_path = ui_dir / "js" / "app.js"
    assert app_js_path.exists()

    code = app_js_path.read_text(encoding="utf-8")

    # 1. Close buttons must only hide modal and not call saveTTSSettings
    close_idx = code.find("if (btnClose && modal)")
    save_idx = code.find("if (btnSave && modal)")
    assert close_idx != -1
    assert save_idx != -1

    close_section = code[close_idx:save_idx]
    assert "saveTTSSettings" not in close_section

    # 2. btnSave section must call await saveTTSSettings
    save_section = code[save_idx:save_idx + 4000]
    assert "await saveTTSSettings();" in save_section
    assert "ttsState.voicevoxSpeakerId = voicevoxSpeakerSelect.value;" in save_section
