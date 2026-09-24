"""
test_all_ggg_variants.py - Unit Tests for All Green Gas Giant (GGG) Variants via CodexEntry & TTS
Elite Dangerous Journal Analyzer
"""

import json
import sqlite3
import pytest

from app.parser.journal_parser import (
    CODEX_GGG_PATTERN,
    GGG_VARIANTS_MAP,
    resolve_ggg_variant,
    JournalParser
)
from app.db.database import init_db
from app.services.tts_service import tts_service


# =====================================================================
# 1. Regex & Variant Resolution Unit Tests
# =====================================================================

@pytest.mark.parametrize("entry_name, expected_raw, expected_speech, expected_en", [
    (
        "$Codex_Ent_Green_Sudarsky_Class_III_Name;",
        "Sudarsky_Class_III",
        "スダルスキー・クラス3 ガス巨人",
        "Sudarsky Class III Gas Giant"
    ),
    (
        "$Codex_Ent_Green_Sudarsky_Class_I_Name;",
        "Sudarsky_Class_I",
        "スダルスキー・クラス1 ガス巨人",
        "Sudarsky Class I Gas Giant"
    ),
    (
        "$Codex_Ent_Green_Gas_Giant_Water_Life_Name;",
        "Gas_Giant_Water_Life",
        "水生生命保有ガス巨人",
        "Gas Giant with Water-based Life"
    ),
    (
        "$Codex_Ent_Green_Gas_Giant_Ammonia_Life_Name;",
        "Gas_Giant_Ammonia_Life",
        "アンモニア生命保有ガス巨人",
        "Gas Giant with Ammonia-based Life"
    ),
    (
        "$Codex_Ent_Green_Helium_Rich_Gas_Giant_Name;",
        "Helium_Rich_Gas_Giant",
        "高ヘリウム含有ガス巨人",
        "Helium-rich Gas Giant"
    ),
    (
        "$Codex_Ent_Green_Water_Giant_Name;",
        "Water_Giant",
        "ウォーター・ジャイアント",
        "Water Giant"
    ),
    (
        "$Codex_Ent_Green_Unknown_Exotic_Type_Name;",
        "Unknown_Exotic_Type",
        "Unknown Exotic Type",
        "Unknown Exotic Type"
    ),
])
def test_resolve_ggg_variants(entry_name, expected_raw, expected_speech, expected_en):
    res = resolve_ggg_variant(entry_name)
    assert res is not None
    raw_v, speech_name, en_name = res
    assert raw_v == expected_raw
    assert speech_name == expected_speech
    assert en_name == expected_en


def test_resolve_ggg_variant_non_ggg_and_none():
    assert resolve_ggg_variant("$Codex_Ent_Bacterial_Gold_Name;") is None
    assert resolve_ggg_variant("$Codex_Ent_Stellar_Black_Hole_Name;") is None
    assert resolve_ggg_variant("") is None
    assert resolve_ggg_variant(None) is None


# =====================================================================
# 2. JournalParser CodexEntry Event & TTS Dispatch Integration Tests
# =====================================================================

@pytest.fixture
def test_parser(tmp_path):
    """Sets up an isolated JournalParser with an in-memory or temp SQLite database."""
    db_file = str(tmp_path / "test_ggg.db")
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    init_db(conn)

    parser = JournalParser(db_conn=conn, is_live=True)
    yield parser, conn
    conn.close()


def test_codex_entry_ggg_speech_and_db_persistence(monkeypatch, test_parser):
    parser, conn = test_parser
    sys_addr = 3932402345678
    body_id = 4
    body_name = "Blae Eurl AB-C d1-2 4"

    # Pre-populate body record in DB via Scan event
    scan_event = {
        "timestamp": "2026-09-24T10:00:00Z",
        "event": "Scan",
        "ScanType": "Detailed",
        "BodyName": body_name,
        "BodyID": body_id,
        "StarSystem": "Blae Eurl AB-C d1-2",
        "SystemAddress": sys_addr,
        "DistanceFromArrivalLS": 1200.0,
        "PlanetClass": "Sudarsky class III gas giant with water based life",
        "SurfaceTemperature": 210.0,
        "MassEM": 120.0
    }
    parser.process_journal_line(json.dumps(scan_event))

    # Track calls to tts_service.enqueue_speak
    spoken_messages = []

    def mock_enqueue_speak(text: str, priority: bool = False):
        spoken_messages.append((text, priority))
        return True

    monkeypatch.setattr(tts_service, "enqueue_speak", mock_enqueue_speak)

    # Process CodexEntry for Sudarsky Class III GGG
    codex_event = {
        "timestamp": "2026-09-24T10:05:00Z",
        "event": "CodexEntry",
        "EntryID": 140001,
        "Name": "$Codex_Ent_Green_Sudarsky_Class_III_Name;",
        "Name_Localised": "Green Gas Giant (Class III)",
        "SubCategory": "$Codex_SubCat_Gas_Giants_Name;",
        "Category": "$Codex_Category_Astronomical_Bodies_Name;",
        "System": "Blae Eurl AB-C d1-2",
        "SystemAddress": sys_addr,
        "BodyID": body_id
    }
    parser.process_journal_line(json.dumps(codex_event))

    # Verify TTS utterance
    assert len(spoken_messages) >= 1
    last_msg, priority = spoken_messages[-1]
    assert priority is True
    assert "警告。正真正銘のグリーンガスジャイアントを発見しました！" in last_msg
    assert "種別は、スダルスキー・クラス3 ガス巨人 です。" in last_msg

    # Verify DB anomalies_json contains confirmed tags
    cursor = conn.cursor()
    cursor.execute("SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = cursor.fetchone()
    assert row is not None
    anomalies = json.loads(row["anomalies_json"])
    tags = [a["tag"] for a in anomalies if isinstance(a, dict)]
    assert "Confirmed GGG" in tags
    assert "Confirmed GGG (Sudarsky Class III Gas Giant)" in tags


@pytest.mark.parametrize("codex_name, expected_speech_sub, expected_tag_sub", [
    (
        "$Codex_Ent_Green_Gas_Giant_Water_Life_Name;",
        "水生生命保有ガス巨人",
        "Confirmed GGG (Gas Giant with Water-based Life)"
    ),
    (
        "$Codex_Ent_Green_Gas_Giant_Ammonia_Life_Name;",
        "アンモニア生命保有ガス巨人",
        "Confirmed GGG (Gas Giant with Ammonia-based Life)"
    ),
    (
        "$Codex_Ent_Green_Helium_Rich_Gas_Giant_Name;",
        "高ヘリウム含有ガス巨人",
        "Confirmed GGG (Helium-rich Gas Giant)"
    ),
    (
        "$Codex_Ent_Green_Water_Giant_Name;",
        "ウォーター・ジャイアント",
        "Confirmed GGG (Water Giant)"
    ),
    (
        "$Codex_Ent_Green_Unknown_Exotic_Type_Name;",
        "Unknown Exotic Type",
        "Confirmed GGG (Unknown Exotic Type)"
    )
])
def test_all_codex_ggg_variants_dispatch(monkeypatch, test_parser, codex_name, expected_speech_sub, expected_tag_sub):
    parser, conn = test_parser
    sys_addr = 555123456
    body_id = 2

    # Insert minimal body record
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, anomalies_json)
        VALUES (?, ?, 'Test Giant', '[]')
    """, (sys_addr, body_id))
    conn.commit()

    captured_tts = []
    monkeypatch.setattr(tts_service, "enqueue_speak", lambda text, priority=False: captured_tts.append((text, priority)))

    codex_event = {
        "timestamp": "2026-09-24T10:10:00Z",
        "event": "CodexEntry",
        "Name": codex_name,
        "SystemAddress": sys_addr,
        "BodyID": body_id
    }
    parser.process_journal_line(json.dumps(codex_event))

    assert len(captured_tts) == 1
    msg, prio = captured_tts[0]
    assert prio is True
    assert expected_speech_sub in msg

    # Verify anomalies_json
    cursor.execute("SELECT anomalies_json FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
    row = cursor.fetchone()
    anomalies = json.loads(row["anomalies_json"])
    tags = [a["tag"] for a in anomalies if isinstance(a, dict)]
    assert "Confirmed GGG" in tags
    assert expected_tag_sub in tags
