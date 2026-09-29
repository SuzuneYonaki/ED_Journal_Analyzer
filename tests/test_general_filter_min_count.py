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


def test_countable_filters_set():
    base_dir = Path(__file__).resolve().parent.parent
    app_js_path = base_dir / "app" / "ui" / "js" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8")

    assert "'has_bookmarks'" in app_js
    assert "'has_anomalies'" in app_js
    assert "'has_ggg'" in app_js


def test_api_general_filter_min_count(client):
    init_db()
    sys_a = 999222333001
    sys_b = 999222333002
    sys_c = 999222333003

    with get_db_connection() as conn:
        # System A: 1 bookmark, 2 non-GGG anomalies, 0 GGG
        conn.execute(
            "INSERT OR REPLACE INTO systems (system_address, star_system, has_anomalies) VALUES (?, ?, ?)",
            (sys_a, "GenCount-System-A", 1)
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_a,))
        conn.execute("DELETE FROM body_bookmarks WHERE system_address = ?", (sys_a,))
        conn.execute(
            """
            INSERT INTO body_bookmarks (system_address, star_system, body_id, body_name, alias_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (sys_a, "GenCount-System-A", 1, "Body A 1", "BM A1")
        )
        conn.execute(
            "INSERT INTO bodies (system_address, body_id, body_name, anomalies_json) VALUES (?, ?, ?, ?)",
            (sys_a, 1, "Body A 1", '["giant_ring"]')
        )
        conn.execute(
            "INSERT INTO bodies (system_address, body_id, body_name, anomalies_json) VALUES (?, ?, ?, ?)",
            (sys_a, 2, "Body A 2", '["rare_atmosphere"]')
        )

        # System B: 2 bookmarks, 1 anomaly (1 GGG), 1 GGG
        conn.execute(
            "INSERT OR REPLACE INTO systems (system_address, star_system, has_anomalies) VALUES (?, ?, ?)",
            (sys_b, "GenCount-System-B", 1)
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_b,))
        conn.execute("DELETE FROM body_bookmarks WHERE system_address = ?", (sys_b,))
        conn.execute(
            """
            INSERT INTO body_bookmarks (system_address, star_system, body_id, body_name, alias_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (sys_b, "GenCount-System-B", 1, "Body B 1", "BM B1")
        )
        conn.execute(
            """
            INSERT INTO body_bookmarks (system_address, star_system, body_id, body_name, alias_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (sys_b, "GenCount-System-B", 2, "Body B 2", "BM B2")
        )
        conn.execute(
            "INSERT INTO bodies (system_address, body_id, body_name, anomalies_json) VALUES (?, ?, ?, ?)",
            (sys_b, 1, "Body B 1", '["Confirmed GGG"]')
        )

        # System C: 0 bookmarks, 2 anomalies (2 GGGs), 2 GGGs
        conn.execute(
            "INSERT OR REPLACE INTO systems (system_address, star_system, has_anomalies) VALUES (?, ?, ?)",
            (sys_c, "GenCount-System-C", 1)
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_c,))
        conn.execute("DELETE FROM body_bookmarks WHERE system_address = ?", (sys_c,))
        conn.execute(
            "INSERT INTO bodies (system_address, body_id, body_name, anomalies_json) VALUES (?, ?, ?, ?)",
            (sys_c, 1, "Body C 1", '["Confirmed GGG"]')
        )
        conn.execute(
            "INSERT INTO bodies (system_address, body_id, body_name, anomalies_json) VALUES (?, ?, ?, ?)",
            (sys_c, 2, "Body C 2", '["Confirmed GGG"]')
        )
        conn.commit()

    # Query 1: has_bookmarks=1 -> A and B
    res = client.get("/api/systems?q=GenCount-System&has_bookmarks=1")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "GenCount-System-A" in names
    assert "GenCount-System-B" in names
    assert "GenCount-System-C" not in names

    # Query 2: has_bookmarks=2 -> only B
    res = client.get("/api/systems?q=GenCount-System&has_bookmarks=2")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["GenCount-System-B"]

    # Query 3: has_anomalies=2 -> A and C (B only has 1)
    res = client.get("/api/systems?q=GenCount-System&has_anomalies=2")
    assert res.status_code == 200
    names = sorted([s["star_system"] for s in res.json()["systems"]])
    assert names == ["GenCount-System-A", "GenCount-System-C"]

    # Query 4: has_ggg=2 -> only C
    res = client.get("/api/systems?q=GenCount-System&has_ggg=2")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["GenCount-System-C"]

    # Cleanup
    with get_db_connection() as conn:
        conn.execute("DELETE FROM body_bookmarks WHERE system_address IN (?, ?, ?)", (sys_a, sys_b, sys_c))
        conn.execute("DELETE FROM bodies WHERE system_address IN (?, ?, ?)", (sys_a, sys_b, sys_c))
        conn.execute("DELETE FROM systems WHERE system_address IN (?, ?, ?)", (sys_a, sys_b, sys_c))
        conn.commit()
