import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.db.database import get_db_connection, init_db
from app.server.api import app


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_star_and_lum_filter_js_wiring():
    base_dir = Path(__file__).resolve().parent.parent

    # 1. app.js contains starCounts and lumCounts in state & fetchSystems
    app_js = (base_dir / "app" / "ui" / "js" / "app.js").read_text(encoding="utf-8")
    assert "starCounts:" in app_js
    assert "lumCounts:" in app_js
    assert "starEntries.map" in app_js
    assert "lumEntries.map" in app_js

    # 2. system_list.js contains contextmenu wiring on the badge chips
    # (stellar type / luminosity filters were converted from
    # checkbox+label to reactive badge chips; right-click-to-set-count
    # is now wired on the chip element itself)
    sys_list = (base_dir / "app" / "ui" / "js" / "system_list.js").read_text(encoding="utf-8")
    assert "state.starCounts[val] =" in sys_list
    assert "state.lumCounts[val] =" in sys_list
    assert "chip.addEventListener('contextmenu'" in sys_list


def test_api_star_and_lum_filter_min_count(client):
    init_db()
    sys_a = 999333444001
    sys_b = 999333444002

    with get_db_connection() as conn:
        # System A: 1 Neutron Star (N), 2 M-class stars (both Lum V)
        conn.execute(
            "INSERT OR REPLACE INTO systems (system_address, star_system) VALUES (?, ?)",
            (sys_a, "StarCount-System-A")
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_a,))
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, star_type, luminosity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_a, 1, "Star A 1", "N", "VII")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, star_type, luminosity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_a, 2, "Star A 2", "M", "V")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, star_type, luminosity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_a, 3, "Star A 3", "M", "V")
        )

        # System B: 2 Neutron Stars (N), 1 M-class star (Lum V)
        conn.execute(
            "INSERT OR REPLACE INTO systems (system_address, star_system) VALUES (?, ?)",
            (sys_b, "StarCount-System-B")
        )
        conn.execute("DELETE FROM bodies WHERE system_address = ?", (sys_b,))
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, star_type, luminosity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_b, 1, "Star B 1", "N", "VII")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, star_type, luminosity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_b, 2, "Star B 2", "N", "VII")
        )
        conn.execute(
            """
            INSERT INTO bodies (system_address, body_id, body_name, star_type, luminosity)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sys_b, 3, "Star B 3", "M", "V")
        )
        conn.commit()

    # Query 1: star_types=N -> both A and B
    res = client.get("/api/systems?q=StarCount-System&star_types=N")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "StarCount-System-A" in names
    assert "StarCount-System-B" in names

    # Query 2: star_types=N:2 -> only B
    res = client.get("/api/systems?q=StarCount-System&star_types=N:2")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["StarCount-System-B"]

    # Query 3: star_types=M:2 -> only A
    res = client.get("/api/systems?q=StarCount-System&star_types=M:2")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["StarCount-System-A"]

    # Query 4: luminosity_classes=V:2 -> only A (A has 2 stars with luminosity V)
    res = client.get("/api/systems?q=StarCount-System&luminosity_classes=V:2")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["StarCount-System-A"]

    # Query 5: star_types=N:2,M:1 (AND) -> only B
    res = client.get("/api/systems?q=StarCount-System&star_types=N:2,M:1&star_match_mode=all")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert names == ["StarCount-System-B"]

    # Query 6: star_types=N:2,M:2 (OR) -> both A and B
    res = client.get("/api/systems?q=StarCount-System&star_types=N:2,M:2&star_match_mode=any")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "StarCount-System-A" in names
    assert "StarCount-System-B" in names

    # Cleanup
    with get_db_connection() as conn:
        conn.execute("DELETE FROM bodies WHERE system_address IN (?, ?)", (sys_a, sys_b))
        conn.execute("DELETE FROM systems WHERE system_address IN (?, ?)", (sys_a, sys_b))
        conn.commit()
