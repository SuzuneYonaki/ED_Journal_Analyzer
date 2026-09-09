import pytest
import json
from fastapi.testclient import TestClient
from app.server.api import app
import app.server.api as api_mod

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_app_settings(monkeypatch, tmp_path):
    settings_file = tmp_path / "app_settings.json"
    monkeypatch.setattr(api_mod, "APP_SETTINGS_FILE", settings_file)
    monkeypatch.setattr(api_mod, "DATA_DIR", tmp_path)


def test_default_language_setting():
    resp = client.get("/api/app_settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["language"] == "ja"


def test_save_and_retrieve_language():
    # Save language 'en'
    post_resp = client.post("/api/app_settings", json={"language": "en"})
    assert post_resp.status_code == 200
    post_data = post_resp.json()
    assert post_data["status"] == "saved"
    assert post_data["settings"]["language"] == "en"

    # Get settings
    get_resp = client.get("/api/app_settings")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["language"] == "en"


def test_settings_merge_preserves_language_and_other_fields(tmp_path):
    # First save language 'en'
    client.post("/api/app_settings", json={"language": "en"})

    # Then update journal_dir
    custom_dir = tmp_path / "custom_journals"
    custom_dir.mkdir()
    update_resp = client.post("/api/app_settings", json={"journal_dir": str(custom_dir)})
    assert update_resp.status_code == 200
    update_data = update_resp.json()
    assert update_data["settings"]["language"] == "en"
    assert update_data["settings"]["journal_dir"] == str(custom_dir)

    # Verify GET returns both
    get_resp = client.get("/api/app_settings")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["language"] == "en"
    assert get_data["journal_dir"] == str(custom_dir)
