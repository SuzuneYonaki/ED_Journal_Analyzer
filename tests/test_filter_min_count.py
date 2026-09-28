import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.db.database import get_db_connection, init_db
from app.server.api import app, _parse_filter_min_count


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_parse_filter_min_count():
    # Inactive / Falsey inputs
    assert _parse_filter_min_count(None) == 0
    assert _parse_filter_min_count(False) == 0
    assert _parse_filter_min_count("") == 0
    assert _parse_filter_min_count("false") == 0
    assert _parse_filter_min_count("False") == 0
    assert _parse_filter_min_count("0") == 0
    assert _parse_filter_min_count(0) == 0
    assert _parse_filter_min_count("-1") == 0
    assert _parse_filter_min_count("invalid") == 0

    # Truthy / Boolean inputs
    assert _parse_filter_min_count(True) == 1
    assert _parse_filter_min_count("true") == 1
    assert _parse_filter_min_count("True") == 1
    assert _parse_filter_min_count(1) == 1
    assert _parse_filter_min_count("1") == 1

    # Numeric counts >= 2
    assert _parse_filter_min_count(2) == 2
    assert _parse_filter_min_count("2") == 2
    assert _parse_filter_min_count(5) == 5
    assert _parse_filter_min_count("5") == 5
    assert _parse_filter_min_count(10) == 10


def test_ui_and_i18n_assets():
    base_dir = Path(__file__).resolve().parent.parent

    # 1. CSS contains count badge and popover styles
    css_path = base_dir / "app" / "ui" / "css" / "style.css"
    css_content = css_path.read_text(encoding="utf-8")
    assert ".chip-count-badge" in css_content
    assert ".filter-count-popover" in css_content

    # 2. i18n contains localized strings
    i18n_path = base_dir / "app" / "ui" / "js" / "i18n.js"
    i18n_content = i18n_path.read_text(encoding="utf-8")
    assert "filter_min_count_title" in i18n_content
    assert "filter_count_reset" in i18n_content
    assert "filter_count_quick" in i18n_content

    # 3. app.js contains logic and listeners
    app_js_path = base_dir / "app" / "ui" / "js" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8")
    assert "COUNTABLE_FILTERS" in app_js
    assert "updateFilterChipUI" in app_js
    assert "showFilterCountPopover" in app_js


def test_api_filter_min_count(client):
    init_db()
    sys_a = 999000111001
    sys_b = 999000111002

    with get_db_connection() as conn:
        # Setup Test System A: 1 ELW, 2 Water Worlds, 1 Bio
        conn.execute(
            """
            INSERT OR REPLACE INTO systems (
                system_address, star_system, has_elw, has_water_world, has_bio, total_bio_signals
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sys_a, "FilterCount-System-A", 1, 1, 1, 1)
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_a,))
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class)
            VALUES (?, ?, ?, ?)
            """,
            (sys_a, 1, "Body A 1", "Earthlike body")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class)
            VALUES (?, ?, ?, ?)
            """,
            (sys_a, 2, "Body A 2", "Water world")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class)
            VALUES (?, ?, ?, ?)
            """,
            (sys_a, 3, "Body A 3", "Water world")
        )

        # Setup Test System B: 2 ELWs, 1 Water World, 3 Bios
        conn.execute(
            """
            INSERT OR REPLACE INTO systems (
                system_address, star_system, has_elw, has_water_world, has_bio, total_bio_signals
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (sys_b, "FilterCount-System-B", 1, 1, 1, 3)
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_b,))
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class)
            VALUES (?, ?, ?, ?)
            """,
            (sys_b, 1, "Body B 1", "Earth-like world")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class)
            VALUES (?, ?, ?, ?)
            """,
            (sys_b, 2, "Body B 2", "Earthlike body")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, planet_class)
            VALUES (?, ?, ?, ?)
            """,
            (sys_b, 3, "Body B 3", "Water world")
        )
        conn.commit()

    # Query 1: has_elw=true / 1 -> both systems returned
    res = client.get("/api/systems?q=FilterCount-System&has_elw=true")
    assert res.status_code == 200
    items = res.json()["systems"]
    sys_names = [s["star_system"] for s in items]
    assert "FilterCount-System-A" in sys_names
    assert "FilterCount-System-B" in sys_names

    # Query 2: has_elw=2 -> only System B returned
    res = client.get("/api/systems?q=FilterCount-System&has_elw=2")
    assert res.status_code == 200
    items = res.json()["systems"]
    filtered_names = [s["star_system"] for s in items]
    assert filtered_names == ["FilterCount-System-B"]

    # Query 3: has_water_world=2 -> only System A returned
    res = client.get("/api/systems?q=FilterCount-System&has_water_world=2")
    assert res.status_code == 200
    items = res.json()["systems"]
    filtered_names = [s["star_system"] for s in items]
    assert filtered_names == ["FilterCount-System-A"]

    # Query 4: has_bio=2 -> only System B returned (total_bio_signals = 3 >= 2)
    res = client.get("/api/systems?q=FilterCount-System&has_bio=2")
    assert res.status_code == 200
    items = res.json()["systems"]
    filtered_names = [s["star_system"] for s in items]
    assert filtered_names == ["FilterCount-System-B"]

    # Cleanup test systems
    with get_db_connection() as conn:
        conn.execute("DELETE FROM bodies WHERE system_address IN (?, ?)", (sys_a, sys_b))
        conn.execute("DELETE FROM systems WHERE system_address IN (?, ?)", (sys_a, sys_b))
        conn.commit()
