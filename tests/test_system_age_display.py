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
