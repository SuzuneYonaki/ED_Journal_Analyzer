import os
import json
import sqlite3
import pytest
from pathlib import Path
from app.db.database import init_db
from app.parser.journal_parser import JournalParser
from fastapi.testclient import TestClient
from app.server.api import app

def test_system_age_db_storage_and_api(tmp_path):
    # Setup temporary database
    db_file = tmp_path / "test_age.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(conn)

    # 1. Simulate FSDJump
    jump_event = {
        "timestamp": "2026-10-05T12:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Test Age System",
        "SystemAddress": 99998888,
        "StarPos": [10.0, 20.0, 30.0]
    }
    parser.process_journal_line(json.dumps(jump_event))

    # 2. Simulate Star Scan with Age_MY
    star_scan = {
        "timestamp": "2026-10-05T12:01:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "BodyName": "Test Age System A",
        "BodyID": 0,
        "StarSystem": "Test Age System",
        "SystemAddress": 99998888,
        "DistanceFromArrivalLS": 0.0,
        "StarType": "G",
        "Age_MY": 4500.0,
        "Luminosity": "Va",
        "AbsoluteMagnitude": 4.8
    }
    parser.process_journal_line(json.dumps(star_scan))
    parser.flush_dirty_systems()

    # Verify bodies table
    cursor = conn.cursor()
    cursor.execute("SELECT age_my FROM bodies WHERE system_address = ? AND body_id = 0", (99998888,))
    b_row = cursor.fetchone()
    assert b_row is not None
    assert b_row["age_my"] == 4500.0

    # Verify systems table
    cursor.execute("SELECT system_age_my FROM systems WHERE system_address = ?", (99998888,))
    s_row = cursor.fetchone()
    assert s_row is not None
    assert s_row["system_age_my"] == 4500.0

    conn.close()

def test_system_age_ui_code_integrity():
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    js_list_path = ui_dir / "js" / "system_list.js"
    i18n_path = ui_dir / "js" / "i18n.js"
    css_path = ui_dir / "css" / "style.css"

    js_code = js_list_path.read_text(encoding="utf-8")
    i18n_code = i18n_path.read_text(encoding="utf-8")
    css_code = css_path.read_text(encoding="utf-8")

    # Verify i18n keys
    assert "system_age:" in i18n_code
    assert "my_unit:" in i18n_code

    # Verify system_list.js markup
    assert "system_age_my" in js_code
    assert "system-card-age" in js_code
    assert "system-card-meta-left" in js_code

    # Verify CSS rules
    assert ".system-card-age" in css_code
    assert ".system-card-meta-left" in css_code


def test_backfill_star_ages_for_previously_parsed_systems(tmp_path):
    # Reproduces an upgrade: the star was stored before age columns were
    # populated (age_my NULL) and its journal is already marked as parsed.
    db_file = tmp_path / "test_backfill.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    parser = JournalParser(conn)

    sys_addr = 77776666
    star_scan = {
        "timestamp": "2026-10-05T12:01:00Z", "event": "Scan", "ScanType": "Detailed",
        "BodyName": "Old System A", "BodyID": 0, "StarSystem": "Old System",
        "SystemAddress": sys_addr, "DistanceFromArrivalLS": 0.0, "StarType": "K",
        "Age_MY": 2110.0, "Luminosity": "Va", "AbsoluteMagnitude": 5.5,
    }
    planet_scan = {
        "timestamp": "2026-10-05T12:02:00Z", "event": "Scan", "ScanType": "Detailed",
        "BodyName": "Old System A 1", "BodyID": 1, "StarSystem": "Old System",
        "SystemAddress": sys_addr, "DistanceFromArrivalLS": 100.0,
        "PlanetClass": "Rocky body",
    }
    parser.process_journal_line(json.dumps({
        "timestamp": "2026-10-05T12:00:00Z", "event": "FSDJump",
        "StarSystem": "Old System", "SystemAddress": sys_addr, "StarPos": [1.0, 2.0, 3.0],
    }))
    parser.process_journal_line(json.dumps(star_scan))
    parser.process_journal_line(json.dumps(planet_scan))
    parser.flush_dirty_systems()

    conn.execute("UPDATE bodies SET age_my = NULL WHERE system_address = ?", (sys_addr,))
    conn.execute("UPDATE systems SET system_age_my = NULL WHERE system_address = ?", (sys_addr,))
    conn.commit()
    visits_before = conn.execute(
        "SELECT visit_count FROM systems WHERE system_address = ?", (sys_addr,)
    ).fetchone()["visit_count"]

    journal_dir = tmp_path / "journals"
    journal_dir.mkdir()
    (journal_dir / "Journal.2026-10-05T120000.01.log").write_text(
        "\n".join(json.dumps(e) for e in (star_scan, planet_scan)) + "\n", encoding="utf-8"
    )

    res = parser.backfill_star_ages(journal_dir)
    assert res["bodies_updated"] == 1
    assert res["systems_updated"] == 1

    assert conn.execute(
        "SELECT age_my FROM bodies WHERE system_address = ? AND body_id = 0", (sys_addr,)
    ).fetchone()["age_my"] == 2110.0
    row = conn.execute(
        "SELECT system_age_my, visit_count FROM systems WHERE system_address = ?", (sys_addr,)
    ).fetchone()
    assert row["system_age_my"] == 2110.0
    assert row["visit_count"] == visits_before

    # Idempotent: a second run changes nothing
    assert parser.backfill_star_ages(journal_dir)["bodies_updated"] == 0
    conn.close()
