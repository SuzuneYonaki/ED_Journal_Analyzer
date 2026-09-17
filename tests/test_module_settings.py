import pytest
from fastapi.testclient import TestClient
from app.server.api import app

client = TestClient(app)

def test_module_settings_api(tmp_path, monkeypatch):
    test_file = tmp_path / "module_settings.json"
    monkeypatch.setattr("app.server.api.MODULE_SETTINGS_FILE", test_file)

    # Initial get should return defaults (exobiology: True, rhino: False)
    res = client.get("/api/module_settings")
    assert res.status_code == 200
    data = res.json()
    assert data["exobiology"] is True
    assert data["rhino"] is False

    # Post new settings (turn off exobiology, turn on rhino)
    post_res = client.post("/api/module_settings", json={"exobiology": False, "rhino": True})
    assert post_res.status_code == 200

    # Get again should return updated
    res2 = client.get("/api/module_settings")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["exobiology"] is False
    assert data2["rhino"] is True

def test_tts_settings_high_bio_default(tmp_path, monkeypatch):
    test_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr("app.server.api.TTS_SETTINGS_FILE", test_file)

    res = client.get("/api/tts_settings")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is False
    assert data["highBioEnabled"] is False
    assert data["highBioMode"] == "both"
