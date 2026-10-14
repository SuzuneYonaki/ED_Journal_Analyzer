from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.db.database as database
from app.server.api import app

EXT_A, EXT_B, VISITED, FLAGGED_VISITED = 7001, 7002, 7003, 7004


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Isolated database: the delete-all endpoint must never run against real data.
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ext.db")
    database.init_db(force=True)
    conn = database.get_db_connection()
    rows = [
        (EXT_A, "Ext Alpha", 0, 1),
        (EXT_B, "Ext Beta", 0, 1),
        (VISITED, "My Visited", 3, 0),
        (FLAGGED_VISITED, "Flagged But Visited", 2, 1),
    ]
    for addr, name, visits, ext in rows:
        conn.execute(
            "INSERT INTO systems (system_address, star_system, visit_count, is_external) VALUES (?, ?, ?, ?)",
            (addr, name, visits, ext),
        )
        conn.execute(
            "INSERT INTO bodies (system_address, body_id, body_name, star_type) VALUES (?, 0, ?, 'G')",
            (addr, f"{name} A"),
        )
    conn.execute(
        "INSERT INTO body_bookmarks (system_address, body_id, body_name, star_system, created_at, updated_at) "
        "VALUES (?, 0, 'Ext Alpha A', 'Ext Alpha', 't', 't')",
        (EXT_A,),
    )
    conn.execute(
        "INSERT INTO body_bookmarks (system_address, body_id, body_name, star_system, created_at, updated_at) "
        "VALUES (?, 0, 'My Visited A', 'My Visited', 't', 't')",
        (VISITED,),
    )
    conn.commit()
    conn.close()
    return TestClient(app)


def _count(sql, *args):
    conn = database.get_db_connection()
    n = conn.execute(sql, args).fetchone()[0]
    conn.close()
    return n


def test_summary_counts_only_unvisited_external(client):
    res = client.get("/api/external/summary")
    assert res.status_code == 200
    assert res.json() == {"systems": 2, "bodies": 2, "bookmarks": 1}


def test_delete_single_external_system(client):
    res = client.delete(f"/api/external/systems/{EXT_A}")
    assert res.status_code == 200
    assert res.json()["systems"] == 1 and res.json()["bodies"] == 1 and res.json()["bookmarks"] == 1
    assert _count("SELECT COUNT(*) FROM systems WHERE system_address = ?", EXT_A) == 0
    assert _count("SELECT COUNT(*) FROM bodies WHERE system_address = ?", EXT_A) == 0
    assert _count("SELECT COUNT(*) FROM body_bookmarks WHERE system_address = ?", EXT_A) == 0
    # Everything else is untouched
    assert _count("SELECT COUNT(*) FROM systems") == 3
    assert _count("SELECT COUNT(*) FROM systems WHERE system_address = ?", EXT_B) == 1


@pytest.mark.parametrize("addr", [VISITED, FLAGGED_VISITED])
def test_visited_systems_are_protected(client, addr):
    res = client.delete(f"/api/external/systems/{addr}")
    assert res.status_code == 400
    assert _count("SELECT COUNT(*) FROM systems WHERE system_address = ?", addr) == 1
    assert _count("SELECT COUNT(*) FROM bodies WHERE system_address = ?", addr) == 1


def test_delete_unknown_system_is_404(client):
    assert client.delete("/api/external/systems/424242").status_code == 404


def test_delete_all_external_keeps_own_data(client):
    res = client.delete("/api/external/systems")
    assert res.status_code == 200
    assert res.json() == {"success": True, "systems": 2, "bodies": 2, "bookmarks": 1}
    remaining = {r for r in _rows("SELECT system_address FROM systems")}
    assert remaining == {VISITED, FLAGGED_VISITED}
    assert _count("SELECT COUNT(*) FROM bodies") == 2
    assert _count("SELECT COUNT(*) FROM body_bookmarks") == 1
    # Idempotent
    assert client.delete("/api/external/systems").json()["systems"] == 0
    assert client.get("/api/external/summary").json()["systems"] == 0


def _rows(sql):
    conn = database.get_db_connection()
    out = [r[0] for r in conn.execute(sql).fetchall()]
    conn.close()
    return out


def test_external_delete_ui_wiring():
    base = Path(__file__).resolve().parent.parent / "app" / "ui"
    html = (base / "components" / "left_pane.html").read_text(encoding="utf-8")
    app_js = (base / "js" / "app.js").read_text(encoding="utf-8")
    i18n_js = (base / "js" / "i18n.js").read_text(encoding="utf-8")
    assert 'id="external-footprint-actions"' in html
    assert "btn-delete-external-this" in app_js and "btn-delete-external-all" in app_js
    assert "/api/external/summary" in app_js and "/api/external/systems" in app_js
    for key in ("footprint_delete_this", "footprint_delete_all", "footprint_delete_this_confirm", "footprint_delete_all_confirm"):
        assert i18n_js.count(f"{key}:") == 2  # ja + en
