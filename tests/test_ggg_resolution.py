import pytest
import sqlite3
import json
from app.db.database import init_db, get_celestial_statistics
from app.parser.journal_parser import JournalParser, is_matching_ggg_planet_class

def test_is_matching_ggg_planet_class():
    assert is_matching_ggg_planet_class("Sudarsky Class III Gas Giant", "Sudarsky class III gas giant")
    assert is_matching_ggg_planet_class("Sudarsky Class I Gas Giant", "Sudarsky class I gas giant")
    assert not is_matching_ggg_planet_class("Sudarsky Class I Gas Giant", "Sudarsky class II gas giant")
    assert is_matching_ggg_planet_class("Gas Giant with Water-based Life", "Gas giant with water based life")
    assert not is_matching_ggg_planet_class("Sudarsky Class III Gas Giant", "A")

def test_ggg_codex_entry_resolves_to_gas_giant_not_star(tmp_path):
    test_db = tmp_path / "test_ggg.db"
    conn = sqlite3.connect(str(test_db))
    conn.row_factory = sqlite3.Row
    init_db(conn, force=True)

    # Insert system, primary star (body_id=0), and planet 3 (body_id=24, Sudarsky Class III)
    c = conn.cursor()
    sys_addr = 999999999
    c.execute("""
        INSERT INTO systems (system_address, star_system, visit_count, is_external)
        VALUES (?, 'Test GGG System', 1, 0)
    """, (sys_addr,))

    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_type, planet_class, anomalies_json)
        VALUES (?, 0, 'Test GGG System', 'A', NULL, '[]')
    """, (sys_addr,))

    c.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_type, planet_class, anomalies_json)
        VALUES (?, 24, 'Test GGG System 3', NULL, 'Sudarsky class III gas giant', '[]')
    """, (sys_addr,))

    conn.commit()

    parser = JournalParser(db_conn=conn)

    # Simulate Frontier's CodexEntry event which gives BodyID=0 (primary star)
    codex_event = {
        "event": "CodexEntry",
        "timestamp": "2026-09-24T00:59:05Z",
        "EntryID": 1200702,
        "Name": "$Codex_Ent_Green_Sudarsky_Class_III_Name;",
        "Name_Localised": "Green gas giant",
        "Category": "$Codex_Category_StellarBodies;",
        "SubCategory": "$Codex_SubCategory_Gas_Giants;",
        "System": "Test GGG System",
        "SystemAddress": sys_addr,
        "BodyID": 0,
        "IsNewEntry": True
    }
    parser._handle_codex_entry(codex_event, "2026-09-24T00:59:05Z")
    parser.flush_dirty_systems()
    conn.commit()

    # 1. Primary star must NOT have Confirmed GGG
    c.execute("SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = 0", (sys_addr,))
    star_row = c.fetchone()
    assert "Confirmed GGG" not in (star_row["anomalies_json"] or "")

    # 2. Planet 3 must have Confirmed GGG
    c.execute("SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = 24", (sys_addr,))
    p3_row = c.fetchone()
    assert "Confirmed GGG" in (p3_row["anomalies_json"] or "")

    # 3. CodexEntry record must be attributed to body_id 24, not 0
    c.execute("SELECT body_id, body_name, is_ggg FROM codex_entries WHERE system_address = ?", (sys_addr,))
    codex_row = c.fetchone()
    assert codex_row["body_id"] == 24
    assert codex_row["body_name"] == "Test GGG System 3"
    assert codex_row["is_ggg"] == 1

    # 4. Header statistics must count 1 green_gas_giant
    stats = get_celestial_statistics(conn, bypass_cache=True)
    assert stats["planets"]["green_gas_giant"] == 1

    conn.close()
