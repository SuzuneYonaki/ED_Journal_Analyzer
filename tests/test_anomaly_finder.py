import pytest
from app.analyzer.anomaly_finder import detect_anomalies, detect_heavy_mass_code

def test_anomaly_finder_desc_en():
    # 1. Rare Stars
    sample_black_hole = {"star_type": "H", "star_system": "Bleia Eud KC-D d12-1"}
    anoms = detect_anomalies(sample_black_hole)
    assert any(a["tag"] == "Black Hole" and a.get("desc_en") == "Black Hole" for a in anoms)

    sample_neutron = {"star_type": "N", "star_system": "Bleia Eud KC-D d12-1"}
    anoms = detect_anomalies(sample_neutron)
    assert any(a["tag"] == "Neutron Star" and "Neutron Star (FSD Supercharge)" in a.get("desc_en", "") for a in anoms)

    # 2. Heavy Mass Code
    sample_heavy = {"star_type": "M", "star_system": "Bleia Eud KC-D e12-1"}
    heavy = detect_heavy_mass_code(sample_heavy["star_system"], sample_heavy["star_type"])
    assert heavy is not None
    assert "desc_en" in heavy
    assert "Supermassive Boxel" in heavy["desc_en"] or "Unusually Heavy Boxel" in heavy["desc_en"]

    # 3. Rare Planets
    sample_elw = {"planet_class": "Earth-like world"}
    anoms = detect_anomalies(sample_elw)
    assert any(a["tag"] == "Earth-like World" and "Earth-like World" in a.get("desc_en", "") for a in anoms)

    sample_ww_tf = {"planet_class": "Water world", "terraforming_state": "Terraformable"}
    anoms = detect_anomalies(sample_ww_tf)
    assert any("Terraformable Water World" in a.get("desc_en", "") for a in anoms)

    # 4. Extreme Orbit & Spin
    sample_orbit = {
        "eccentricity": 0.85,
        "orbital_period": 0.1 * 86400,
        "rotation_period": 1.5 * 3600,
        "orbital_inclination": 105.0,
        "tidal_lock": False
    }
    anoms = detect_anomalies(sample_orbit)
    tags = [a["tag"] for a in anoms]
    assert "Extreme Eccentricity" in tags
    assert "Ultra-Fast Orbit" in tags
    assert "Rapid Spinner" in tags
    assert "Retrograde Orbit" in tags
    for a in anoms:
        assert "desc_en" in a, f"Missing desc_en in anomaly: {a}"
        assert len(a["desc_en"]) > 0

    # 5. Extreme Gravity
    sample_high_g = {
        "landable": True,
        "surface_gravity_g": 3.5
    }
    anoms = detect_anomalies(sample_high_g)
    assert any("Extreme High-G Hazard" in a.get("desc_en", "") for a in anoms)

    # 6. Rings
    sample_ringed_star = {
        "star_type": "M",
        "rings": [{"Name": "Ring A", "OuterRad": 6000000000}]
    }
    anoms = detect_anomalies(sample_ringed_star)
    assert any(a["tag"] == "Ringed Star" and a.get("desc_en") == "Ringed Star" for a in anoms)
    assert any(a["tag"] == "Giant Ring System" and "Giant Ring System" in a.get("desc_en", "") for a in anoms)
