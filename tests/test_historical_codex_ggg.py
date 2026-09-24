"""
test_historical_codex_ggg.py - Unit tests for historical Codex GGG scanning,
event-order inversion safety, and TTS live suppression.
"""
import json
import sqlite3
import pytest
from pathlib import Path

from app.db.database import init_db
from app.parser.journal_parser import JournalParser
from app.services.tts_service import tts_service


@pytest.fixture
def parser_env(tmp_path):
    """Sets up an isolated SQLite database and JournalParser instances."""
    db_file = str(tmp_path / "test_hist_ggg.db")
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser_live = JournalParser(db_conn=conn, is_live=True)
    parser_hist = JournalParser(db_conn=conn, is_live=False)

    yield {"conn": conn, "live": parser_live, "hist": parser_hist, "tmp_path": tmp_path}
    conn.close()


def test_event_inversion_codex_before_scan(parser_env):
    """
    Verifies that when CodexEntry arrives BEFORE the Scan event:
    1. CodexEntry is stored in codex_entries table.
    2. When Scan event arrives later, it queries codex_entries and preserves
       Confirmed GGG tags in anomalies_json.
    """
    parser = parser_env["live"]
    conn = parser_env["conn"]
    sys_addr = 9876543210123
    body_id = 7
    body_name = "Hypo Hypo AB-C d1-1 7"

    # Step 1: CodexEntry arrives first (before any Scan event exists)
    codex_event = {
        "timestamp": "2026-09-24T12:00:00Z",
        "event": "CodexEntry",
        "EntryID": 140003,
        "Name": "$Codex_Ent_Green_Helium_Rich_Gas_Giant_Name;",
        "Name_Localised": "Green Helium-rich Gas Giant",
        "Category": "$Codex_Category_Astronomical_Bodies_Name;",
        "SubCategory": "$Codex_SubCat_Gas_Giants_Name;",
        "System": "Hypo Hypo AB-C d1-1",
        "SystemAddress": sys_addr,
        "BodyID": body_id,
        "BodyName": body_name
    }
    parser.process_journal_line(json.dumps(codex_event))

    # Verify codex_entries persistence
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM codex_entries WHERE system_address = ? AND body_id = ?",
        (sys_addr, body_id)
    )
    codex_row = cursor.fetchone()
    assert codex_row is not None
    assert codex_row["is_ggg"] == 1
    assert codex_row["ggg_variant"] == "Helium-rich Gas Giant"

    # Step 2: Scan event arrives later
    scan_event = {
        "timestamp": "2026-09-24T12:05:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "BodyName": body_name,
        "BodyID": body_id,
        "StarSystem": "Hypo Hypo AB-C d1-1",
        "SystemAddress": sys_addr,
        "DistanceFromArrivalLS": 3400.0,
        "PlanetClass": "Gas giant with water based life",
        "SurfaceTemperature": 150.0,
        "MassEM": 85.0
    }
    parser.process_journal_line(json.dumps(scan_event))

    # Step 3: Verify bodies table record has Confirmed GGG tags preserved
    cursor.execute(
        "SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = ?",
        (sys_addr, body_id)
    )
    body_row = cursor.fetchone()
    assert body_row is not None
    anomalies = json.loads(body_row["anomalies_json"])
    tags = [a["tag"] for a in anomalies if isinstance(a, dict)]
    assert "Confirmed GGG" in tags
    assert "Confirmed GGG (Helium-rich Gas Giant)" in tags


def test_event_order_scan_before_codex_and_rescan_safety(parser_env):
    """
    Verifies that when Scan arrives first, then CodexEntry arrives, and then
    another Scan arrives, the Confirmed GGG status is never overwritten or lost.
    """
    parser = parser_env["live"]
    conn = parser_env["conn"]
    sys_addr = 112233445566
    body_id = 3
    body_name = "Synuefe XO-P c2-5 3"

    # 1. Scan arrives first
    scan_event = {
        "timestamp": "2026-09-24T13:00:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "BodyName": body_name,
        "BodyID": body_id,
        "StarSystem": "Synuefe XO-P c2-5",
        "SystemAddress": sys_addr,
        "DistanceFromArrivalLS": 890.0,
        "PlanetClass": "Sudarsky class V gas giant",
        "SurfaceTemperature": 1400.0,
        "MassEM": 450.0
    }
    parser.process_journal_line(json.dumps(scan_event))

    # 2. CodexEntry arrives
    codex_event = {
        "timestamp": "2026-09-24T13:10:00Z",
        "event": "CodexEntry",
        "EntryID": 140005,
        "Name": "$Codex_Ent_Green_Sudarsky_Class_V_Name;",
        "Name_Localised": "Green Gas Giant (Class V)",
        "Category": "$Codex_Category_Astronomical_Bodies_Name;",
        "SubCategory": "$Codex_SubCat_Gas_Giants_Name;",
        "SystemAddress": sys_addr,
        "BodyID": body_id
    }
    parser.process_journal_line(json.dumps(codex_event))

    cursor = conn.cursor()
    cursor.execute("SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    b_row = cursor.fetchone()
    anomalies = json.loads(b_row["anomalies_json"])
    tags = [a["tag"] for a in anomalies if isinstance(a, dict)]
    assert "Confirmed GGG" in tags
    assert "Confirmed GGG (Sudarsky Class V Gas Giant)" in tags

    # 3. Subsequent Scan event (e.g. DSS mapping update or re-parse)
    scan_event_dss = dict(scan_event)
    scan_event_dss["timestamp"] = "2026-09-24T13:15:00Z"
    scan_event_dss["WasMapped"] = True
    parser.process_journal_line(json.dumps(scan_event_dss))

    cursor.execute("SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    b_row2 = cursor.fetchone()
    anomalies2 = json.loads(b_row2["anomalies_json"])
    tags2 = [a["tag"] for a in anomalies2 if isinstance(a, dict)]
    assert "Confirmed GGG" in tags2
    assert "Confirmed GGG (Sudarsky Class V Gas Giant)" in tags2


def test_tts_live_vs_historical_suppression(monkeypatch, parser_env):
    """
    Verifies that TTS audio playback is strictly suppressed when is_live is False,
    and enabled when is_live is True.
    """
    live_parser = parser_env["live"]
    hist_parser = parser_env["hist"]

    spoken_messages = []

    def mock_speak(text, priority=False):
        spoken_messages.append((text, priority))
        return True

    monkeypatch.setattr(tts_service, "enqueue_speak", mock_speak)

    codex_event = {
        "timestamp": "2026-09-24T14:00:00Z",
        "event": "CodexEntry",
        "EntryID": 140008,
        "Name": "$Codex_Ent_Green_Water_Giant_Name;",
        "SystemAddress": 777888999,
        "BodyID": 1
    }

    # Historical parser should NOT speak
    hist_parser.process_journal_line(json.dumps(codex_event))
    assert len(spoken_messages) == 0

    # Live parser SHOULD speak
    live_parser.process_journal_line(json.dumps(codex_event))
    assert len(spoken_messages) == 1
    msg, prio = spoken_messages[0]
    assert prio is True
    assert "ウォーター・ジャイアント" in msg


def test_scan_historical_codex_entries_utility(monkeypatch, parser_env):
    """
    Verifies scan_historical_codex_entries finds GGGs in past journal files,
    populates codex_entries, links with existing bodies, and never triggers TTS.
    """
    conn = parser_env["conn"]
    tmp_path = parser_env["tmp_path"]
    journal_dir = tmp_path / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
    journal_dir.mkdir(parents=True, exist_ok=True)

    spoken = []
    monkeypatch.setattr(tts_service, "enqueue_speak", lambda text, priority=False: spoken.append(text))

    sys_addr = 444555666777
    body_id = 5

    # Pre-insert body into DB (as if scanned in past without Codex)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, anomalies_json)
        VALUES (?, ?, 'Pha Aea TX-A d1 5', '[]')
    """, (sys_addr, body_id))
    conn.commit()

    # Create mock journal file 1 (Contains normal logs and Codex GGG)
    jfile1 = journal_dir / "Journal.2026-01-01T100000.01.log"
    lines1 = [
        json.dumps({"timestamp": "2026-01-01T10:00:00Z", "event": "Fileheader", "part": 1}),
        json.dumps({"timestamp": "2026-01-01T10:01:00Z", "event": "FSDJump", "StarSystem": "Sol"}),
        json.dumps({
            "timestamp": "2026-01-01T10:05:00Z",
            "event": "CodexEntry",
            "Name": "$Codex_Ent_Green_Sudarsky_Class_I_Name;",
            "Name_Localised": "Green Gas Giant (Class I)",
            "SystemAddress": sys_addr,
            "BodyID": body_id,
            "BodyName": "Pha Aea TX-A d1 5"
        })
    ]
    jfile1.write_text("\n".join(lines1) + "\n", encoding="utf-8")

    # Create mock journal file 2 (Non-GGG Codex entry)
    jfile2 = journal_dir / "Journal.2026-01-02T100000.01.log"
    lines2 = [
        json.dumps({
            "timestamp": "2026-01-02T10:05:00Z",
            "event": "CodexEntry",
            "Name": "$Codex_Ent_Bacterial_Name;",
            "SystemAddress": sys_addr,
            "BodyID": 2
        })
    ]
    jfile2.write_text("\n".join(lines2) + "\n", encoding="utf-8")

    # Run historical scan with live parser to verify TTS suppression holds
    parser = parser_env["live"]
    result = parser.scan_historical_codex_entries(journal_dir)

    assert result["scanned_files"] == 2
    assert result["codex_entries_found"] == 2
    assert result["ggg_entries_found"] == 1
    assert len(spoken) == 0  # No TTS spoken during historical scan

    # Verify codex_entries in DB
    cursor.execute("SELECT * FROM codex_entries WHERE is_ggg = 1")
    ggg_rows = cursor.fetchall()
    assert len(ggg_rows) == 1
    assert ggg_rows[0]["ggg_variant"] == "Sudarsky Class I Gas Giant"

    # Verify pre-existing body got updated with Confirmed GGG anomaly tag
    cursor.execute("SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    b_row = cursor.fetchone()
    anomalies = json.loads(b_row["anomalies_json"])
    tags = [a["tag"] for a in anomalies if isinstance(a, dict)]
    assert "Confirmed GGG" in tags
    assert "Confirmed GGG (Sudarsky Class I Gas Giant)" in tags
