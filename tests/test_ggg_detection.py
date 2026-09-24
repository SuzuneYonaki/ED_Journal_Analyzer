import pytest
import sqlite3
import json
from app.db.database import init_db, get_celestial_statistics
from app.parser.rarity_scorer import calculate_celestial_rarity, calculate_ggg_probability
from app.parser.journal_parser import resolve_ggg_variant

def test_resolve_ggg_variant():
    assert resolve_ggg_variant("$Codex_Ent_Green_Sudarsky_Class_I_Name;") is not None
    res = resolve_ggg_variant("$Codex_Ent_Green_Sudarsky_Class_I_Name;")
    assert res[0].lower() == "sudarsky_class_i"
    assert "クラス1" in res[1]

    # Non-GGG codex entry
    assert resolve_ggg_variant("$Codex_Ent_Biol_Tubeworm_Name;") is None
    assert resolve_ggg_variant(None) is None

def test_ggg_candidate_vs_confirmed():
    # 1. Body matching GGG conditions (water based life gas giant in viable temp/mass)
    candidate_body = {
        "BodyName": "Test Gas Giant A 1",
        "PlanetClass": "Sudarsky Class I gas giant with water-based life",
        "SurfaceTemperature": 220.0,
        "MassEM": 150.0,
        "DistanceFromArrivalLS": 1200.0,
        "parent_star_type": "G"
    }
    prob = calculate_ggg_probability(candidate_body)
    assert prob["is_candidate"] is True
    assert prob["score"] >= 80
    assert prob["alert_level"] == "URGENT"
    assert "高確率のグリーンガスジャイアント候補" in prob["tts_message"]

    # Evaluate rarity without codex confirmation
    rarity_candidate = calculate_celestial_rarity(candidate_body, is_confirmed_ggg=False)
    # Must have "GGG Candidate", but NEVER "Confirmed GGG" or "Green Gas Giant Candidate"
    assert "GGG Candidate" in rarity_candidate["tags"]
    assert "Green Gas Giant Candidate" not in rarity_candidate["tags"]
    assert "Confirmed GGG" not in rarity_candidate["tags"]
    assert rarity_candidate["ggg_evaluation"]["is_confirmed"] is False

    # 2. Body with Codex confirmed GGG
    rarity_confirmed = calculate_celestial_rarity(
        candidate_body,
        is_confirmed_ggg=True,
        confirmed_ggg_variant="Sudarsky Class I Gas Giant"
    )
    assert "Confirmed GGG" in rarity_confirmed["tags"]
    assert "Confirmed GGG (Sudarsky Class I Gas Giant)" in rarity_confirmed["tags"]
    assert "GGG Candidate" not in rarity_confirmed["tags"]
    assert rarity_confirmed["ggg_evaluation"]["is_confirmed"] is True

def test_celestial_statistics_ggg_separation():
    # Test on an in-memory database
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    cursor = conn.cursor()
    # Insert system
    cursor.execute("INSERT INTO systems (system_address, star_system) VALUES (12345, 'Test System')")
    
    # Insert body with GGG Candidate tag
    cursor.execute("""
        INSERT INTO bodies (
            system_address, body_id, body_name, planet_class, anomalies_json
        ) VALUES (
            12345, 1, 'Candidate Planet', 'Gas giant with water based life',
            '[{"type": "ggg_candidate", "tag": "GGG Candidate", "color": "cyan"}]'
        )
    """)

    # Insert body with Confirmed GGG
    cursor.execute("""
        INSERT INTO bodies (
            system_address, body_id, body_name, planet_class, anomalies_json
        ) VALUES (
            12345, 2, 'Confirmed Planet', 'Gas giant with water based life',
            '[{"type": "confirmed_ggg", "tag": "Confirmed GGG", "color": "green"}]'
        )
    """)

    stats = get_celestial_statistics(conn)
    # Green gas giant count must be 1 (only the confirmed one, not the candidate)
    assert stats["planets"]["green_gas_giant"] == 1
    assert stats["planets"]["gas_giant_water_life"] == 2
    conn.close()
