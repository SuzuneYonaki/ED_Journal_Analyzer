import os
import pytest
import sqlite3
from app.db.database import init_db
from app.services.export_service import (
    calculate_package_signature,
    verify_package_signature,
    create_edsys_package,
    import_edsys_package,
    generate_standalone_html,
    sanitize_system_for_export
)

def test_signature_and_tampering():
    test_systems = [
        {
            "system_address": 12345,
            "star_system": "Col 285 Sector Test",
            "bodies": [
                {"body_id": 1, "body_name": "Col 285 Sector Test A", "star_type": "G"},
                {"body_id": 2, "body_name": "Col 285 Sector Test 1", "planet_class": "Earthlike body"}
            ]
        }
    ]
    cmdr = "Commander Yonaki"
    sig = calculate_package_signature(test_systems, cmdr)
    assert len(sig) == 64

    package = {
        "format": "ED_JOURNAL_ANALYZER_PACKAGE_V1",
        "metadata": {
            "version": "1.0",
            "cmdr_name": cmdr,
            "system_count": 1
        },
        "signature": sig,
        "systems": test_systems
    }

    # 1. Valid package
    is_valid, msg = verify_package_signature(package)
    assert is_valid is True

    # 2. Tampered CMDR name
    tampered_package = dict(package)
    tampered_package["metadata"] = {"version": "1.0", "cmdr_name": "Impostor CMDR", "system_count": 1}
    is_valid_t, msg_t = verify_package_signature(tampered_package)
    assert is_valid_t is False
    assert "改ざん" in msg_t or "mismatch" in msg_t.lower()

    # 3. Tampered celestial body
    tampered_sys = [
        {
            "system_address": 12345,
            "star_system": "Col 285 Sector Test",
            "bodies": [
                {"body_id": 1, "body_name": "Col 285 Sector Test A", "star_type": "G"},
                {"body_id": 2, "body_name": "Hacked Body Name", "planet_class": "Earthlike body"}
            ]
        }
    ]
    tampered_package_body = dict(package)
    tampered_package_body["systems"] = tampered_sys
    is_valid_b, _ = verify_package_signature(tampered_package_body)
    assert is_valid_b is False

def test_standalone_html_generation():
    sys_data = {
        "star_system": "Eol Prou Test",
        "main_star_type": "K",
        "star_pos_x": 100.0,
        "star_pos_y": -50.0,
        "star_pos_z": 300.0,
        "total_fss_value": 1500000,
        "total_potential_value": 4500000,
        "total_bio_signals": 3
    }
    bodies = [
        {"body_id": 1, "body_name": "Eol Prou Test A", "star_type": "K", "distance_from_arrival_ls": 0},
        {"body_id": 2, "body_name": "Eol Prou Test 1", "planet_class": "High metal content world", "radius": 4500000, "surface_gravity_g": 1.1, "landable": 1, "bio_signals": 3}
    ]
    mining_sites = [
        {"latitude": -12.3456, "longitude": 45.6789, "body_name": "Eol Prou Test 1", "commodities": ["Tungsten", "Molybdenum"]}
    ]
    bookmarks = [
        {"body_id": 2, "alias_name": "Mining Haven", "note_markdown": "Rich in high tier raw materials."}
    ]

    html_out = generate_standalone_html(sys_data, bodies, mining_sites, bookmarks, cmdr_name="Yonaki")
    assert "<!DOCTYPE html>" in html_out
    assert "Eol Prou Test" in html_out
    assert "CMDR Yonaki" in html_out
    assert "Mining Haven" in html_out
    assert "Tungsten" in html_out
    assert '<script type="application/json" id="ed-system-astrophysics-data">' in html_out
    assert "ED_JOURNAL_ANALYZER_ASTROPHYSICS_DATA_V1" in html_out
    assert "生成AI（LLM）天体物理分析" in html_out
    # Check that no external script or stylesheet links exist
    assert "<script src=" not in html_out
    assert '<link rel="stylesheet"' not in html_out

def test_package_export_and_import():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    cursor = conn.cursor()
    # Insert a test system and body
    cursor.execute("""
        INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, main_star_type, total_potential_value)
        VALUES (999001, 'Praea Euq AB-C d1', 500.0, -100.0, 1200.0, 'F', 2800000)
    """)
    cursor.execute("""
        INSERT INTO bodies (system_address, body_id, body_name, star_system, planet_class, radius, surface_gravity_g, was_discovered, was_mapped)
        VALUES (999001, 1, 'Praea Euq AB-C d1 1', 'Praea Euq AB-C d1', 'Earthlike body', 6371000, 1.0, 0, 1)
    """)
    cursor.execute("""
        INSERT INTO surface_mining_activities (system_address, star_system, body_id, body_name, material_name, latitude, longitude, timestamp)
        VALUES (999001, 'Praea Euq AB-C d1', 1, 'Praea Euq AB-C d1 1', 'Selenium', 10.5, -20.5, '2026-09-01T12:00:00Z')
    """)
    conn.commit()

    # Create export package
    pkg = create_edsys_package(conn, [999001], cmdr_name="Explorer A", notes="Shared test exploration system")
    assert pkg["format"] == "ED_JOURNAL_ANALYZER_PACKAGE_V1"
    assert len(pkg["systems"]) == 1
    assert pkg["metadata"]["cmdr_name"] == "Explorer A"

    # Now import into a fresh recipient database
    dest_conn = sqlite3.connect(":memory:")
    dest_conn.row_factory = sqlite3.Row
    init_db(dest_conn)

    res = import_edsys_package(dest_conn, pkg)
    assert res["success"] is True
    assert res["imported_systems"] == 1
    assert res["imported_bodies"] == 1

    # Verify recipient's body has was_discovered = 1 (never triggers false first-discovery for recipient)
    dest_cursor = dest_conn.cursor()
    dest_cursor.execute("SELECT was_discovered, was_mapped FROM bodies WHERE system_address = 999001 AND body_id = 1")
    b_imported = dest_cursor.fetchone()
    assert b_imported["was_discovered"] == 1

def test_api_export_and_import_endpoints():
    from fastapi.testclient import TestClient
    from app.server.api import app
    from app.db.database import get_db_connection, init_db

    client = TestClient(app)

    # Insert test system in real DB after init_db
    conn = get_db_connection()
    init_db(conn)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, main_star_type, total_potential_value)
        VALUES (888123, 'Test API System', 10.0, 20.0, 30.0, 'M', 123456)
    """)
    c.execute("""
        INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_system, planet_class, was_discovered, was_mapped)
        VALUES (888123, 1, 'Test API System 1', 'Test API System', 'Icy body', 1, 1)
    """)
    conn.commit()
    conn.close()

    # 1. Test HTML export endpoint
    html_resp = client.get("/api/export/html/888123?cmdr_name=Tester")
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
    assert "Test API System" in html_resp.text

    # 2. Test package export without consent (should fail with 400)
    fail_resp = client.post("/api/export/package", json={
        "system_addresses": [888123],
        "consent_token": False
    })
    assert fail_resp.status_code == 400
    assert "同意" in fail_resp.json()["error"] or "Lock" in fail_resp.json()["error"]

    # 3. Test package export with consent (success)
    ok_resp = client.post("/api/export/package", json={
        "system_addresses": [888123],
        "cmdr_name": "CMDR Test",
        "notes": "Test notes",
        "consent_token": True
    })
    assert ok_resp.status_code == 200
    pkg_data = ok_resp.json()
    assert pkg_data["format"] == "ED_JOURNAL_ANALYZER_PACKAGE_V1"
    assert len(pkg_data["systems"]) == 1

    # 4. Test preview endpoint
    prev_resp = client.post("/api/import/package/preview", json=pkg_data)
    assert prev_resp.status_code == 200
    pdata = prev_resp.json()
    assert pdata["is_valid"] is True
    assert pdata["system_count"] == 1
    assert pdata["cmdr_name"] == "CMDR Test"

    # 5. Test toggle shared endpoint
    toggle_resp = client.post("/api/systems/888123/toggle-shared")
    assert toggle_resp.status_code == 200
    assert "is_shared" in toggle_resp.json()

    # 6. Test save-local package endpoint
    save_fail = client.post("/api/export/package/save-local", json={
        "system_addresses": [888123],
        "consent_token": False
    })
    assert save_fail.status_code == 400

    save_ok = client.post("/api/export/package/save-local", json={
        "system_addresses": [888123],
        "cmdr_name": "CMDR Test",
        "notes": "Test notes",
        "consent_token": True,
        "reveal": False
    })
    assert save_ok.status_code == 200
    res_json = save_ok.json()
    assert res_json["status"] == "success"
    assert "saved_path" in res_json
    assert os.path.exists(res_json["saved_path"])
    # Clean up created file
    try:
        os.remove(res_json["saved_path"])
    except OSError:
        pass

    # 7. Test preview with wrapped package_data
    wrapped_prev = client.post("/api/import/package/preview", json={"package_data": pkg_data})
    assert wrapped_prev.status_code == 200
    wp_data = wrapped_prev.json()
    assert wp_data["is_valid"] is True
    assert wp_data["signature_valid"] is True
    assert wp_data["total_bodies"] == 1
    assert wp_data["created_by"] == "CMDR Test"

    # 8. Test execute with wrapped package_data
    exec_resp = client.post("/api/import/package/execute", json={
        "package_data": pkg_data,
        "consent_token": True,
        "overwrite": True
    })
    assert exec_resp.status_code == 200
    assert exec_resp.json()["success"] is True
