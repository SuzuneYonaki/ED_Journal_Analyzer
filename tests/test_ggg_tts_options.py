"""
test_ggg_tts_options.py - Unit tests for GGG confirmed and candidate TTS alert options
Elite Dangerous Journal Analyzer
"""
import json
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.server.api import app, TTS_SETTINGS_FILE


@pytest.fixture
def client():
    return TestClient(app)


def test_get_tts_settings_defaults(tmp_path, monkeypatch, client):
    """Verifies that get_tts_settings returns gggConfirmedEnabled and gggCandidateEnabled by default."""
    test_settings_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr("app.server.api.TTS_SETTINGS_FILE", test_settings_file)

    res = client.get("/api/tts_settings")
    assert res.status_code == 200
    data = res.json()
    assert data["gggEnabled"] is True
    assert data["gggConfirmedEnabled"] is True
    assert data["gggCandidateEnabled"] is True


def test_save_and_retrieve_ggg_toggle_settings(tmp_path, monkeypatch, client):
    """Verifies that gggConfirmedEnabled and gggCandidateEnabled can be persisted individually."""
    test_settings_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr("app.server.api.TTS_SETTINGS_FILE", test_settings_file)

    # Disable candidate alert, keep confirmed alert
    payload = {
        "gggEnabled": True,
        "gggConfirmedEnabled": True,
        "gggCandidateEnabled": False,
        "gggMode": "tts"
    }

    res = client.post("/api/tts_settings", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "saved"

    # Verify file content
    with open(test_settings_file, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved["gggConfirmedEnabled"] is True
    assert saved["gggCandidateEnabled"] is False

    # Verify GET endpoint merges properly
    res_get = client.get("/api/tts_settings")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["gggConfirmedEnabled"] is True
    assert data_get["gggCandidateEnabled"] is False


def test_ui_modal_contains_ggg_toggles():
    """Verifies modals.html contains the toggle checkboxes for confirmed and candidate GGGs."""
    modal_file = Path("app/ui/components/modals.html")
    assert modal_file.exists()
    content = modal_file.read_text(encoding="utf-8")

    assert 'id="tts-ggg-confirmed-toggle"' in content
    assert 'id="tts-ggg-candidate-toggle"' in content
    assert 'data-i18n="tts_ggg_confirmed_toggle_label"' in content
    assert 'data-i18n="tts_ggg_candidate_toggle_label"' in content


def test_i18n_contains_ggg_toggle_labels():
    """Verifies i18n.js has the translation keys in both ja and en dictionaries."""
    i18n_file = Path("app/ui/js/i18n.js")
    assert i18n_file.exists()
    content = i18n_file.read_text(encoding="utf-8")

    # Match in ja dictionary
    assert 'tts_ggg_confirmed_toggle_label: "確定GGG通知"' in content
    assert 'tts_ggg_candidate_toggle_label: "候補GGG通知"' in content

    # Match in en dictionary
    assert 'tts_ggg_confirmed_toggle_label: "Confirmed GGG Alert"' in content
    assert 'tts_ggg_candidate_toggle_label: "Candidate GGG Alert"' in content


def test_app_js_evaluates_ggg_toggles():
    """Verifies app.js handles confirmed and candidate toggles in ttsState, updateTTSModalFields, and checkAndAnnounceGggBody."""
    app_js_file = Path("app/ui/js/app.js")
    assert app_js_file.exists()
    content = app_js_file.read_text(encoding="utf-8")

    # ttsState initial properties
    assert "gggConfirmedEnabled: true" in content
    assert "gggCandidateEnabled: true" in content

    # DOM elements
    assert "tts-ggg-confirmed-toggle" in content
    assert "tts-ggg-candidate-toggle" in content

    # checkAndAnnounceGggBody branching
    assert "ttsState.gggConfirmedEnabled === false" in content
    assert "ttsState.gggCandidateEnabled === false" in content
