import sqlite3
import pytest
from fastapi.testclient import TestClient

from app.db.database import get_celestial_statistics, init_db
from app.server.api import app


@pytest.fixture
def test_db(monkeypatch, tmp_path):
    """Creates a temporary SQLite database with bodies table for testing statistics."""
    db_file = tmp_path / "test_stats.db"
    
    # Override DB_PATH
    import app.db.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", str(db_file))
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_CACHE", None)
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_TIMESTAMP", 0)
    monkeypatch.setattr(db_mod, "_DB_INITIALIZED", False)

    # Initialize tables
    init_db(force=True)

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Insert test bodies
    test_bodies = [
        # Sudarsky classes
        (1, "Body 1", 1, "Sudarsky class I gas giant", None, None),
        (2, "Body 2", 1, "Sudarsky class II gas giant", None, None),
        (3, "Body 3", 1, "Sudarsky class III gas giant", None, None),
        (4, "Body 4", 1, "Sudarsky class IV gas giant", None, None),
        (5, "Body 5", 1, "Sudarsky class V gas giant", None, None),
        # Life-bearing gas giants (ringed vs unringed)
        (6, "Body 6", 1, "Gas giant with water based life", None, None),
        (7, "Body 7", 1, "Gas giant with water based life", '[{"name": "Ring A"}]', None),
        (8, "Body 8", 1, "Gas giant with ammonia based life", None, None),
        (9, "Body 9", 1, "Gas giant with ammonia based life", '[{"name": "Ring B"}]', None),
        # Helium variants
        (10, "Body 10", 1, "Helium rich gas giant", None, None),
        (11, "Body 11", 1, "Helium gas giant", None, None),
        # Water giant
        (12, "Body 12", 1, "Water giant", None, None),
        # Confirmed GGG
        (13, "Body 13", 1, "Sudarsky class III gas giant", None, '["Confirmed GGG (Class III Gas Giant)"]'),
        # Non-gas giant terrestrials
        (14, "Body 14", 1, "Earthlike body", None, None),
        (15, "Body 15", 1, "Water world", None, None),
        (16, "Body 16", 1, "Ammonia world", None, None),
    ]

    for b in test_bodies:
        c.execute("""
            INSERT INTO bodies (
                body_id, body_name, system_address, planet_class, rings, anomalies_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, b)

    # Insert a dummy system
    c.execute("""
        INSERT INTO systems (
            system_address, star_system, scanned_bodies, total_potential_value
        ) VALUES (1, "Test System", 16, 50000000)
    """)

    conn.commit()
    conn.close()

    return str(db_file)


def test_get_celestial_statistics_breakdown(test_db, monkeypatch):
    """Validates that get_celestial_statistics accurately aggregates all gas giant variants."""
    import app.db.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", test_db)
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_CACHE", None)
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_TIMESTAMP", 0)

    stats = get_celestial_statistics(bypass_cache=True)
    planets = stats["planets"]

    assert planets["sudarsky_class_1"] == 1
    assert planets["sudarsky_class_2"] == 1
    assert planets["sudarsky_class_3"] == 2  # Body 3 + Body 13
    assert planets["sudarsky_class_4"] == 1
    assert planets["sudarsky_class_5"] == 1

    assert planets["gas_giant_water_life"] == 2
    assert planets["gas_giant_water_life_unringed"] == 1
    assert planets["gas_giant_water_life_ringed"] == 1

    assert planets["gas_giant_ammonia_life"] == 2
    assert planets["gas_giant_ammonia_life_unringed"] == 1
    assert planets["gas_giant_ammonia_life_ringed"] == 1

    assert planets["helium_rich_gas_giant"] == 1
    assert planets["helium_gas_giant"] == 1
    assert planets["water_giant"] == 1
    assert planets["green_gas_giant"] == 1

    # Total gas giants = 1+1+2+1+1 + 2 + 2 + 1 + 1 + 1 = 13
    assert planets["gas_giants_total"] == 13


def test_api_stats_celestial_counts(test_db, monkeypatch):
    """Validates /api/stats includes complete celestial_counts with gas giant breakdown."""
    import app.db.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", test_db)
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_CACHE", None)
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_TIMESTAMP", 0)

    client = TestClient(app)
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert "celestial_counts" in data
    cc = data["celestial_counts"]
    assert cc["gas_giants_total"] == 13
    assert cc["sudarsky_class_1"] == 1
    assert cc["sudarsky_class_2"] == 1
    assert cc["sudarsky_class_3"] == 2
    assert cc["sudarsky_class_4"] == 1
    assert cc["sudarsky_class_5"] == 1
    assert cc["gas_giant_water_life_ringed"] == 1
    assert cc["gas_giant_ammonia_life_ringed"] == 1
    assert cc["helium_rich_gas_giant"] == 1
    assert cc["helium_gas_giant"] == 1
    assert cc["water_giant"] == 1
    assert cc["green_gas_giant"] == 1


def test_api_stats_celestial_counts_endpoint(test_db, monkeypatch):
    """Validates /api/stats/celestial_counts endpoint structure."""
    import app.db.database as db_mod
    monkeypatch.setattr(db_mod, "DB_PATH", test_db)
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_CACHE", None)
    monkeypatch.setattr(db_mod, "_CELESTIAL_STATS_TIMESTAMP", 0)

    client = TestClient(app)
    resp = client.get("/api/stats/celestial_counts")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "success"
    planets = res_data["data"]["planets"]
    assert planets["gas_giants_total"] == 13
    assert planets["green_gas_giant"] == 1


def test_ggg_badge_classification_logic():
    """
    Validates the badge classification logic mirrored from system_map.js.
    Ensures confirmed GGG receives [GGG] and candidate receives [GGG？].
    """
    def get_ggg_badge(body: dict) -> tuple[str, str, str] | None:
        anomalies = body.get("anomalies") or []
        confirmed_anom = next((a for a in anomalies if "Confirmed GGG" in a), None)
        is_confirmed = bool(confirmed_anom or body.get("is_confirmed_ggg"))
        is_cand = bool(body.get("is_ggg") and not is_confirmed)

        if is_confirmed:
            variant_str = confirmed_anom.replace("Confirmed GGG", "").strip(" ()") if confirmed_anom else "Gas Giant"
            return ("ggg-confirmed", "[GGG]", f"確定グリーンガスジャイアント: {variant_str}")
        elif is_cand:
            return ("ggg-candidate", "[GGG？]", "グリーンガスジャイアント候補 (FSSまたは目視確認推奨)")
        return None

    # Test Confirmed GGG from anomalies
    b_conf = {"anomalies": ["Confirmed GGG (Class III Gas Giant)"], "is_ggg": True}
    res = get_ggg_badge(b_conf)
    assert res is not None
    assert res[0] == "ggg-confirmed"
    assert res[1] == "[GGG]"
    assert "確定グリーンガスジャイアント: Class III Gas Giant" in res[2]

    # Test Confirmed GGG from is_confirmed_ggg flag
    b_conf_flag = {"is_confirmed_ggg": True}
    res_flag = get_ggg_badge(b_conf_flag)
    assert res_flag is not None
    assert res_flag[0] == "ggg-confirmed"
    assert res_flag[1] == "[GGG]"

    # Test Candidate GGG
    b_cand = {"is_ggg": True}
    res_cand = get_ggg_badge(b_cand)
    assert res_cand is not None
    assert res_cand[0] == "ggg-candidate"
    assert res_cand[1] == "[GGG？]"
    assert "グリーンガスジャイアント候補" in res_cand[2]

    # Test Non-GGG body
    b_normal = {"planet_class": "Sudarsky class I gas giant"}
    assert get_ggg_badge(b_normal) is None

