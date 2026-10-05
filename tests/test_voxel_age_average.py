import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db_connection, init_db
from app.server.api import app
from app.utils.voxel import voxel_age_stats, voxel_key


@pytest.mark.parametrize("name,expected", [
    ("Noijo AA-Z e5", "Noijo AA-Z e"),
    ("Noijo AA-Z e0", "Noijo AA-Z e"),
    ("Noijo JR-W f1-57", "Noijo JR-W f"),
    ("Col 285 Sector LK-P a3-1", "Col 285 Sector LK-P a"),
    ("Brairee AA-A h0", "Brairee AA-A h"),
    ("Sol", None),
    ("Beagle Point", None),
    ("Noijo AA-Z", None),
    ("Noijo AA-Z z5", None),
    ("", None),
    (None, None),
])
def test_voxel_key(name, expected):
    assert voxel_key(name) == expected


def test_same_voxel_code_with_different_mass_code_is_a_different_key():
    assert voxel_key("Brairee AA-A g3") != voxel_key("Brairee AA-A h3")


def test_voxel_age_stats(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "v.db"))
    init_db(conn)
    rows = [
        (1, "Noijo AA-Z e0", 100.0),
        (2, "Noijo AA-Z e7", 300.0),
        (3, "Noijo AA-Z f1-9", 5000.0),   # same voxel code, different mass code
        (4, "Noijo CA-Z e1", 900.0),
        (5, "Noijo AA-Z e9", None),       # unknown age: not counted
        (6, "Sol", 4600.0),
    ]
    for addr, name, age in rows:
        conn.execute("INSERT INTO systems (system_address, star_system, system_age_my) VALUES (?, ?, ?)", (addr, name, age))
    conn.commit()

    stats = voxel_age_stats(conn, ["Noijo AA-Z e", "Noijo CA-Z e", "Noijo AA-Z f"])
    assert stats["Noijo AA-Z e"] == (200.0, 2)
    assert stats["Noijo CA-Z e"] == (900.0, 1)
    assert stats["Noijo AA-Z f"] == (5000.0, 1)
    assert voxel_age_stats(conn, []) == {}
    conn.close()


def test_api_returns_voxel_average():
    init_db()
    client = TestClient(app)
    fixtures = {
        999555000001: ("VoxelTest AA-Z e1", 100.0),
        999555000002: ("VoxelTest AA-Z e2", 300.0),
        999555000003: ("VoxelTest BA-Z e1", 7000.0),
    }
    with get_db_connection() as conn:
        for addr, (name, age) in fixtures.items():
            conn.execute(
                "INSERT OR REPLACE INTO systems (system_address, star_system, system_age_my) VALUES (?, ?, ?)",
                (addr, name, age),
            )
        conn.commit()
    try:
        res = client.get("/api/systems?q=VoxelTest")
        assert res.status_code == 200
        by_name = {s["star_system"]: s for s in res.json()["systems"]}
        a = by_name["VoxelTest AA-Z e1"]
        assert a["voxel_key"] == "VoxelTest AA-Z e"
        assert a["voxel_age_avg_my"] == 200.0
        assert a["voxel_age_count"] == 2
        assert by_name["VoxelTest AA-Z e2"]["voxel_age_avg_my"] == 200.0
        b = by_name["VoxelTest BA-Z e1"]
        assert b["voxel_age_avg_my"] == 7000.0 and b["voxel_age_count"] == 1
    finally:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM systems WHERE system_address IN (?, ?, ?)", tuple(fixtures))
            conn.commit()


def test_voxel_ui_wiring():
    base = Path(__file__).resolve().parent.parent / "app" / "ui"
    sys_list = (base / "js" / "system_list.js").read_text(encoding="utf-8")
    i18n_js = (base / "js" / "i18n.js").read_text(encoding="utf-8")
    css = (base / "css" / "style.css").read_text(encoding="utf-8")
    assert "voxel_age_avg_my" in sys_list and "system-card-voxel-age" in sys_list
    assert ".system-card-voxel-age" in css
    for key in ("voxel_age_avg", "voxel_age_avg_tip"):
        assert i18n_js.count(f"{key}:") == 2  # ja + en
