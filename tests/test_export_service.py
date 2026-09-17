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
    generate_share_snippet,
    has_special_orbits,
    extract_system_ring_summary,
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
    # Check astrophysical parameters summary exists without AI inference label
    assert "詳細天体物理パラメータ" in html_out
    assert "(AI推論用)" not in html_out
    assert "（AI推論用）" not in html_out
    # Check that no external script or stylesheet links exist
    assert "<script src=" not in html_out
    assert '<link rel="stylesheet"' not in html_out

def test_interactive_orrery_binary_and_moons():
    sys_data = {
        "star_system": "Col 285 Binary System",
        "main_star_type": "G",
        "star_pos_x": 10.0,
        "star_pos_y": 20.0,
        "star_pos_z": 30.0,
        "total_fss_value": 2500000,
        "total_potential_value": 5000000,
        "total_bio_signals": 2
    }
    bodies = [
        {"body_id": 1, "body_name": "Col 285 Binary System A", "star_type": "G", "distance_from_arrival_ls": 0},
        {"body_id": 2, "body_name": "Col 285 Binary System A 1", "planet_class": "High metal content world", "distance_from_arrival_ls": 150, "semi_major_axis": 44800000000},
        {"body_id": 3, "body_name": "Col 285 Binary System B", "star_type": "M", "distance_from_arrival_ls": 12500, "semi_major_axis": 3747000000000},
        {"body_id": 4, "body_name": "Col 285 Binary System B 1", "planet_class": "Icy body", "distance_from_arrival_ls": 12550, "semi_major_axis": 15000000000},
        {"body_id": 5, "body_name": "Col 285 Binary System B 1 a", "planet_class": "Rocky body", "distance_from_arrival_ls": 12551, "semi_major_axis": 450000000}
    ]
    html_out = generate_standalone_html(sys_data, bodies, [], [], cmdr_name="Yonaki")

    # Verify Companion Star B exists in Orrery
    assert "Col 285 Binary System B" in html_out
    # Verify Companion Planet B 1 exists in Orrery
    assert "Col 285 Binary System B 1" in html_out
    # Verify Moon B 1 a exists in Orrery
    assert "Col 285 Binary System B 1 a" in html_out
    # Verify Quick Jump buttons for both Star A and Star B (default JA)
    assert "主星 A" in html_out
    assert "伴星 B" in html_out
    # Verify Zoom / Pan UI controls and SVG interactive layer
    assert 'id="interactive-orrery-svg"' in html_out
    assert 'id="orrery-pan-zoom-layer"' in html_out
    assert 'id="orrery-wrapper"' in html_out
    assert 'zoomOrrery' in html_out
    assert 'resetOrreryView' in html_out

    # Test English Orrery
    html_en = generate_standalone_html(sys_data, bodies, [], [], cmdr_name="Yonaki", lang="en")
    assert "Primary A" in html_en
    assert "Companion B" in html_en
    assert "Zoom In" in html_en
    assert "Zoom Out" in html_en
    assert "Reset" in html_en


def test_standalone_html_generation_english():
    sys_data = {
        "star_system": "Eol Prou Test EN",
        "main_star_type": "K",
        "star_pos_x": 100.0,
        "star_pos_y": -50.0,
        "star_pos_z": 300.0,
        "total_fss_value": 1500000,
        "total_potential_value": 4500000,
        "total_bio_signals": 3
    }
    bodies = [
        {"body_id": 1, "body_name": "Eol Prou Test EN A", "star_type": "K", "distance_from_arrival_ls": 0, "stellar_mass": 0.8},
        {"body_id": 2, "body_name": "Eol Prou Test EN 1", "planet_class": "High metal content world", "radius": 4500000, "surface_gravity_g": 1.1, "landable": 1, "bio_signals": 3, "semi_major_axis": 149597870700, "orbital_period": 864000}
    ]
    mining_sites = [
        {"latitude": -12.3456, "longitude": 45.6789, "body_name": "Eol Prou Test EN 1", "commodities": ["Tungsten", "Molybdenum"]}
    ]
    bookmarks = [
        {"body_id": 2, "alias_name": "Mining Haven", "note_markdown": "Rich in high tier raw materials."}
    ]

    html_out = generate_standalone_html(sys_data, bodies, mining_sites, bookmarks, cmdr_name="Yonaki", lang="en")
    assert '<html lang="en">' in html_out
    assert "Coordinates:" in html_out
    assert "Sol Distance:" in html_out
    assert "Main Star:" in html_out
    assert "Generative AI (LLM) Astrophysical Analysis" in html_out
    assert "Full Observation JSON Embedded" in html_out
    assert "Estimated Max Value" in html_out
    assert "FSS Scan Value" in html_out
    assert "Celestial Bodies" in html_out
    assert "Bio Signals" in html_out
    assert "System Composition & Survey Inventory" in html_out
    assert "Body Name" in html_out
    assert "Class / Tag" in html_out
    assert "Distance" in html_out
    assert "Gravity" in html_out
    assert "Surface Temp" in html_out
    assert "Atmosphere" in html_out
    assert "Scan Value" in html_out
    assert "Detailed Astrophysical Parameters" in html_out
    assert "(AI推論用)" not in html_out
    assert "（AI推論用）" not in html_out
    assert "Mass:" in html_out
    assert "Radius:" in html_out
    assert "Semi-Major Axis:" in html_out
    assert "Orbital Period:" in html_out
    assert "Rhino SRV Surface Mining Sites" in html_out
    assert "Extracted Materials:" in html_out


def test_has_special_orbits():
    # 1. Normal system with standard circular orbits
    normal_bodies = [
        {"body_name": "Sol 1", "eccentricity": 0.02, "axial_tilt": 0.1, "planet_class": "High metal content world"},
        {"body_name": "Sol 2", "eccentricity": 0.05, "axial_tilt": 0.2, "planet_class": "Rocky body"}
    ]
    assert has_special_orbits(normal_bodies) is False

    # 2. Extreme eccentricity (e >= 0.35)
    eccentric_bodies = [
        {"body_name": "Sol 1", "eccentricity": 0.75, "planet_class": "High metal content world"}
    ]
    assert has_special_orbits(eccentric_bodies) is True

    # 3. Extreme axial tilt (> 80 degrees / retrograde)
    import math
    tilted_bodies = [
        {"body_name": "Sol 1", "axial_tilt": math.radians(95.0), "planet_class": "Icy body"}
    ]
    assert has_special_orbits(tilted_bodies) is True

    # 4. Hot Jupiter (gas giant with orbital period < 3 days)
    hot_jupiter_bodies = [
        {"body_name": "Sol 1", "orbital_period": 86400 * 1.5, "planet_class": "Gas giant with water based life"}
    ]
    assert has_special_orbits(hot_jupiter_bodies) is True

    # 5. Sub-moon (nested moon 1 a a)
    submoon_bodies = [
        {"body_name": "Sol 1 a a", "planet_class": "Rocky body"}
    ]
    assert has_special_orbits(submoon_bodies) is True


def test_generate_share_snippet_ja_and_en():
    sys_data = {
        "system_address": 777999,
        "star_system": "Synuefe CE-R c21-6",
        "main_star_type": "K",
        "star_pos_x": 125.4,
        "star_pos_y": -32.1,
        "star_pos_z": 890.5,
        "total_bio_signals": 5
    }
    bodies = [
        {"body_id": 1, "body_name": "Synuefe CE-R c21-6 A", "star_type": "K"},
        {"body_id": 2, "body_name": "Synuefe CE-R c21-6 1", "planet_class": "Earthlike body", "geo_signals": 3},
        {"body_id": 3, "body_name": "Synuefe CE-R c21-6 2", "planet_class": "Water world", "rings": '[{"Name": "Ring A", "RingClass": "eRingClass_Metallic"}]'},
        {"body_id": 4, "body_name": "Synuefe CE-R c21-6 3", "planet_class": "High metal content world", "eccentricity": 0.55}
    ]

    # Japanese snippet
    snippet_ja = generate_share_snippet(sys_data, bodies, lang="ja")
    assert "Synuefe CE-R c21-6" in snippet_ja
    assert "主星: K型" in snippet_ja
    assert "座標: [125.4, -32.1, 890.5]" in snippet_ja
    assert "ELW: 1" in snippet_ja
    assert "水の世界: 1" in snippet_ja
    assert "生体: 5箇所" in snippet_ja
    assert "地質: 3箇所" in snippet_ja
    assert "環: あり" in snippet_ja
    assert "特殊な天体軌道あり" in snippet_ja
    assert "https://spansh.co.uk/system/777999" in snippet_ja
    # Must NOT reveal Orrery or Cr
    assert "Orrery" not in snippet_ja
    assert "Cr" not in snippet_ja

    # English snippet
    snippet_en = generate_share_snippet(sys_data, bodies, lang="en")
    assert "Synuefe CE-R c21-6" in snippet_en
    assert "Main Star: Class K" in snippet_en
    assert "Coords: [125.4, -32.1, 890.5]" in snippet_en
    assert "ELW: 1" in snippet_en
    assert "Water World: 1" in snippet_en
    assert "Bio: 5" in snippet_en
    assert "Geo: 3" in snippet_en
    assert "Rings: Yes" in snippet_en
    assert "Special Orbits Detected" in snippet_en
    assert "https://spansh.co.uk/system/777999" in snippet_en


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

    # 1. Test HTML export endpoint (default ja and en)
    html_resp = client.get("/api/export/html/888123?cmdr_name=Tester")
    assert html_resp.status_code == 200
    assert "text/html" in html_resp.headers["content-type"]
    assert "Test API System" in html_resp.text
    assert '<html lang="ja">' in html_resp.text

    html_en_resp = client.get("/api/export/html/888123?cmdr_name=Tester&lang=en")
    assert html_en_resp.status_code == 200
    assert '<html lang="en">' in html_en_resp.text
    assert "Coordinates:" in html_en_resp.text

    # 1b. Test snippet export endpoint
    snip_resp = client.get("/api/export/snippet/888123?lang=ja")
    assert snip_resp.status_code == 200
    assert snip_resp.json()["status"] == "ok"
    assert "Test API System" in snip_resp.json()["snippet"]
    assert "主星:" in snip_resp.json()["snippet"]

    snip_en_resp = client.get("/api/export/snippet/888123?lang=en")
    assert snip_en_resp.status_code == 200
    assert "Main Star:" in snip_en_resp.json()["snippet"]

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
