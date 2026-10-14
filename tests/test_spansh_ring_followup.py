import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.db.database as database
from app.addons import addon_manager
from app.server.api import app
from app.services import spansh_followup
from app.services.edsm_service import edsm_service
from app.services.ring_format import normalize_rings, to_journal_ring
from app.services.spansh_service import spansh_service

SYS_ADDR = 424200
EDSM_RING = {"name": "Foo A Belt", "type": "Metal Rich", "mass": 1179800000, "innerRadius": 744720, "outerRadius": 1709400}
SPANSH_BODIES = [{
    "name": "Foo A", "body_id": 1,
    "rings": [{"name": "Foo A Belt", "type": "Metal Rich", "signals": [{"name": "Platinum", "count": 3}, {"name": "Painite", "count": 1}]}],
}]


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "f.db")
    database.init_db(force=True)
    conn = database.get_db_connection()
    conn.execute("INSERT INTO systems (system_address, star_system, visit_count, is_external) VALUES (?, 'Foo', 0, 1)", (SYS_ADDR,))
    conn.commit()
    conn.close()


def _add_body(rings):
    conn = database.get_db_connection()
    conn.execute(
        "INSERT INTO bodies (system_address, body_id, body_name, star_type, rings) VALUES (?, 1, 'Foo A', 'G', ?)",
        (SYS_ADDR, rings),
    )
    conn.commit()
    conn.close()


def _stored_rings():
    conn = database.get_db_connection()
    raw = conn.execute("SELECT rings FROM bodies WHERE system_address = ? AND body_id = 1", (SYS_ADDR,)).fetchone()[0]
    conn.close()
    return json.loads(raw)


def test_to_journal_ring_converts_edsm_shape():
    r = to_journal_ring(EDSM_RING)
    assert r == {
        "Name": "Foo A Belt", "RingClass": "eRingClass_MetalRich", "MassMT": 1179800000,
        "InnerRad": 744720000.0, "OuterRad": 1709400000.0,
    }


def test_journal_shaped_rings_are_unchanged():
    journal = {"Name": "X Ring", "RingClass": "eRingClass_Icy", "MassMT": 1.0, "InnerRad": 5.0, "OuterRad": 6.0}
    assert to_journal_ring(journal) is journal
    assert normalize_rings(None) is None and normalize_rings([]) == []


def test_spansh_hotspots_merge_into_edsm_format_rings(db, monkeypatch):
    _add_body(json.dumps([EDSM_RING]))
    monkeypatch.setattr(spansh_service, "fetch_system_bodies", lambda name: SPANSH_BODIES)
    conn = database.get_db_connection()
    summary = spansh_service.sync_system_spansh(conn, SYS_ADDR, "Foo")
    conn.close()
    assert summary["hotspots_found"] == 4
    ring = _stored_rings()[0]
    assert ring["Name"] == "Foo A Belt" and ring["RingClass"] == "eRingClass_MetalRich"
    assert ring["Hotspots"] == {"Platinum": 3, "Painite": 1}


def test_followup_requests_spansh_only_when_rings_exist(db, monkeypatch):
    calls = []
    monkeypatch.setattr(spansh_service, "sync_system_spansh", lambda conn, a, n: calls.append((a, n)) or {"success": True, "hotspots_found": 2})

    _add_body(None)
    assert spansh_followup.fetch_ring_hotspots_if_rings(SYS_ADDR, "Foo") is None
    assert calls == []

    conn = database.get_db_connection()
    conn.execute("UPDATE bodies SET rings = '[]' WHERE system_address = ?", (SYS_ADDR,))
    conn.commit()
    conn.close()
    assert spansh_followup.fetch_ring_hotspots_if_rings(SYS_ADDR, "Foo") is None
    assert calls == []

    conn = database.get_db_connection()
    conn.execute("UPDATE bodies SET rings = ? WHERE system_address = ?", (json.dumps([EDSM_RING]), SYS_ADDR))
    conn.commit()
    conn.close()
    assert spansh_followup.fetch_ring_hotspots_if_rings(SYS_ADDR, "Foo") == {"success": True, "hotspots_found": 2}
    assert calls == [(SYS_ADDR, "Foo")]


def test_followup_skipped_when_spansh_addon_disabled(db, monkeypatch):
    _add_body(json.dumps([EDSM_RING]))
    calls = []
    monkeypatch.setattr(spansh_service, "sync_system_spansh", lambda *a: calls.append(a) or {})
    monkeypatch.setattr(addon_manager, "is_enabled", lambda addon_id: False)
    assert spansh_followup.fetch_ring_hotspots_if_rings(SYS_ADDR, "Foo") is None
    assert calls == []


def test_followup_failure_is_reported_not_raised(db, monkeypatch):
    _add_body(json.dumps([EDSM_RING]))

    def boom(*a):
        raise RuntimeError("spansh down")

    monkeypatch.setattr(spansh_service, "sync_system_spansh", boom)
    res = spansh_followup.fetch_ring_hotspots_if_rings(SYS_ADDR, "Foo")
    assert res["success"] is False and "spansh down" in res["error"]


def test_edsm_import_endpoint_adds_spansh_summary(db, monkeypatch):
    _add_body(json.dumps([EDSM_RING]))
    monkeypatch.setattr(
        edsm_service, "import_unvisited_system_by_name",
        lambda name: {"success": True, "system_address": SYS_ADDR, "star_system": "Foo"},
    )
    monkeypatch.setattr(spansh_service, "fetch_system_bodies", lambda name: SPANSH_BODIES)
    res = TestClient(app).post("/api/external/import_edsm?system_name=Foo")
    assert res.status_code == 200
    assert res.json()["spansh"]["hotspots_found"] == 4
    assert _stored_rings()[0]["Hotspots"] == {"Platinum": 3, "Painite": 1}


def test_ui_shows_hotspot_count_after_load():
    app_js = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "app.js").read_text(encoding="utf-8")
    assert "resData.spansh" in app_js and "hotspots_found" in app_js


def test_edsm_body_import_stores_rings_in_journal_form(db):
    from app.services.edsm.body_importer import import_and_complete_bodies

    edsm_body = {
        "name": "Foo A", "bodyId": 1, "type": "Planet", "subType": "Gas giant with water based life",
        "distanceToArrival": 100.0, "rings": [EDSM_RING],
    }
    conn = database.get_db_connection()
    assert import_and_complete_bodies(conn, SYS_ADDR, "Foo", [edsm_body]) == 1
    conn.commit()
    conn.close()
    assert _stored_rings() == [to_journal_ring(EDSM_RING)]
