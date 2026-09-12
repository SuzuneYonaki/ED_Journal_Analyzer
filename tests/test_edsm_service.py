"""
Unit tests for EDSM Service integration, rate limiting, and database caching.

All code, strings, and comments in this test module are strictly English ASCII.
"""

import time
from unittest.mock import patch, MagicMock
from app.db.database import get_db_connection, init_db
from app.services.edsm_service import EDSMService, REQUEST_DELAY_SEC


def test_edsm_service_queue_and_cache(tmp_path):
    """Test that EDSMService queues systems and handles responses correctly."""
    conn = get_db_connection()
    init_db(conn)
    c = conn.cursor()

    # Insert a mock test system
    test_sys_addr = 999999001
    test_sys_name = "Test EDSM Alpha"
    c.execute("""
        INSERT OR REPLACE INTO systems (system_address, star_system, edsm_checked, edsm_registered)
        VALUES (?, ?, 0, 0)
    """, (test_sys_addr, test_sys_name))
    conn.commit()
    conn.close()

    service = EDSMService()

    # Mock urllib response for registered system
    mock_system_resp = MagicMock()
    mock_system_resp.status = 200
    mock_system_resp.read.return_value = b'{"name": "Test EDSM Alpha", "coords": {"x": 10.0, "y": 20.0, "z": 30.0}}'
    mock_system_resp.__enter__.return_value = mock_system_resp

    mock_bodies_resp = MagicMock()
    mock_bodies_resp.status = 200
    mock_bodies_resp.read.return_value = b'{"bodyCount": 3, "bodies": [{"name": "Test EDSM Alpha A", "discovery": {"commander": "CMDR Pioneer", "date": "2024-01-01"}}]}'
    mock_bodies_resp.__enter__.return_value = mock_bodies_resp

    with patch("urllib.request.urlopen", side_effect=[mock_system_resp, mock_bodies_resp]):
        service._fetch_and_update_system(test_sys_addr, test_sys_name)

    # Verify DB update
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT edsm_checked, edsm_registered, edsm_first_discoverer, edsm_body_count FROM systems WHERE system_address = ?", (test_sys_addr,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row["edsm_checked"] == 1
    assert row["edsm_registered"] == 1
    assert row["edsm_first_discoverer"] == "CMDR Pioneer"
    assert row["edsm_body_count"] == 3


def test_edsm_unregistered_system():
    """Test handling of systems not present on EDSM."""
    conn = get_db_connection()
    c = conn.cursor()

    test_sys_addr = 999999002
    test_sys_name = "Test EDSM Unregistered"
    c.execute("""
        INSERT OR REPLACE INTO systems (system_address, star_system, edsm_checked, edsm_registered)
        VALUES (?, ?, 0, 0)
    """, (test_sys_addr, test_sys_name))
    conn.commit()
    conn.close()

    service = EDSMService()

    # Mock empty response indicating unregistered system
    mock_empty_resp = MagicMock()
    mock_empty_resp.status = 200
    mock_empty_resp.read.return_value = b'{}'
    mock_empty_resp.__enter__.return_value = mock_empty_resp

    with patch("urllib.request.urlopen", return_value=mock_empty_resp):
        service._fetch_and_update_system(test_sys_addr, test_sys_name)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT edsm_checked, edsm_registered, edsm_first_discoverer FROM systems WHERE system_address = ?", (test_sys_addr,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row["edsm_checked"] == 1
    assert row["edsm_registered"] == 0
    assert row["edsm_first_discoverer"] is None


def test_edsm_priority_queue_and_backfill():
    """Test priority queue placement and recovery for registered systems with 0 bodies."""
    conn = get_db_connection()
    c = conn.cursor()
    test_sys_addr = 999999003
    test_sys_name = "Test EDSM Priority"

    # Seed system as registered but with 0 bodies in DB
    c.execute("""
        INSERT OR REPLACE INTO systems (system_address, star_system, edsm_checked, edsm_registered, edsm_body_count)
        VALUES (?, ?, 1, 1, 5)
    """, (test_sys_addr, test_sys_name))
    c.execute("DELETE FROM bodies WHERE system_address = ?", (test_sys_addr,))
    conn.commit()
    conn.close()

    service = EDSMService()
    # Should accept queueing because bodies are missing in DB
    service.queue_system_check(test_sys_addr, test_sys_name, priority=True)
    assert test_sys_addr in service.priority_systems
    assert not service.high_priority_queue.empty()


def test_edsm_service_extracts_state_and_factions():
    """Test that EDSMService extracts factionState (e.g. Boom), faction, reserve, economy."""
    init_db()
    conn = get_db_connection()
    c = conn.cursor()
    test_sys_addr = 999999004
    test_sys_name = "Kuk"

    c.execute("DELETE FROM systems WHERE system_address = ?", (test_sys_addr,))
    c.execute("""
        INSERT INTO systems (system_address, star_system, edsm_checked, edsm_registered)
        VALUES (?, ?, 0, 0)
    """, (test_sys_addr, test_sys_name))
    conn.commit()
    conn.close()

    service = EDSMService()

    # Mock system response with Boom state and detailed information
    mock_system_resp = MagicMock()
    mock_system_resp.status = 200
    mock_system_resp.read.return_value = b'''{
        "name": "Kuk",
        "id64": 999999004,
        "information": {
            "allegiance": "Independent",
            "government": "Anarchy",
            "faction": "Kuk Silver Mafia",
            "factionState": "Boom",
            "population": 1500000,
            "security": "Low",
            "economy": "Extraction",
            "secondEconomy": "Refinery",
            "reserve": "Pristine"
        }
    }'''
    mock_system_resp.__enter__.return_value = mock_system_resp

    # Mock factions response
    mock_factions_resp = MagicMock()
    mock_factions_resp.status = 200
    mock_factions_resp.read.return_value = b'''{
        "factions": [
            {"name": "Kuk Silver Mafia", "state": "Boom", "influence": 0.65}
        ]
    }'''
    mock_factions_resp.__enter__.return_value = mock_factions_resp

    # Mock bodies response
    mock_bodies_resp = MagicMock()
    mock_bodies_resp.status = 200
    mock_bodies_resp.read.return_value = b'{"bodyCount": 0, "bodies": []}'
    mock_bodies_resp.__enter__.return_value = mock_bodies_resp

    with patch("urllib.request.urlopen", side_effect=[mock_system_resp, mock_factions_resp, mock_bodies_resp]):
        res = service.fetch_and_update_system_sync(test_sys_addr, test_sys_name)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT system_state, controlling_faction, system_reserve, system_economy, system_second_economy
        FROM systems WHERE system_address = ?
    """, (test_sys_addr,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row["system_state"] == "Boom"
    assert row["controlling_faction"] == "Kuk Silver Mafia"
    assert row["system_reserve"] == "Pristine"
    assert row["system_economy"] == "Extraction"
    assert row["system_second_economy"] == "Refinery"


