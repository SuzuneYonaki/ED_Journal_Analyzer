import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.db.database import get_db_connection, init_db
from app.server.api import app


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_celestial_filter_js_wiring():
    base_dir = Path(__file__).resolve().parent.parent

    # 1. left_pane.html contains celestial chips
    left_pane_path = base_dir / "app" / "ui" / "components" / "left_pane.html"
    left_html = left_pane_path.read_text(encoding="utf-8")
    assert 'data-celestial="ringed"' in left_html
    assert 'data-celestial="eccentric"' in left_html

    # 2. app.js contains logic and handlers
    app_js_path = base_dir / "app" / "ui" / "js" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8")

    assert "celestialCounts:" in app_js
    assert "dataset.celestial" in app_js
    assert "showFilterCountPopover(chip, state.celestialCounts[cKey]" in app_js
    assert "state.celestialCounts = {};" in app_js


def test_api_celestial_filter_min_count(client):
    init_db()
    sys_a = 999111222001
    sys_b = 999111222002

    with get_db_connection() as conn:
        # System A: 1 Ringed body, 2 Eccentric bodies
        conn.execute(
            """
            INSERT OR REPLACE INTO systems (system_address, star_system)
            VALUES (?, ?)
            """,
            (sys_a, "CelestialCount-System-A")
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_a,))
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, rings, eccentricity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_a, 1, "Body A 1", json.dumps([{"Name": "A Ring"}]), 0.6)
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, rings, eccentricity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_a, 2, "Body A 2", None, 0.7)
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, rings, eccentricity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_a, 3, "Body A 3", None, 0.1)
        )

        # System B: 2 Ringed bodies, 1 Eccentric body
        conn.execute(
            """
            INSERT OR REPLACE INTO systems (system_address, star_system)
            VALUES (?, ?)
            """,
            (sys_b, "CelestialCount-System-B")
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_b,))
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, rings, eccentricity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_b, 1, "Body B 1", json.dumps([{"Name": "B Ring 1"}]), 0.8)
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, rings, eccentricity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_b, 2, "Body B 2", json.dumps([{"Name": "B Ring 2"}]), 0.05)
        )
        conn.commit()

    # Query 1: standard ringed filter (count=1) -> both match
    res = client.get("/api/systems?q=CelestialCount-System&celestial_filters=ringed")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "CelestialCount-System-A" in names
    assert "CelestialCount-System-B" in names

    # Query 2: ringed:2 -> only System B matches
    res = client.get("/api/systems?q=CelestialCount-System&celestial_filters=ringed:2")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["CelestialCount-System-B"]

    # Query 3: eccentric:2 -> only System A matches
    res = client.get("/api/systems?q=CelestialCount-System&celestial_filters=eccentric:2")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["CelestialCount-System-A"]

    # Query 4: ringed:2,eccentric:1 (AND) -> only System B matches
    res = client.get("/api/systems?q=CelestialCount-System&celestial_filters=ringed:2,eccentric:1&celestial_match_mode=all")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["CelestialCount-System-B"]

    # Query 5: ringed:2,eccentric:2 (OR) -> both match
    res = client.get("/api/systems?q=CelestialCount-System&celestial_filters=ringed:2,eccentric:2&celestial_match_mode=any")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "CelestialCount-System-A" in names
    assert "CelestialCount-System-B" in names

    # Cleanup
    with get_db_connection() as conn:
        conn.execute("DELETE FROM bodies WHERE system_address IN (?, ?)", (sys_a, sys_b))
        conn.execute("DELETE FROM systems WHERE system_address IN (?, ?)", (sys_a, sys_b))
        conn.commit()
