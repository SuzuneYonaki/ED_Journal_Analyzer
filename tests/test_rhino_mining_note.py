import os
import tempfile
import sqlite3
import pytest
from fastapi.testclient import TestClient

os.environ["ED_JOURNAL_DIR"] = tempfile.mkdtemp()
from app.db.database import get_db_connection, init_db
from app.server.api import app
from app.live.rhino.note_integrator import (
    append_or_merge_mining_site_to_note,
    update_body_note_in_db,
    MINING_SECTION_HEADER
)
from app.live.rhino.tracker import extract_all_mining_materials_for_body, sync_body_mining_to_note
from app.parser.journal_parser import JournalParser

@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)

def test_note_integrator_formatting_and_merging():
    """
    Assert that:
    1. Only coordinates and mined materials are recorded (no verbose timestamps or log spam).
    2. Repeated mining at the same coordinates cleanly merges minerals into a single line.
    3. User's existing notes are 100% preserved.
    """
    initial_user_note = "CMDR Note: Excellent flat terrain for SRV racing."
    lat = 12.3456
    lon = -45.6789

    # 1. First mining event
    note_v1 = append_or_merge_mining_site_to_note(
        existing_note=initial_user_note,
        lat=lat,
        lon=lon,
        new_minerals=["Iron", "Nickel"]
    )
    assert initial_user_note in note_v1
    assert MINING_SECTION_HEADER in note_v1
    assert "- [Lat: +12.3456°, Lon: -45.6789°]: Iron, Nickel" in note_v1

    # 2. Second mining event at the SAME coordinates with a NEW mineral
    note_v2 = append_or_merge_mining_site_to_note(
        existing_note=note_v1,
        lat=lat,
        lon=lon,
        new_minerals=["Germanium", "Iron"]  # Duplicate Iron, new Germanium
    )
    # The note must NOT have duplicate lines for the same coordinate
    lines = [line.strip() for line in note_v2.splitlines() if "[Lat: +12.3456°, Lon: -45.6789°]" in line]
    assert len(lines) == 1, f"Expected 1 merged line, found: {lines}"
    assert "- [Lat: +12.3456°, Lon: -45.6789°]: Germanium, Iron, Nickel" in lines[0]
    assert initial_user_note in note_v2

    # 3. Third mining event at a DIFFERENT coordinate
    lat2 = 20.0000
    lon2 = 80.0000
    note_v3 = append_or_merge_mining_site_to_note(
        existing_note=note_v2,
        lat=lat2,
        lon=lon2,
        new_minerals=["Polonium"]
    )
    lines_c1 = [line.strip() for line in note_v3.splitlines() if "[Lat: +12.3456°, Lon: -45.6789°]" in line]
    lines_c2 = [line.strip() for line in note_v3.splitlines() if "[Lat: +20.0000°, Lon: +80.0000°]" in line]
    assert len(lines_c1) == 1
    assert len(lines_c2) == 1
    assert "- [Lat: +20.0000°, Lon: +80.0000°]: Polonium" in lines_c2[0]

def test_api_append_mining_endpoint(client):
    """
    Test the POST /api/bookmark/{system_address}/{body_id}/append_mining endpoint.
    """
    sys_addr = 1122334455
    body_id = 4
    star_sys = "Test Mining System"
    body_name = "Test Mining Planet 4"

    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO systems (system_address, star_system)
            VALUES (?, ?)
        """, (sys_addr, star_sys))
        conn.execute("""
            INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_system)
            VALUES (?, ?, ?, ?)
        """, (sys_addr, body_id, body_name, star_sys))
        conn.commit()

    # Append single site
    res = client.post(f"/api/bookmark/{sys_addr}/{body_id}/append_mining", json={
        "latitude": -5.1234,
        "longitude": 102.4321,
        "minerals": ["Bauxite", "Painite"]
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "ok"
    assert "Bauxite, Painite" in data["note_markdown"]
    assert "[Lat: -5.1234°, Lon: +102.4321°]" in data["note_markdown"]

    # Verify in DB
    with get_db_connection() as conn:
        row = conn.execute("SELECT note_markdown FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (sys_addr, body_id)).fetchone()
        assert row is not None
        assert "[Lat: -5.1234°, Lon: +102.4321°]: Bauxite, Painite" in row["note_markdown"]

def test_journal_parser_live_mining_auto_note():
    """
    Verify that JournalParser in live mode automatically appends to the body note during SRV mining.
    """
    sys_addr = 5566778899
    body_id = 2
    star_sys = "Live Mining System"
    body_name = "Live Mining Moon 2"

    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO systems (system_address, star_system) VALUES (?, ?)", (sys_addr, star_sys))
    conn.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_system) VALUES (?, ?, ?, ?)", (sys_addr, body_id, body_name, star_sys))
    conn.commit()

    parser = JournalParser(db_conn=conn, is_live=True)
    parser.current_system_address = sys_addr
    parser.current_star_system = star_sys
    parser.current_body_id = body_id
    parser.current_body_name = body_name
    parser.in_srv = True
    parser.current_latitude = -15.5555
    parser.current_longitude = 30.3333

    # Process MaterialCollected
    parser.process_journal_line('{"timestamp":"2026-09-12T09:00:00Z","event":"MaterialCollected","Category":"Raw","Name":"selenium","Name_Localised":"Selenium","Count":1}')
    # Process another MaterialCollected at same coords
    parser.process_journal_line('{"timestamp":"2026-09-12T09:00:05Z","event":"MaterialCollected","Category":"Raw","Name":"iron","Name_Localised":"Iron","Count":1}')

    # Check note in DB
    row = conn.execute("SELECT note_markdown FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (sys_addr, body_id)).fetchone()
    assert row is not None
    note = row["note_markdown"]
    assert "- [Lat: -15.5555°, Lon: +30.3333°]: Iron, Selenium" in note

    conn.close()
