"""
Unit tests for stateful Exobiology journal event handling and replay.
Verifies FSSBodySignals, Scan candidate recalculation, SAASignalsFound DSSCompleted flag,
ScanOrganic stage tracking (1/3, 2/3, 3/3), and confirmed organic prediction locking.

All code, docstrings, and comments are strictly English ASCII.
"""

import json
import sqlite3
import pytest
from app.db.database import init_db
from app.parser.journal_parser import JournalParser


def test_stateful_exobiology_event_lifecycle():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(conn)
    sys_addr = 123456789
    body_id = 2

    # Step 1: FSDJump into system
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-30T10:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Test Exo System",
        "SystemAddress": sys_addr,
        "StarPos": [50.0, 10.0, -100.0]
    }))

    # Step 2: FSSBodySignals detects 2 biological signals on Body 2
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-30T10:01:00Z",
        "event": "FSSBodySignals",
        "SystemAddress": sys_addr,
        "BodyID": body_id,
        "BodyName": "Test Exo System 2",
        "Signals": [
            {"Type": "$SAA_SignalType_Biological;", "Count": 2},
            {"Type": "$SAA_SignalType_Geological;", "Count": 1}
        ]
    }))
    parser.flush_dirty_systems()

    c = conn.cursor()
    c.execute("SELECT bio_signals, geo_signals, is_mapped_by_user FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = c.fetchone()
    assert row is not None
    assert row["bio_signals"] == 2
    assert row["geo_signals"] == 1
    assert row["is_mapped_by_user"] == 0

    # Step 3: Detailed Scan updates physical properties and predicts candidates
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-30T10:02:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "StarSystem": "Test Exo System",
        "SystemAddress": sys_addr,
        "BodyName": "Test Exo System 2",
        "BodyID": body_id,
        "DistanceFromArrivalLS": 300.0,
        "PlanetClass": "High metal content body",
        "Atmosphere": "Carbon dioxide",
        "SurfaceTemperature": 240.0,
        "SurfaceGravity": 0.30 * 9.80665,
        "SurfacePressure": 0.035 * 101325,
        "Landable": True,
        "StarType": "F"
    }))
    parser.flush_dirty_systems()

    c.execute("SELECT exobiology_predictions, surface_temperature FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = c.fetchone()
    assert row["surface_temperature"] == 240.0
    preds = json.loads(row["exobiology_predictions"])
    assert len(preds) > 0
    # Stratum Tectonicas should be present
    assert any("Stratum" in p["genus"] for p in preds)

    # Step 4: SAASignalsFound (DSS completed) refreshes bio signals and sets is_mapped_by_user = 1
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-30T10:03:00Z",
        "event": "SAASignalsFound",
        "SystemAddress": sys_addr,
        "BodyID": body_id,
        "BodyName": "Test Exo System 2",
        "Signals": [
            {"Type": "$SAA_SignalType_Biological;", "Count": 2}
        ],
        "Genuses": [
            {"Genus": "$Codex_Ent_Stratum_Genus_Name;", "Genus_Localised": "Stratum"}
        ]
    }))
    parser.flush_dirty_systems()

    c.execute("SELECT is_mapped_by_user, confirmed_genuses FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = c.fetchone()
    assert row["is_mapped_by_user"] == 1
    assert "Stratum" in row["confirmed_genuses"]

    # Step 5: ScanOrganic - Log stage (1/3)
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-30T10:05:00Z",
        "event": "ScanOrganic",
        "ScanType": "Log",
        "SystemAddress": sys_addr,
        "Body": body_id,
        "Genus": "$Codex_Ent_Stratum_Genus_Name;",
        "Genus_Localised": "Stratum",
        "Species": "$Codex_Ent_Stratum_01_Name;",
        "Species_Localised": "Stratum Tectonicas"
    }))
    parser.flush_dirty_systems()

    c.execute("SELECT exobiology_predictions FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = c.fetchone()
    preds = json.loads(row["exobiology_predictions"])
    tectonicas = next((p for p in preds if "Tectonicas" in p["species"]), None)
    assert tectonicas is not None
    assert tectonicas["confidence"] == "confirmed"
    assert tectonicas["stage_level"] == 1
    assert tectonicas["locked"] is True

    # Step 6: ScanOrganic - Analyse stage (3/3)
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-30T10:10:00Z",
        "event": "ScanOrganic",
        "ScanType": "Analyse",
        "SystemAddress": sys_addr,
        "Body": body_id,
        "Genus": "$Codex_Ent_Stratum_Genus_Name;",
        "Genus_Localised": "Stratum",
        "Species": "$Codex_Ent_Stratum_01_Name;",
        "Species_Localised": "Stratum Tectonicas"
    }))
    parser.flush_dirty_systems()

    c.execute("SELECT exobiology_predictions FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = c.fetchone()
    preds = json.loads(row["exobiology_predictions"])
    tectonicas = next((p for p in preds if "Tectonicas" in p["species"]), None)
    assert tectonicas is not None
    assert tectonicas["confidence"] == "confirmed"
    assert tectonicas["stage_level"] == 3
    assert tectonicas["locked"] is True

    # Step 7: Replay Scan event - confirmed organic should remain locked
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-08-30T10:12:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "StarSystem": "Test Exo System",
        "SystemAddress": sys_addr,
        "BodyName": "Test Exo System 2",
        "BodyID": body_id,
        "DistanceFromArrivalLS": 300.0,
        "PlanetClass": "High metal content body",
        "Atmosphere": "Carbon dioxide",
        "SurfaceTemperature": 240.0,
        "SurfaceGravity": 0.30 * 9.80665,
        "SurfacePressure": 0.035 * 101325,
        "Landable": True
    }))
    parser.flush_dirty_systems()

    c.execute("SELECT exobiology_predictions FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = c.fetchone()
    preds = json.loads(row["exobiology_predictions"])
    tectonicas_replayed = next((p for p in preds if "Tectonicas" in p["species"]), None)
    assert tectonicas_replayed is not None
    assert tectonicas_replayed["confidence"] == "confirmed"
    assert tectonicas_replayed["stage_level"] == 3
    assert tectonicas_replayed["locked"] is True

    conn.close()
