import pytest

from app.parser.bioscan.adapters import (
    build_body_context,
    build_system_context,
    normalize_atmosphere,
    normalize_planet_class,
    normalize_volcanism,
)
from app.parser.bioscan.genus import data as GENUS_DATA
from app.parser.bioscan.matcher import (
    _star_colors,
    BodyContext,
    StarInfo,
    SystemContext,
    match_body,
    match_genus,
    ruleset_passes,
    star_check,
)
from app.parser.bioscan.regions import region_map
from app.parser.bioscan.species import rules as SPECIES_RULES
from app.utils.galactic_regions import GALACTIC_REGIONS


def test_ported_data_is_consistent():
    assert set(SPECIES_RULES) == set(GENUS_DATA)
    assert sum(len(v) for v in SPECIES_RULES.values()) == 119
    assert all(rid in GALACTIC_REGIONS for ids in region_map.values() for rid in ids)
    # Species the old hand-written table spelled wrongly exist under their in-game names
    names = {d["name"] for sp in SPECIES_RULES.values() for d in sp.values()}
    assert {"Bacterium Informem", "Tussock Caputus", "Stratum Aranaemus", "Radicoida Unicus"} <= names
    assert not {"Bacterium Informis", "Tussock Caputis", "Radicoida Unica"} & names


@pytest.mark.parametrize("query,star_type,expected", [
    ("A", "A", True), ("A", "A_BlueWhiteSuperGiant", True), ("A", "AeBe", False),
    ("M", "M_RedGiant", True), ("K", "K_OrangeGiant", True), ("K", "M", False),
    ("D", "DAB", True), ("W", "WN", True), ("C", "CS", True),
    ("Ae", "AeBe", True), ("N", "N", True), ("H", "H", True), ("TTS", "TTS", True),
])
def test_star_check(query, star_type, expected):
    assert star_check(query, star_type) is expected


@pytest.mark.parametrize("raw,expected", [
    ("CarbonDioxide", "CarbonDioxide"),
    ("Thin Carbon dioxide", "CarbonDioxide"),
    ("Hot thin Carbon dioxide", "CarbonDioxide"),
    ("Thin Neon-rich", "NeonRich"),
    ("Carbon dioxide-rich", "CarbonDioxideRich"),
    ("Sulphur dioxide", "SulphurDioxide"),
    ("No atmosphere", "None"), ("None", "None"), ("", "None"), (None, "None"),
])
def test_normalize_atmosphere(raw, expected):
    assert normalize_atmosphere(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("High metal content world", "High metal content body"),
    ("Metal-rich body", "Metal rich body"),
    ("Rocky Ice world", "Rocky ice body"),
    ("Earth-like world", "Earthlike body"),
    ("Gas giant with water-based life", "Gas giant with water based life"),
    ("Icy body", "Icy body"),
])
def test_normalize_planet_class(raw, expected):
    assert normalize_planet_class(raw) == expected


def test_normalize_volcanism():
    assert normalize_volcanism("No volcanism") == "" and normalize_volcanism(None) == ""
    assert normalize_volcanism("Minor Water Geysers Volcanism") == "minor water geysers volcanism"


def _system(**kwargs):
    kwargs.setdefault("name", "Test")
    return SystemContext(**kwargs)


def test_unknown_inputs_never_eliminate():
    body = BodyContext(name="b", body_type="Rocky body")
    assert ruleset_passes({"nebula": "all"}, body, _system())  # no coordinates
    assert ruleset_passes({"guardian": True}, body, _system())
    assert ruleset_passes({"tuber": "Any"}, body, _system())
    assert ruleset_passes({"parent_star": ["A"]}, body, _system())  # no star data at all
    assert ruleset_passes({"main_star": [("G", "V")]}, body, _system())
    assert ruleset_passes({"max_temperature": 100.0}, body, _system())  # temperature unknown


def test_known_inputs_do_eliminate():
    cold = BodyContext(name="b", body_type="Rocky body", temperature=300.0)
    assert not ruleset_passes({"max_temperature": 100.0}, cold, _system())
    assert not ruleset_passes({"body_type": ["Icy body"]}, cold, _system())
    assert not ruleset_passes({"system": "HIP 87621"}, cold, _system())
    assert ruleset_passes({"system": "Test"}, cold, _system())


def test_guardian_and_nebula_use_coordinates():
    body = BodyContext(name="b", body_type="Rocky body")
    near_guardian_site = _system(x=1099.2, y=-146.7, z=-133.6)   # Gamma Velorum
    far_away = _system(x=0.0, y=0.0, z=60000.0)
    assert ruleset_passes({"guardian": True}, body, near_guardian_site)
    assert not ruleset_passes({"guardian": True}, body, far_away)
    assert ruleset_passes({"nebula": "all"}, body, _system(name="Orion Sector AB-C d1", x=0.0, y=0.0, z=60000.0))
    assert not ruleset_passes({"nebula": "large"}, body, far_away)


def test_main_star_with_luminosity():
    body = BodyContext(name="b", body_type="Rocky body")
    system = _system(stars={"S": StarInfo("S", "G", "Vab", 0.0)}, main_star_name="S", main_star_type="G",
                     main_star_luminosity="Vab")
    assert ruleset_passes({"main_star": [("G", "V")]}, body, system)  # V + "ab"
    assert not ruleset_passes({"main_star": [("G", "IV")]}, body, system)
    assert not ruleset_passes({"main_star": ["K"]}, body, system)


def test_colours_follow_the_parent_star_and_the_arrival_star():
    aleoida = next(k for k, v in GENUS_DATA.items() if v["name"] == "Aleoida")
    table = GENUS_DATA[aleoida]["colors"]["star"]  # K -> Turquoise, F -> Teal
    stars = {
        "T A": StarInfo("T A", "K", "Va", 0.0, body_id=1),
        "T B": StarInfo("T B", "F", "V", 800.0, body_id=2),
    }
    system = _system(stars=stars, main_star_name="T A", main_star_type="K", main_star_luminosity="Va")
    orbiting_b = BodyContext(name="T B 1", body_type="Rocky body", parent_stars=["T B"])
    # parent star F gives Teal; the arrival star (distance 0, K) adds Turquoise
    assert _star_colors(table, orbiting_b, system) == {table["F"], table["K"]}
    orbiting_a = BodyContext(name="T A 1", body_type="Rocky body", parent_stars=["T A"])
    assert _star_colors(table, orbiting_a, system) == {table["K"]}


def test_element_coloured_species_survive_unknown_materials_but_not_wrong_ones():
    bacterium = next(k for k, v in GENUS_DATA.items() if v["name"] == "Bacterium")
    species = next(k for k, d in SPECIES_RULES[bacterium].items() if d["name"] == "Bacterium Informem")  # colour by element
    system = _system(stars={"S": StarInfo("S", "M", "V", 0.0)}, main_star_name="S", main_star_type="M",
                     main_star_luminosity="V")
    base = dict(name="b", body_type="Rocky body", atmosphere="Nitrogen", gravity=0.44 * 9.8, temperature=131.0,
                pressure=100.0, parent_stars=["S"])
    unknown = match_genus(bacterium, BodyContext(**base), system)
    with_element = match_genus(bacterium, BodyContext(**base, materials=frozenset({"antimony"})), system)
    wrong_elements = match_genus(bacterium, BodyContext(**base, materials=frozenset({"iron"})), system)
    assert species in unknown
    assert with_element.get(species) == ["Red"]
    assert species not in wrong_elements


def test_build_contexts_from_database_style_rows():
    rows = [
        {"body_id": 0, "body_name": "Sys A", "star_type": "G", "luminosity": "Va", "distance_from_arrival_ls": 0.0},
        {"body_id": 1, "body_name": "Sys A 1", "planet_class": "High metal content world"},
        {"body_id": 2, "body_name": "Sys A 2", "planet_class": "Earth-like world"},
    ]
    system = build_system_context(rows, system_name="Sys", star_pos=(1.0, 2.0, 3.0), region_id=18)
    assert system.main_star_name == "Sys A" and system.main_star_type == "G" and system.region_id == 18
    assert system.planet_types == ["High metal content body", "Earthlike body"]
    assert system.has_coordinates

    body = build_body_context({
        "body_name": "Sys A 1", "planet_class": "High metal content world", "atmosphere_type": "Thin Carbon dioxide",
        "surface_gravity": 4.9, "surface_gravity_g": 0.5, "surface_temperature": 200.0, "surface_pressure": 5000.0,
        "volcanism": "No volcanism", "parents": '[{"Star": 0}, {"Null": 0}]',
        "materials": '[{"Name": "iron", "Percent": 1.0}]',
        "atmosphere_composition": '[{"Name": "CarbonDioxide", "Percent": 95.0}]',
    }, system)
    assert body.body_type == "High metal content body" and body.atmosphere == "CarbonDioxide"
    assert body.gravity == 4.9 and body.volcanism == "" and body.pressure == 5000.0
    assert body.parent_stars == ["Sys A"] and body.materials == frozenset({"iron"})
    assert body.gases == {"CarbonDioxide": 95.0}


def test_match_body_returns_only_genera_that_can_exist():
    system = _system(stars={"S": StarInfo("S", "G", "V", 0.0)}, main_star_name="S", main_star_type="G",
                     main_star_luminosity="V")
    airless = BodyContext(name="b", body_type="Rocky body", atmosphere="None", gravity=2.0, temperature=300.0,
                          parent_stars=["S"])
    assert "Tussock" not in {GENUS_DATA[g]["name"] for g in match_body(airless, system)}


def test_engine_reports_the_remaining_species_and_value_range():
    from app.parser.exobiology import _genus_candidate

    stratum_key = next(k for k, v in GENUS_DATA.items() if v["name"] == "Stratum" and "Genus" in k)
    by_name = {d["name"]: k for k, d in SPECIES_RULES[stratum_key].items()}
    remaining = [
        (stratum_key, by_name["Stratum Tectonicas"], ["Emerald"]),
        (stratum_key, by_name["Stratum Paleas"], ["Emerald", "Teal"]),
    ]
    entry = _genus_candidate("Stratum", remaining, genus_certain=True)
    # The cheapest remaining species stands in; the rest are listed as alternates
    assert entry["species"] == "Stratum Paleas"
    assert entry["candidate_species"] == ["Stratum Paleas", "Stratum Tectonicas"]
    assert entry["alternate_species"] == ["Stratum Tectonicas"]
    assert entry["species_in_genus"] == 2
    assert entry["min_value"] == entry["base_value"] < entry["max_value"] == 19010800
    assert entry["possible_pct"] == 50
    assert entry["confidence"] == "possible" and entry["genus_confirmed"] is True
    assert entry["variant_color"] == "" and entry["alternate_variants"] == ["Emerald", "Teal"]

    single = _genus_candidate("Stratum", remaining[:1], genus_certain=True)
    assert single["confidence"] == "definite" and single["variant_color"] == "Emerald"
    assert single["species_variant"] == "Stratum Tectonicas - Emerald"


def test_system_detail_api_reports_the_galactic_region(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    import app.db.database as database
    from app.server.api import app

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "region.db")
    database.init_db(force=True)
    conn = database.get_db_connection()
    conn.execute(
        "INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, edsm_checked, edsm_registered) "
        "VALUES (7, 'Colonia', -9530.5, -910.3, 19808.1, 1, 0)"
    )
    conn.commit()
    conn.close()
    system = TestClient(app).get("/api/system/7").json()["system"]
    assert system["galactic_region_id"] == 9
    assert system["galactic_region_en"] == "Inner Scutum-Centaurus Arm"
    assert system["galactic_region_ja"] == "内たて・ケンタウルス腕"


def test_recompute_replaces_stored_predictions_and_keeps_scanned_organics(tmp_path, monkeypatch):
    import json
    import sqlite3

    from app.addons import addon_manager
    from app.db.database import init_db
    from app.parser.journal_parser import JournalParser

    conn = sqlite3.connect(str(tmp_path / "recompute.db"))
    conn.row_factory = sqlite3.Row
    init_db(conn)
    old = json.dumps([{"species": "Bacterium Informis", "genus": "Bacterium", "confidence": "definite", "base_value": 1}])
    conn.execute("INSERT INTO systems (system_address, star_system, star_pos_x, star_pos_y, star_pos_z, main_star_type) "
                 "VALUES (9, 'Sys', 0, 0, 0, 'F')")
    conn.execute("INSERT INTO bodies (system_address, body_id, body_name, star_type, luminosity, distance_from_arrival_ls) "
                 "VALUES (9, 0, 'Sys A', 'F', 'V', 0)")
    conn.execute(
        "INSERT INTO bodies (system_address, body_id, body_name, planet_class, atmosphere_type, surface_gravity, "
        "surface_gravity_g, surface_temperature, surface_pressure, landable, bio_signals, exobiology_predictions, parents) "
        "VALUES (9, 1, 'Sys A 1', 'High metal content body', 'CarbonDioxide', 2.94, 0.30, 240.0, 3546.0, 1, 2, ?, '[{\"Star\": 0}]')",
        (old,),
    )
    conn.execute(
        "INSERT INTO bodies (system_address, body_id, body_name, planet_class, landable, bio_signals, exobiology_predictions) "
        "VALUES (9, 2, 'Sys A 2', 'Rocky body', 1, 0, ?)", (old,)
    )
    conn.execute(
        "INSERT INTO scanned_organics (system_address, body_id, body_name, timestamp, scan_type, genus_localised, "
        "species_localised, base_value, first_discovery_value) "
        "VALUES (9, 1, 'Sys A 1', 't', 'Analyse', 'Stratum', 'Stratum Tectonicas', 19010800, 95054000)"
    )
    conn.commit()

    result = JournalParser(conn).recompute_exobiology_predictions()
    assert result == {"skipped": False, "bodies": 1, "updated": 1}  # only bodies with bio signals

    preds = json.loads(conn.execute("SELECT exobiology_predictions FROM bodies WHERE body_id = 1").fetchone()[0])
    assert "Bacterium Informis" not in {p["species"] for p in preds}
    tectonicas = next(p for p in preds if p["species"] == "Stratum Tectonicas")
    assert tectonicas["confidence"] == "confirmed" and tectonicas["locked"] is True and tectonicas["stage_level"] == 3
    # Bodies without bio signals are left alone
    assert json.loads(conn.execute("SELECT exobiology_predictions FROM bodies WHERE body_id = 2").fetchone()[0]) == json.loads(old)

    # With the prediction addon off nothing is touched
    monkeypatch.setattr(addon_manager, "get_provider", lambda name: None)
    assert JournalParser(conn).recompute_exobiology_predictions()["skipped"] is True
    conn.close()
