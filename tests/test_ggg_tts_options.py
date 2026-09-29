"""
test_ggg_tts_options.py - Unit tests for GGG confirmed TTS alert options
Elite Dangerous Journal Analyzer

Candidate (unconfirmed) GGG detections are never voiced -- only
Codex-confirmed sightings trigger a TTS alert. The candidate badge/filter
on the system map is unaffected and untested here.
"""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.server.api import app
from app.addons import addon_manager

_tts_addon = addon_manager.loaded["tts"].module


@pytest.fixture
def client():
    return TestClient(app)


def test_get_tts_settings_defaults(tmp_path, monkeypatch, client):
    """Verifies that get_tts_settings returns gggConfirmedEnabled by default and no candidate key."""
    test_settings_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr(_tts_addon, "TTS_SETTINGS_FILE", test_settings_file)

    res = client.get("/api/tts_settings")
    assert res.status_code == 200
    data = res.json()
    assert data["gggEnabled"] is True
    assert data["gggConfirmedEnabled"] is True
    assert "gggCandidateEnabled" not in data


def test_save_and_retrieve_ggg_confirmed_setting(tmp_path, monkeypatch, client):
    """Verifies that gggConfirmedEnabled can be persisted."""
    test_settings_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr(_tts_addon, "TTS_SETTINGS_FILE", test_settings_file)

    payload = {
        "gggEnabled": True,
        "gggConfirmedEnabled": False,
        "gggMode": "tts"
    }

    res = client.post("/api/tts_settings", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "saved"

    with open(test_settings_file, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved["gggConfirmedEnabled"] is False

    res_get = client.get("/api/tts_settings")
    assert res_get.status_code == 200
    assert res_get.json()["gggConfirmedEnabled"] is False


def test_ui_modal_contains_ggg_confirmed_toggle_only():
    """Verifies modals.html has the confirmed GGG toggle and no candidate toggle."""
    modal_file = Path("app/ui/components/modals.html")
    assert modal_file.exists()
    content = modal_file.read_text(encoding="utf-8")

    assert 'id="tts-ggg-confirmed-toggle"' in content
    assert 'data-i18n="tts_ggg_confirmed_toggle_label"' in content
    assert 'id="tts-ggg-candidate-toggle"' not in content
    assert 'data-i18n="tts_ggg_candidate_toggle_label"' not in content


def test_i18n_contains_ggg_confirmed_label_only():
    """Verifies i18n.js has the confirmed GGG label and no candidate label."""
    i18n_file = Path("app/ui/js/i18n.js")
    assert i18n_file.exists()
    content = i18n_file.read_text(encoding="utf-8")

    assert 'tts_ggg_confirmed_toggle_label: "確定GGG通知"' in content
    assert 'tts_ggg_confirmed_toggle_label: "Confirmed GGG Alert"' in content
    assert 'tts_ggg_candidate_toggle_label' not in content


def test_app_js_evaluates_ggg_confirmed_toggle_only():
    """Verifies app.js handles the confirmed toggle in ttsState, updateTTSModalFields, and
    checkAndAnnounceGggBody, with no candidate-related state left over."""
    app_js_file = Path("app/ui/js/app.js")
    assert app_js_file.exists()
    content = app_js_file.read_text(encoding="utf-8")

    assert "gggConfirmedEnabled: true" in content
    assert "tts-ggg-confirmed-toggle" in content
    assert "ttsState.gggConfirmedEnabled === false" in content

    assert "gggCandidateEnabled" not in content
    assert "tts-ggg-candidate-toggle" not in content


def test_backend_parser_only_supports_confirmed_ggg_alert(tmp_path, monkeypatch):
    """Verifies journal_parser's GGG TTS alert path is confirmed-only: the config has no
    candidate key, and _check_and_trigger_ggg_alert no longer accepts candidate params."""
    from app.parser.journal_parser import get_ggg_tts_config, JournalParser

    test_settings_file = tmp_path / "tts_settings.json"
    monkeypatch.setattr("app.config.DATA_DIR", tmp_path)

    with open(test_settings_file, "w", encoding="utf-8") as f:
        json.dump({
            "enabled": True,
            "gggEnabled": True,
            "gggConfirmedEnabled": True,
            "engine": "voicevox"
        }, f)

    cfg = get_ggg_tts_config()
    assert cfg["confirmed_enabled"] is True
    assert "candidate_enabled" not in cfg

    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    parser = JournalParser(db_conn=conn, is_live=True)
    parser.current_star_system = "Sol"

    # is_candidate / alert_level are no longer accepted parameters.
    import inspect
    sig = inspect.signature(parser._check_and_trigger_ggg_alert)
    assert "is_candidate" not in sig.parameters
    assert "alert_level" not in sig.parameters

    # Confirmed alerts still fire normally.
    enqueued_confirmed = parser._check_and_trigger_ggg_alert(
        sys_addr=123,
        body_name="Body 2",
        is_confirmed=True,
        variant_name="Class II",
    )
    assert enqueued_confirmed is True
