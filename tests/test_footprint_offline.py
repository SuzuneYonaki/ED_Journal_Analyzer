from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.db.database as database
from app.addons import addon_manager
from app.server.api import app
from app.services.footprint_service import FootprintService, footprint_service


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "fp.db")
    database.init_db(force=True)
    conn = database.get_db_connection()
    conn.execute("INSERT INTO systems (system_address, star_system, visit_count) VALUES (1, 'Known System', 3)")
    conn.commit()
    conn.close()
    svc = FootprintService()
    calls = []

    def found(name):
        calls.append(name)
        return {"found": True, "url": "", "details": None}

    for method in ("_check_edsm", "_check_spansh", "_check_inara"):
        monkeypatch.setattr(svc, method, found)
    svc.calls = calls
    return svc


def test_offline_check_never_contacts_external_services(service):
    result = service.check_system_footprint("Never Visited", allow_external=False)
    assert service.calls == []
    assert result["offline"] is True and result["has_footprint"] is False
    assert result["summary"] == "offline", "must not be reported as 'not registered'"


def test_offline_check_is_not_cached_so_going_online_works(service):
    service.check_system_footprint("Never Visited", allow_external=False)
    online = service.check_system_footprint("Never Visited", allow_external=True)
    assert len(service.calls) == 3 and online["has_footprint"] is True and "offline" not in online


def test_local_database_hit_still_works_offline(service):
    result = service.check_system_footprint("Known System", allow_external=False)
    assert result["in_local_db"] is True and service.calls == []


@pytest.mark.parametrize("edsm,spansh,expect_online", [
    (False, False, False),
    (True, False, True),
    (False, True, True),
    (True, True, True),
])
def test_endpoint_goes_online_only_when_a_network_addon_is_on(monkeypatch, edsm, spansh, expect_online):
    seen = {}
    monkeypatch.setattr(addon_manager, "is_enabled", lambda addon_id: {"edsm_sync": edsm, "spansh_sync": spansh}.get(addon_id, False))
    monkeypatch.setattr(
        footprint_service, "check_system_footprint",
        lambda name, allow_external=True: seen.update(name=name, allow=allow_external) or {"system_name": name},
    )
    assert TestClient(app).get("/api/external_footprint?system_name=Sol").status_code == 200
    assert seen == {"name": "Sol", "allow": expect_online}


def test_footprint_ui_is_off_by_default_and_hidden_while_offline():
    base = Path(__file__).resolve().parent.parent / "app" / "ui"
    app_js = (base / "js" / "app.js").read_text(encoding="utf-8")
    css = (base / "css" / "style.css").read_text(encoding="utf-8")
    html = (base / "components" / "left_pane.html").read_text(encoding="utf-8")
    # Off unless the user ticked it before
    assert "externalFootprintCheck: localStorage.getItem('ed_external_footprint_check') === 'true'" in app_js
    checkbox = next(line for line in html.splitlines() if 'id="cb-external-footprint"' in line)
    assert "checked" not in checkbox.replace("cb-external-footprint", "")
    # Hidden and inert when neither EDSM nor Spansh is connected
    assert "body.addon-off-edsm_sync.addon-off-spansh_sync #external-check-row" in css
    assert app_js.count("addon-off-spansh_sync") >= 2 and "data.offline" in app_js
