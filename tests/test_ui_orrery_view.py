import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.server.api import app
from app.db.database import get_db_connection

client = TestClient(app)

def test_center_pane_button_order_and_orrery():
    pane_path = Path("app/ui/components/center_pane.html")
    assert pane_path.exists(), "center_pane.html must exist"
    content = pane_path.read_text(encoding="utf-8")

    assert 'id="btn-view-orrery"' in content

    # Check button ordering: sysmap -> flat -> orrery -> bio -> mining -> visits -> physics
    idx_sysmap = content.index('id="btn-view-sysmap"')
    idx_flat = content.index('id="btn-view-flat"')
    idx_orrery = content.index('id="btn-view-orrery"')
    idx_bio = content.index('id="btn-view-bio"')
    idx_mining = content.index('id="btn-view-mining"')
    idx_visits = content.index('id="btn-view-visits"')
    idx_physics = content.index('id="btn-view-physics"')

    assert idx_sysmap < idx_flat < idx_orrery < idx_bio < idx_mining < idx_visits < idx_physics, \
        "Tab ordering must be: System, Celestial, Orrery, Bio, P Mining, Visits, Astro Rarity"

def test_i18n_view_orrery():
    i18n_path = Path("app/ui/js/i18n.js")
    assert i18n_path.exists()
    content = i18n_path.read_text(encoding="utf-8")
    assert "view_orrery:" in content

def test_app_js_orrery_integration():
    app_js_path = Path("app/ui/js/app.js")
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    assert "btn-view-orrery" in content
    assert "currentView === 'orrery'" in content
    assert "renderOrreryView" in content
    assert "initOrreryInteractions" in content

def test_api_system_orrery_endpoint():
    # Insert dummy system and bodies to test endpoint
    sys_addr = 9876543210
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bodies WHERE system_address = ?", (sys_addr,))
        cursor.execute("DELETE FROM systems WHERE system_address = ?", (sys_addr,))
        cursor.execute("""
            INSERT INTO systems (system_address, star_system, main_star_type, star_pos_x, star_pos_y, star_pos_z)
            VALUES (?, 'Orrery Test System', 'G', 10.0, 20.0, 30.0)
        """, (sys_addr,))
        cursor.execute("""
            INSERT INTO bodies (system_address, body_id, body_name, star_type, distance_from_arrival_ls)
            VALUES (?, 1, 'Orrery Test System A', 'G', 0)
        """, (sys_addr,))
        cursor.execute("""
            INSERT INTO bodies (system_address, body_id, body_name, planet_class, distance_from_arrival_ls, surface_gravity_g)
            VALUES (?, 2, 'Orrery Test System A 1', 'High metal content body', 150, 1.05)
        """, (sys_addr,))
        cursor.execute("""
            INSERT INTO bodies (system_address, body_id, body_name, planet_class, distance_from_arrival_ls, surface_gravity_g)
            VALUES (?, 3, 'Orrery Test System A 1 a', 'Rocky body', 150.2, 0.12)
        """, (sys_addr,))
        conn.commit()

    try:
        # Test JA endpoint
        resp_ja = client.get(f"/api/system/{sys_addr}/orrery?lang=ja")
        assert resp_ja.status_code == 200
        data_ja = resp_ja.json()
        assert "html" in data_ja
        html_ja = data_ja["html"]
        assert 'class="orrery-container"' in html_ja
        assert 'interactive-orrery-svg' in html_ja
        assert 'data-body-id="1"' in html_ja
        assert 'data-body-id="2"' in html_ja
        assert 'data-body-id="3"' in html_ja

        # Test EN endpoint
        resp_en = client.get(f"/api/system/{sys_addr}/orrery?lang=en")
        assert resp_en.status_code == 200
        html_en = resp_en.json()["html"]
        assert "Reset" in html_en
    finally:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bodies WHERE system_address = ?", (sys_addr,))
            cursor.execute("DELETE FROM systems WHERE system_address = ?", (sys_addr,))
            conn.commit()
