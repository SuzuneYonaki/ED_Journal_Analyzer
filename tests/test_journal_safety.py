import pytest
import sqlite3
import os
import json
from pathlib import Path
from app.db.database import init_db
from app.parser.journal_parser import JournalParser

@pytest.fixture
def test_env(tmp_path):
    db_file = tmp_path / "test_safety.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    
    journal_dir = tmp_path / "journals"
    journal_dir.mkdir()
    
    yield conn, journal_dir
    conn.close()

def test_incomplete_line_rollback_and_recovery(test_env):
    conn, journal_dir = test_env
    parser = JournalParser(conn)
    log_file = journal_dir / "Journal.2026-09-12T000000.01.log"

    # Step 1: Write a complete FSDJump line and an INCOMPLETE Scan line (no newline)
    line1_bytes = (json.dumps({
        "timestamp": "2026-09-12T00:00:00Z",
        "event": "FSDJump",
        "StarSystem": "Sol",
        "SystemAddress": 10418619,
        "StarPos": [0.0, 0.0, 0.0]
    }) + "\n").encode("utf-8")

    incomplete_bytes = b'{"timestamp":"2026-09-12T00:01:00Z","event":"Scan","BodyName":"Earth","SystemAddress":10418619' # Truncated!

    with open(log_file, "wb") as f:
        f.write(line1_bytes)
        f.write(incomplete_bytes)

    # Parse file while incomplete
    parser.parse_file(str(log_file))

    # Check that Sol was registered, but Earth scan was NOT registered yet (offset wound back)
    c = conn.cursor()
    c.execute("SELECT star_system FROM systems WHERE system_address = 10418619")
    sys_row = c.fetchone()
    assert sys_row is not None
    assert sys_row["star_system"] == "Sol"

    c.execute("SELECT body_name FROM bodies WHERE system_address = 10418619")
    bodies = c.fetchall()
    assert len(bodies) == 0  # Incomplete line was safely ignored!

    # Check stored offset in parsed_files: should be exactly len(line1_bytes)
    c.execute("SELECT last_line_offset FROM parsed_files WHERE filename = ?", (log_file.name,))
    row = c.fetchone()
    assert row["last_line_offset"] == len(line1_bytes)

    # Step 2: Elite Dangerous finishes writing the complete Scan line with newline
    completed_bytes = b',"BodyID":1,"PlanetClass":"Earthlike body","MassEM":1.0,"ScanType":"Detailed"}\n'
    with open(log_file, "ab") as f:
        f.write(completed_bytes)

    # Re-parse the file
    parser.parse_file(str(log_file))

    # Check that Earth is now fully registered without any corruption or data loss!
    c.execute("SELECT body_name, planet_class, scan_type FROM bodies WHERE system_address = 10418619")
    earth = c.fetchone()
    assert earth is not None
    assert earth["body_name"] == "Earth"
    assert earth["planet_class"] == "Earthlike body"
    assert earth["scan_type"] == "Detailed"

def test_file_truncation_resets_offset(test_env):
    conn, journal_dir = test_env
    parser = JournalParser(conn)
    log_file = journal_dir / "Journal.2026-09-12T000001.01.log"

    # Step 1: Write two lines
    line1 = (json.dumps({"timestamp": "2026-09-12T00:00:00Z", "event": "FSDJump", "StarSystem": "SysA", "SystemAddress": 111, "StarPos": [0,0,0]}) + "\n").encode("utf-8")
    line2 = (json.dumps({"timestamp": "2026-09-12T00:01:00Z", "event": "FSDJump", "StarSystem": "SysB", "SystemAddress": 222, "StarPos": [1,1,1]}) + "\n").encode("utf-8")

    with open(log_file, "wb") as f:
        f.write(line1 + line2)

    parser.parse_file(str(log_file))
    c = conn.cursor()
    c.execute("SELECT last_line_offset FROM parsed_files WHERE filename = ?", (log_file.name,))
    old_offset = c.fetchone()["last_line_offset"]
    assert old_offset > len(line1)

    # Step 2: File is truncated or overwritten with smaller content
    short_line = (json.dumps({"timestamp": "2026-09-12T00:02:00Z", "event": "FSDJump", "StarSystem": "SysC", "SystemAddress": 333, "StarPos": [2,2,2]}) + "\n").encode("utf-8")
    with open(log_file, "wb") as f:
        f.write(short_line)

    # Re-parse: offset should safely reset to 0 and parse SysC
    parser.parse_file(str(log_file))

    c.execute("SELECT star_system FROM systems WHERE system_address = 333")
    assert c.fetchone() is not None
