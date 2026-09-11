import pytest
from fastapi.testclient import TestClient
from app.server.api import app, get_db_connection
from app.services.physics_translator import (
    translate_narrative_report_to_ja,
    translate_anomalies_list_to_ja,
    translate_anomaly_to_ja
)

client = TestClient(app)

def test_physics_translator_units():
    # Test anomaly translation
    en_anom1 = "Mega-Earth anomaly: Planet 1 (R=1.8 R_Earth > 1.6, density=5.5 g/cm^3; Weiss & Marcy 2014 transition)"
    ja_anom1 = translate_anomaly_to_ja(en_anom1)
    assert "メガ・アース特異点" in ja_anom1
    assert "Weiss & Marcy 2014" in ja_anom1

    # Test anomalies list translation
    en_anoms = [
        "Mega-Earth anomaly: Planet 1 (R=1.8 R_Earth > 1.6, density=5.5 g/cm^3; Weiss & Marcy 2014 transition)",
        "Super-Mercury mantle stripping: Planet 2 (density=9.2 g/cm^3 > 8.0 g/cm^3)"
    ]
    ja_anoms = translate_anomalies_list_to_ja(en_anoms)
    assert len(ja_anoms) == 2
    assert "メガ・アース特異点" in ja_anoms[0]
    assert "スーパー・マーキュリー" in ja_anoms[1]

    # Test narrative report translation
    en_report = (
        "ASTROPHYSICAL EXPLORATION REPORT:\n"
        "[EXECUTIVE SUMMARY]\n"
        "A profound astronomical anomaly featuring 2 star(s) and 5 planetary body/bodies.\n"
        "[HABITABLE WORLDS (FAMILIAR SCALE BREAKDOWN)]\n"
        "temperate, hospitable Earth-like climate\n"
        "comparable to Mercury's orbit"
    )
    ja_report = translate_narrative_report_to_ja(en_report)
    assert "天体物理・探査レポート" in ja_report
    assert "【総合サマリー / 概況】" in ja_report
    assert "温暖・生命居住に適した地球型気候" in ja_report
    assert "水星の公転軌道に匹敵する至近距離" in ja_report

    # Test updated polar orbit phrasing
    polar_en = "Orthogonal/polar orbit detected on Planet 4 relative to system reference plane (inclination=92.10 deg)"
    polar_ja = translate_anomaly_to_ja(polar_en)
    assert "星系基準軌道面に対して直交する極軌道" in polar_ja

    # Test updated Habitable Zone '確認' phrasing
    hz_en = "Planet 3 confirmed in conservative Habitable Zone (Kopparapu 2013, S_eff=1.02)"
    hz_ja = translate_anomaly_to_ja(hz_en)
    assert "確認" in hz_ja
    assert "実証" not in hz_ja

def test_api_systems_rarity_score_and_sort():
    res = client.get("/api/systems?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "systems" in data
    assert len(data["systems"]) > 0
    first_sys = data["systems"][0]
    assert "rarity_score" in first_sys

    res_sorted = client.get("/api/systems?sort_by=rarity_score&sort_order=desc&limit=5")
    assert res_sorted.status_code == 200
    sorted_data = res_sorted.json()
    scores = [s.get("rarity_score") or 10.0 for s in sorted_data["systems"]]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1]

def test_api_system_physics_detail_and_ondemand():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT system_address FROM bodies GROUP BY system_address HAVING COUNT(*) > 1 LIMIT 1")
    row = c.fetchone()
    conn.close()

    assert row is not None, "At least one system with scannable bodies should exist in the test DB"
    sys_addr = row["system_address"]

    res = client.get(f"/api/system/{sys_addr}")
    assert res.status_code == 200
    data = res.json()
    assert "physics_evaluation" in data
    eval_data = data["physics_evaluation"]
    assert eval_data is not None
    assert "rarity_score" in eval_data
    assert eval_data["rarity_score"] >= 10.0
    assert "anomalies_en" in eval_data
    assert "anomalies_ja" in eval_data
    assert "narrative_report_en" in eval_data
    assert "narrative_report_ja" in eval_data
    assert "raw_features" in eval_data

    res_phys = client.get(f"/api/systems/{sys_addr}/physics")
    assert res_phys.status_code == 200
    phys_json = res_phys.json()
    assert phys_json["system_address"] == sys_addr
    assert "rarity_score" in phys_json
    assert "narrative_report_ja" in phys_json
    assert "narrative_report_en" in phys_json
