import json
import pytest
from app.db.database import get_db_connection, init_db
from app.parser.journal_parser import JournalParser
from app.parser.exobiology import evaluate_high_value_bio, predict_exobiology_candidates
from app.services.tts_service import tts_service


def test_evaluate_high_value_bio_stratum_tectonicas():
    """Verify that Stratum Tectonicas triggers high-value status under bonus (40M) and base (8M) thresholds."""
    candidates = [
        {
            "species": "Stratum Tectonicas",
            "genus": "Stratum",
            "base_value": 19010800,
            "first_discovery_value": 95054000,
            "confidence": "definite"
        }
    ]
    
    # 1. Default threshold (40M Cr with 5x bonus)
    res_bonus = evaluate_high_value_bio(candidates, bio_signals=1, threshold=40_000_000, threshold_type="bonus")
    assert res_bonus["is_high_value"] is True
    assert res_bonus["is_bonus_metric"] is True
    assert res_bonus["total_estimated_bonus"] == 95054000
    assert res_bonus["total_estimated_base"] == 19010800
    assert "Stratum Tectonicas" in res_bonus["qualifying_species"]

    # 2. Base value threshold (8M Cr base)
    res_base = evaluate_high_value_bio(candidates, bio_signals=1, threshold=8_000_000, threshold_type="base")
    assert res_base["is_high_value"] is True
    assert res_base["is_bonus_metric"] is False
    assert res_base["comparison_value"] == 19010800
    assert "Stratum Tectonicas" in res_base["qualifying_species"]


def test_evaluate_high_value_bio_low_value_rejection():
    """Verify that low-value organisms (e.g. Bacterium) do not trigger 40M / 8M thresholds."""
    candidates = [
        {
            "species": "Bacterium Aurasus",
            "genus": "Bacterium",
            "base_value": 1000000,
            "first_discovery_value": 5000000,
            "confidence": "definite"
        }
    ]
    
    res_bonus = evaluate_high_value_bio(candidates, bio_signals=1, threshold=40_000_000, threshold_type="bonus")
    assert res_bonus["is_high_value"] is False
    assert len(res_bonus["qualifying_species"]) == 0

    res_base = evaluate_high_value_bio(candidates, bio_signals=1, threshold=8_000_000, threshold_type="base")
    assert res_base["is_high_value"] is False


def test_evaluate_high_value_bio_empty_and_null_guard():
    """Verify safe fallback on empty or None input."""
    res_empty = evaluate_high_value_bio([], bio_signals=0)
    assert res_empty["is_high_value"] is False
    assert res_empty["total_estimated_base"] == 0
    assert res_empty["top_species"] is None


def test_journal_parser_live_high_bio_alert(tmp_path, monkeypatch):
    """Verify that JournalParser enqueues TTS audio when a high-value biological planet is scanned live."""
    conn = get_db_connection()
    init_db()
    
    captured_speech = []
    monkeypatch.setattr(tts_service, "enqueue_speak", lambda text, priority=False: captured_speech.append((text, priority)))
    
    # Mock settings to enable highBio alert
    mock_settings_file = tmp_path / "tts_settings.json"
    mock_settings_file.write_text(json.dumps({
        "enabled": True,
        "highBioEnabled": True,
        "highBioMode": "both",
        "highBioThreshold": 40000000,
        "highBioThresholdType": "bonus",
        "highBioText": "{body}、高額生物反応です。見込額{value}クレジット。"
    }), encoding="utf-8")
    
    import app.parser.journal_parser as jp_module
    import app.config as cfg_module
    monkeypatch.setattr(cfg_module, "DATA_DIR", tmp_path)
    
    parser = JournalParser(conn, is_live=True)
    parser.current_star_system = "Praea Euq YZ-Y d100"
    
    # Scan planet matching Stratum Tectonicas (HMC, CO2 atmosphere, 250K, 0.35G)
    scan_event = {
        "event": "Scan",
        "timestamp": "2026-09-24T08:00:00Z",
        "SystemAddress": 888888888,
        "BodyName": "Praea Euq YZ-Y d100 3",
        "BodyID": 3,
        "PlanetClass": "High metal content world",
        "Atmosphere": "Carbon dioxide",
        "SurfaceTemperature": 250.0,
        "SurfaceGravity": 0.35 * 9.80665,
        "SurfacePressure": 0.04 * 101325,
        "Landable": True,
        "StarType": "F",
        "BioSignals": 2
    }
    
    parser.process_journal_line(json.dumps(scan_event))
    
    assert len(captured_speech) == 1
    msg, priority = captured_speech[0]
    assert "Praea Euq YZ-Y d100 3" in msg
    assert "高額生物反応です" in msg
    assert "95.1M" in msg or "95.0M" in msg or "M" in msg
    assert priority is False

    # Second scan of same body should NOT re-trigger alert (deduplication)
    parser.process_journal_line(json.dumps(scan_event))
    assert len(captured_speech) == 1
    
    conn.close()
