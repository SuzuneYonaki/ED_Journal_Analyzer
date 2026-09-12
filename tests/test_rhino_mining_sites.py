import os
import tempfile
import pytest
from fastapi.testclient import TestClient

os.environ["ED_JOURNAL_DIR"] = tempfile.mkdtemp()
from app.db.database import (
    get_db_connection, init_db, is_same_mining_site,
    save_or_merge_mining_site, get_mining_sites,
    add_manual_mining_site, update_mining_site, delete_mining_site
)
from app.server.api import app
from app.parser.journal_parser import JournalParser


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_is_same_mining_site_top_2_digits_grouping():
    """
    User rule: '上2桁が同じ場合は採掘場所は同じ箇所として（素材をマージ）、別の場合は新たに記録'
    (~0.2 deg difference and matching top 2 digits)
    """
    # 1. Nearby coordinates with matching integer part
    assert is_same_mining_site(12.3456, -45.6789, 12.3800, -45.7200) is True
    assert is_same_mining_site(12.3456, -45.6789, 12.4500, -45.7500) is True

    # 2. Different locations (different top 2 digits / > 0.2 deg)
    assert is_same_mining_site(12.3456, -45.6789, 15.3456, -45.6789) is False
    assert is_same_mining_site(12.3456, -45.6789, 12.3456, -48.6789) is False

    # 3. Different hemispheres
    assert is_same_mining_site(12.3456, -45.6789, -12.3456, -45.6789) is False
    assert is_same_mining_site(12.3456, -45.6789, 12.3456, 45.6789) is False

    # 4. Near equator / zero meridian within threshold
    assert is_same_mining_site(0.05, 0.05, 0.12, 0.15) is True
    assert is_same_mining_site(0.05, 0.05, 1.50, 0.05) is False


def test_save_or_merge_mining_site_merging():
    """
    Verify that save_or_merge_mining_site:
    - Creates a new site when no matching site exists.
    - Merges minerals into the existing site when coordinates match top 2 digits.
    - Creates a separate site when coordinates are clearly distinct.
    """
    init_db()
    conn = get_db_connection()
    sys_addr = 9988776655
    body_id = 1
    star_sys = "Test System Alpha"
    body_name = "Test Body 1"

    conn.execute("DELETE FROM surface_mining_sites WHERE system_address = ?", (sys_addr,))
    conn.commit()

    # Event 1: Initial mining at (12.3456, -45.6789)
    site_id_1 = save_or_merge_mining_site(
        conn=conn,
        system_address=sys_addr,
        star_system=star_sys,
        body_id=body_id,
        body_name=body_name,
        latitude=12.3456,
        longitude=-45.6789,
        material_name="Iron"
    )
    assert site_id_1 is not None

    sites = get_mining_sites(conn, sys_addr, body_id)
    assert len(sites) == 1
    assert sites[0]["id"] == site_id_1
    assert "Iron" in sites[0]["commodities"]

    # Event 2: Mining nearby (12.3900, -45.7100) with Nickel -> should merge
    site_id_2 = save_or_merge_mining_site(
        conn=conn,
        system_address=sys_addr,
        star_system=star_sys,
        body_id=body_id,
        body_name=body_name,
        latitude=12.3900,
        longitude=-45.7100,
        material_name="Nickel"
    )
    assert site_id_2 == site_id_1

    sites = get_mining_sites(conn, sys_addr, body_id)
    assert len(sites) == 1
    assert "Iron" in sites[0]["commodities"]
    assert "Nickel" in sites[0]["commodities"]

    # Event 3: Mining at a distant location (35.0000, 110.0000) -> should create a new site
    site_id_3 = save_or_merge_mining_site(
        conn=conn,
        system_address=sys_addr,
        star_system=star_sys,
        body_id=body_id,
        body_name=body_name,
        latitude=35.0000,
        longitude=110.0000,
        material_name="Germanium"
    )
    assert site_id_3 != site_id_1

    sites = get_mining_sites(conn, sys_addr, body_id)
    assert len(sites) == 2
    conn.close()


def test_api_mining_sites_crud(client):
    """
    Test GET, POST, PUT, DELETE /api/mining_sites
    """
    sys_addr = 7788990011
    star_sys = "CRUD Test System"
    body_id = 3
    body_name = "CRUD Planet 3"

    with get_db_connection() as conn:
        conn.execute("DELETE FROM surface_mining_sites WHERE system_address = ?", (sys_addr,))
        conn.execute("INSERT OR REPLACE INTO systems (system_address, star_system) VALUES (?, ?)", (sys_addr, star_sys))
        conn.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_system, landable) VALUES (?, ?, ?, ?, 1)", (sys_addr, body_id, body_name, star_sys))
        conn.commit()

    # 1. Create site via POST
    create_res = client.post("/api/mining_sites", json={
        "system_address": sys_addr,
        "star_system": star_sys,
        "body_id": body_id,
        "body_name": body_name,
        "latitude": 24.5678,
        "longitude": -80.1234,
        "hotspot": "Hotspot 1",
        "minerals": "Iron, Manganese",
        "note": "Initial crater survey"
    })
    assert create_res.status_code == 200, create_res.text
    site_id = create_res.json()["site_id"]

    # 2. Read sites via GET
    get_res = client.get(f"/api/mining_sites/{sys_addr}?body_id={body_id}")
    assert get_res.status_code == 200
    sites_data = get_res.json()["sites"]
    assert len(sites_data) >= 1
    target = next((s for s in sites_data if s["id"] == site_id), None)
    assert target is not None
    assert abs(target["latitude"] - 24.5678) < 1e-4
    assert abs(target["longitude"] - (-80.1234)) < 1e-4
    assert target["hotspot"] == "Hotspot 1"
    assert "Iron" in target["commodities"]
    assert "Manganese" in target["commodities"]
    assert target["note"] == "Initial crater survey"

    # 3. Update site via PUT
    put_res = client.put(f"/api/mining_sites/{site_id}", json={
        "latitude": 24.5800,
        "longitude": -80.1400,
        "hotspot": "Painite Hotspot",
        "minerals": "Iron, Manganese, Polonium",
        "note": "Updated survey: rich deposit found"
    })
    assert put_res.status_code == 200

    # Verify update
    get_res2 = client.get(f"/api/mining_sites/{sys_addr}?body_id={body_id}")
    sites_data2 = get_res2.json()["sites"]
    target2 = next((s for s in sites_data2 if s["id"] == site_id), None)
    assert target2 is not None
    assert abs(target2["latitude"] - 24.5800) < 1e-4
    assert target2["hotspot"] == "Painite Hotspot"
    assert "Polonium" in target2["commodities"]
    assert target2["note"] == "Updated survey: rich deposit found"

    # 4. Verify in get_system_detail
    sys_res = client.get(f"/api/system/{sys_addr}")
    assert sys_res.status_code == 200
    sys_payload = sys_res.json()
    assert "rhino_mining_sites" in sys_payload
    assert any(s["id"] == site_id for s in sys_payload["rhino_mining_sites"])
    b_obj = next((b for b in sys_payload["bodies"] if b["body_id"] == body_id), None)
    assert b_obj is not None
    assert any(s["id"] == site_id for s in b_obj.get("rhino_mining_sites", []))
    b_site = next((s for s in b_obj.get("rhino_mining_sites", []) if s["id"] == site_id), None)
    assert b_site is not None
    assert b_site["hotspot"] == "Painite Hotspot"

    # 5. Delete site via DELETE
    del_res = client.delete(f"/api/mining_sites/{site_id}")
    assert del_res.status_code == 200

    # Verify deletion
    get_res3 = client.get(f"/api/mining_sites/{sys_addr}?body_id={body_id}")
    assert not any(s["id"] == site_id for s in get_res3.json()["sites"])


def test_journal_parser_live_mining_saves_to_surface_mining_sites():
    """
    Verify that live MaterialCollected in SRV creates records in surface_mining_sites table
    and does not spam body_bookmarks.note_markdown.
    """
    init_db()
    conn = get_db_connection()
    sys_addr = 6655443322
    body_id = 5
    star_sys = "Live Dedicated Mining Sys"
    body_name = "Live Mining Body 5"

    conn.execute("DELETE FROM surface_mining_sites WHERE system_address = ?", (sys_addr,))
    conn.execute("DELETE FROM body_bookmarks WHERE system_address = ?", (sys_addr,))
    conn.execute("INSERT OR REPLACE INTO systems (system_address, star_system) VALUES (?, ?)", (sys_addr, star_sys))
    conn.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_system, landable) VALUES (?, ?, ?, ?, 1)", (sys_addr, body_id, body_name, star_sys))
    conn.commit()

    parser = JournalParser(db_conn=conn, is_live=True)
    parser.current_system_address = sys_addr
    parser.current_star_system = star_sys
    parser.current_body_id = body_id
    parser.current_body_name = body_name
    parser.in_srv = True
    parser.current_latitude = 40.1234
    parser.current_longitude = -120.5678

    # Process MaterialCollected
    parser.process_journal_line('{"timestamp":"2026-09-13T01:00:00Z","event":"MaterialCollected","Category":"Raw","Name":"vanadium","Name_Localised":"Vanadium","Count":1}')
    
    # Process nearby MaterialCollected
    parser.current_latitude = 40.1500
    parser.current_longitude = -120.5900
    parser.process_journal_line('{"timestamp":"2026-09-13T01:02:00Z","event":"MaterialCollected","Category":"Raw","Name":"chromium","Name_Localised":"Chromium","Count":1}')

    # Verify surface_mining_sites table has the merged site
    sites = get_mining_sites(conn, sys_addr, body_id)
    assert len(sites) == 1
    assert "Vanadium" in sites[0]["commodities"]
    assert "Chromium" in sites[0]["commodities"]

    # Verify body_bookmarks has NOT been automatically polluted with markdown notes
    row = conn.execute("SELECT note_markdown FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (sys_addr, body_id)).fetchone()
    assert row is None or not row["note_markdown"], "body_bookmarks note should not be polluted automatically"

    conn.close()
