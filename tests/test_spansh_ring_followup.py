import json
from pathlib import Path

import pytest

import app.db.database as database
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


# ---- external data is fetched only when the user asks for it ---------------------------------------

def _auto_lookup(monkeypatch, tmp_path, setting):
    import json

    import app.config as config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    if setting is not None:
        (tmp_path / "app_settings.json").write_text(json.dumps({"edsm_auto_lookup": setting}), encoding="utf-8")


@pytest.mark.parametrize("setting,expected", [
    (None, True),    # no choice made: on, as before, so catalog systems such as Sol get their bodies
    (True, True),
    (False, False),  # the user switched it off in Settings
])
def test_edsm_background_lookup_follows_the_users_setting(tmp_path, monkeypatch, setting, expected):
    from app.services.edsm_service import EDSMService, edsm_service

    _auto_lookup(monkeypatch, tmp_path, setting)
    queued = []
    monkeypatch.setattr(edsm_service.client, "queue_system_check", lambda *a, **k: queued.append(a))
    assert EDSMService.auto_lookup_enabled() is expected
    edsm_service.queue_system_check(1, "Sol", priority=True)
    assert bool(queued) is expected


def test_opening_an_unscanned_catalog_system_queues_the_edsm_fill_in(tmp_path, monkeypatch):
    """Regression: Sol / Omicron Capricorni B have no scan records in the journal; their bodies come from EDSM."""
    from fastapi.testclient import TestClient

    import app.db.database as database
    from app.server.api import app
    from app.services.edsm_service import edsm_service

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "catalog.db")
    database.init_db(force=True)
    conn = database.get_db_connection()
    conn.execute("INSERT INTO systems (system_address, star_system, visit_count, edsm_checked, edsm_registered) "
                 "VALUES (220354045116, 'Omicron Capricorni B', 2, 0, 0)")
    conn.commit()
    conn.close()
    _auto_lookup(monkeypatch, tmp_path / "settings", None)  # no settings file at all = defaults
    queued = []
    monkeypatch.setattr(edsm_service.client, "queue_system_check", lambda *a, **k: queued.append((a, k)))

    assert TestClient(app).get("/api/system/220354045116").status_code == 200
    assert queued and queued[0][0][:2] == (220354045116, "Omicron Capricorni B")
    assert queued[0][1].get("priority") is True


def test_manual_edsm_actions_do_not_depend_on_auto_lookup(tmp_path, monkeypatch):
    from app.services.edsm_service import edsm_service

    _auto_lookup(monkeypatch, tmp_path, False)
    called = []
    monkeypatch.setattr("app.services.edsm_service._import_unvisited_system_by_name",
                        lambda *a, **k: called.append("import") or {"success": True})
    monkeypatch.setattr(edsm_service, "_fetch_and_update_system", lambda *a, **k: called.append("sync") or {})
    monkeypatch.setattr(edsm_service.client, "throttle_delay", lambda: None)
    edsm_service.import_unvisited_system_by_name("Sol")
    edsm_service.fetch_and_update_system_sync(1, "Sol")
    assert called == ["import", "sync"]


def test_no_spansh_request_is_made_automatically_after_edsm():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    for relative in ("app/server/api.py", "addons/edsm_sync/addon.py"):
        assert "fetch_ring_hotspots" not in (root / relative).read_text(encoding="utf-8"), relative
    assert not (root / "app" / "services" / "spansh_followup.py").exists()



def test_settings_endpoint_reports_the_auto_lookup_choice(monkeypatch):
    from fastapi.testclient import TestClient

    import app.server.api as api

    monkeypatch.setattr(api, "load_app_settings_data", lambda: {"edsm_auto_lookup": False})
    assert TestClient(api.app).get("/api/app_settings").json()["edsm_auto_lookup"] is False
    monkeypatch.setattr(api, "load_app_settings_data", lambda: {})
    assert TestClient(api.app).get("/api/app_settings").json()["edsm_auto_lookup"] is True


def test_ui_offers_hotspots_and_the_auto_lookup_switch():
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent / "app" / "ui"
    app_js = (base / "js" / "app.js").read_text(encoding="utf-8")
    modals = (base / "components" / "modals.html").read_text(encoding="utf-8")
    i18n_js = (base / "js" / "i18n.js").read_text(encoding="utf-8")
    assert "offerSpanshHotspots(" in app_js and "btn-spansh-hotspots-after-load" in app_js
    assert 'data-requires-addon", "spansh_sync"' in app_js.replace("'", '"')
    row = next(line for line in modals.splitlines() if 'id="edsm-auto-lookup-row"' in line)
    assert 'id="cb-edsm-auto-lookup"' in modals
    assert "data-requires-addon" not in row, "the switch must stay reachable when the EDSM addon is off"
    for key in ("spansh_hotspots_offer", "spansh_hotspots_done", "edsm_auto_lookup_title", "edsm_auto_lookup_desc"):
        assert i18n_js.count(f"{key}:") == 2  # ja + en
