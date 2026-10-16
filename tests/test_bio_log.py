from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.db.database as database
from app.server.api import app
from app.services.bio_log import GEOLOGY_GENUS, collect_bio_entries, query_bio_log

SYS_A, SYS_B = 8101, 8102


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "bio.db")
    database.init_db(force=True)
    c = database.get_db_connection()
    c.execute("INSERT INTO systems (system_address, star_system) VALUES (?, 'Alpha System')", (SYS_A,))
    c.execute("INSERT INTO systems (system_address, star_system) VALUES (?, 'Beta System')", (SYS_B,))

    def organic(sys_addr, body_id, body, ts, stage, genus_loc, species_loc, variant_loc="", base=1000000, fd=5000000):
        c.execute(
            "INSERT INTO scanned_organics (system_address, body_id, body_name, timestamp, scan_type, genus, "
            "genus_localised, species, species_localised, variant, variant_localised, base_value, first_discovery_value) "
            "VALUES (?, ?, ?, ?, ?, '', ?, '', ?, '', ?, ?, ?)",
            (sys_addr, body_id, body, ts, stage, genus_loc, species_loc, variant_loc, base, fd),
        )

    # Stratum Paleas on Alpha 1: all three stages, logged on two row shapes (variant row + species row)
    organic(SYS_A, 1, "Alpha 1", "2026-01-01T10:00:00Z", "Log", "Stratum", "Stratum Paleas - Lime", "Stratum Paleas - Lime", 1638900, 8194500)
    organic(SYS_A, 1, "Alpha 1", "2026-01-01T10:05:00Z", "Sample", "Stratum", "Stratum Paleas")
    organic(SYS_A, 1, "Alpha 1", "2026-01-01T10:10:00Z", "Analyse", "Stratum", "Stratum Paleas", base=1638900)
    # Bacterium Aurasus on Beta 2: only the first sample so far
    organic(SYS_B, 2, "Beta 2", "2026-02-01T09:00:00Z", "Log", "Bacterium", "Bacterium Aurasus - Teal", "Bacterium Aurasus - Teal", 1000000, 5000000)
    # Same species on a second body of Alpha: a separate entry
    organic(SYS_A, 3, "Alpha 3", "2026-03-01T09:00:00Z", "Analyse", "Stratum", "Stratum Paleas - Lime", "Stratum Paleas - Lime", 1638900, 8194500)
    # Codex-only rows with no genus: a colour-prefixed organism and a geological site
    organic(SYS_B, 4, "Beta 4", "2026-04-01T09:00:00Z", "Log", "Unknown", "Roseum Bioluminescent Anemone")
    organic(SYS_B, 5, "Beta 5", "2026-04-02T09:00:00Z", "Log", "Unknown", "Sulphur Dioxide Fumarole")
    c.execute(
        "INSERT INTO codex_entries (system_address, body_id, entry_id, name, name_localised, category, sub_category, timestamp, created_at) "
        "VALUES (?, 5, 1, 'x', 'Sulphur Dioxide Fumarole', '$Codex_Category_Biology;', '$Codex_SubCategory_Geology_and_Anomalies;', 't', 't')",
        (SYS_B,),
    )
    c.commit()
    yield c
    c.close()


def _by(entries, species, body):
    return next(e for e in entries if e["species"] == species and e["body_name"] == body)


def test_entries_are_one_per_system_body_species(conn):
    entries = collect_bio_entries(conn)
    assert len(entries) == 5
    a1 = _by(entries, "Stratum Paleas", "Alpha 1")
    assert a1["star_system"] == "Alpha System"
    assert a1["genus"] == "Stratum" and a1["variant"] == "Lime"
    assert a1["stage_name"] == "Analyse" and a1["is_completed"] is True
    assert a1["first_found_at"] == "2026-01-01T10:00:00Z" and a1["last_at"] == "2026-01-01T10:10:00Z"
    assert a1["base_value"] == 1638900 and a1["first_discovery_value"] == 8194500
    assert _by(entries, "Stratum Paleas", "Alpha 3")["is_completed"] is True


def test_in_progress_stage(conn):
    b2 = _by(collect_bio_entries(conn), "Bacterium Aurasus", "Beta 2")
    assert b2["stage"] == 1 and b2["stage_name"] == "Log" and b2["is_completed"] is False
    assert b2["variant"] == "Teal"


def test_genus_fallbacks_for_codex_only_rows(conn):
    entries = collect_bio_entries(conn)
    assert _by(entries, "Roseum Bioluminescent Anemone", "Beta 4")["genus"] == "Bioluminescent Anemone"
    assert _by(entries, "Sulphur Dioxide Fumarole", "Beta 5")["genus"] == GEOLOGY_GENUS


def test_query_filters_and_counts(conn):
    entries = collect_bio_entries(conn)
    assert query_bio_log(entries)["summary"] == {"entries": 5, "species": 4, "systems": 2}

    assert query_bio_log(entries, status="completed")["total"] == 2
    assert query_bio_log(entries, status="in_progress")["total"] == 3

    by_genus = query_bio_log(entries, genus=["stratum"])
    assert by_genus["total"] == 2
    # Genus chip counts ignore the genus filter itself so the chips stay usable
    assert {g["genus"]: g["count"] for g in by_genus["genus_counts"]}["Bacterium"] == 1

    assert query_bio_log(entries, q="beta")["total"] == 3
    assert query_bio_log(entries, q="alpha 3")["items"][0]["body_name"] == "Alpha 3"
    assert query_bio_log(entries, q="lime")["total"] == 2
    assert query_bio_log(entries, q="nothing-matches")["items"] == []


def test_query_sort_and_paging(conn):
    entries = collect_bio_entries(conn)
    newest = query_bio_log(entries, sort="found_desc")["items"]
    assert [e["first_found_at"] for e in newest] == sorted((e["first_found_at"] for e in newest), reverse=True)
    oldest = query_bio_log(entries, sort="found_asc")["items"]
    assert oldest[0]["first_found_at"] == "2026-01-01T10:00:00Z"
    assert query_bio_log(entries, sort="value_desc")["items"][0]["base_value"] == 1638900
    page2 = query_bio_log(entries, limit=2, page=2)
    assert page2["total"] == 5 and len(page2["items"]) == 2 and page2["page"] == 2


def test_api_endpoint(conn):
    client = TestClient(app)
    res = client.get("/api/bio_log?genus=Stratum,Bacterium&status=completed")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert {i["star_system"] for i in body["items"]} == {"Alpha System"}
    assert client.get("/api/bio_log?q=beta&sort=species").json()["total"] == 3


def test_bio_log_ui_wiring():
    base = Path(__file__).resolve().parent.parent / "app" / "ui"
    html = (base / "components" / "center_pane.html").read_text(encoding="utf-8")
    index = (base / "index.html").read_text(encoding="utf-8")
    app_js = (base / "js" / "app.js").read_text(encoding="utf-8")
    i18n_js = (base / "js" / "i18n.js").read_text(encoding="utf-8")
    assert 'id="btn-view-biolog"' in html
    assert "/static/js/bio_log.js" in index
    assert "renderBioLogView" in app_js and "switchCenterPaneView('biolog')" in app_js
    # The new view follows the Exobiology module toggle like the existing Bio view
    assert "btnViewBioLog.style.display = modSettings.exobiology" in app_js
    for key in ("view_biolog", "biolog_col_species", "biolog_status_completed", "biolog_summary", "biolog_geology"):
        assert i18n_js.count(f"{key}:") == 2  # ja + en
