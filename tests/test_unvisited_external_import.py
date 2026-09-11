import os
import tempfile
import sqlite3
import pytest
from fastapi.testclient import TestClient

os.environ["ED_JOURNAL_DIR"] = tempfile.mkdtemp()
from app.db.database import get_db_connection, init_db
from app.server.api import app

@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)

def test_unvisited_external_system_import_and_export_lock(client):
    """
    Assert that:
    1. An external unvisited system can be registered/imported with is_external=1 and visit_count=0.
    2. Exporting as standalone HTML is strictly blocked with HTTP 403.
    3. Exporting in an .edsys package is strictly blocked with HTTP 403.
    """
    dummy_addr = 999888777666
    dummy_sys_name = "Test_External_System_999"

    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO systems (
                system_address, star_system, star_pos_x, star_pos_y, star_pos_z,
                is_external, visit_count, total_bodies, scanned_bodies
            ) VALUES (?, ?, 100.0, -50.0, 200.0, 1, 0, 5, 5)
        """, (dummy_addr, dummy_sys_name))
        conn.execute("""
            INSERT OR REPLACE INTO bodies (
                body_id, system_address, body_name, star_type, scan_type
            ) VALUES (1, ?, 'Test_External_System_999 A', 'Star', 'EDSM_Known')
        """, (dummy_addr,))
        conn.commit()

    # 1. Verify DB registration
    with get_db_connection() as conn:
        row = conn.execute("SELECT is_external, visit_count FROM systems WHERE system_address = ?", (dummy_addr,)).fetchone()
        assert row is not None
        assert row["is_external"] == 1
        assert row["visit_count"] == 0

    # 2. Standalone HTML Export should return 403
    res_html = client.get(f"/api/export/html/{dummy_addr}")
    assert res_html.status_code == 403
    assert "外部参照" in res_html.text or "未訪問" in res_html.text

    # 3. .edsys Package Export should return 403
    res_pkg = client.post("/api/export/package", json={
        "system_addresses": [dummy_addr],
        "consent_token": True,
        "cmdr_name": "Commander",
        "notes": "Test"
    })
    assert res_pkg.status_code == 403
    assert "外部参照" in res_pkg.text or "未訪問" in res_pkg.text

    # 4. Save local .edsys Package Export should return 403
    res_save = client.post("/api/export/package/save-local", json={
        "system_addresses": [dummy_addr],
        "consent_token": True,
        "cmdr_name": "Commander",
        "notes": "Test"
    })
    assert res_save.status_code == 403
    assert "外部参照" in res_save.text or "未訪問" in res_save.text
