import pytest
from fastapi.testclient import TestClient
from app.server.api import app
from app.db.database import get_db_connection, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_db_connection()
    c = conn.cursor()

    # Create test systems
    c.execute("INSERT OR REPLACE INTO systems (system_address, star_system, main_star_type, total_potential_value) VALUES (888001, 'Sys-Supergiant-I', 'B', 1000)")
    c.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_type, luminosity) VALUES (888001, 1, 'Star-I', 'B', 'Ia')")

    c.execute("INSERT OR REPLACE INTO systems (system_address, star_system, main_star_type, total_potential_value) VALUES (888002, 'Sys-Giant-III', 'M', 2000)")
    c.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_type, luminosity) VALUES (888002, 1, 'Star-III', 'M', 'IIIab')")

    c.execute("INSERT OR REPLACE INTO systems (system_address, star_system, main_star_type, total_potential_value) VALUES (888003, 'Sys-Subdwarf-VI', 'G', 3000)")
    c.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_type, luminosity) VALUES (888003, 1, 'Star-VI', 'G', 'VI')")

    c.execute("INSERT OR REPLACE INTO systems (system_address, star_system, main_star_type, total_potential_value) VALUES (888004, 'Sys-Degenerate-WD', 'D', 4000)")
    c.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_type, luminosity) VALUES (888004, 1, 'Star-WD', 'DA', 'VII')")

    c.execute("INSERT OR REPLACE INTO systems (system_address, star_system, main_star_type, total_potential_value) VALUES (888005, 'Sys-MainSequence-V', 'G', 5000)")
    c.execute("INSERT OR REPLACE INTO bodies (system_address, body_id, body_name, star_type, luminosity) VALUES (888005, 1, 'Star-V', 'G', 'Va')")

    conn.commit()
    conn.close()

def test_luminosity_filter_all_when_unchecked():
    """Unchecked luminosity should return all matching systems."""
    res = client.get("/api/systems?q=Sys-&limit=50")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "Sys-Supergiant-I" in names
    assert "Sys-Giant-III" in names
    assert "Sys-Subdwarf-VI" in names
    assert "Sys-Degenerate-WD" in names
    assert "Sys-MainSequence-V" in names

def test_luminosity_filter_giant_III():
    """Filtering by luminosity III should return giant stars only."""
    res = client.get("/api/systems?q=Sys-&luminosity_classes=III")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "Sys-Giant-III" in names
    assert "Sys-Supergiant-I" not in names
    assert "Sys-Subdwarf-VI" not in names

def test_luminosity_filter_subdwarf_VI():
    """Filtering by luminosity VI should return subdwarf stars only."""
    res = client.get("/api/systems?q=Sys-&luminosity_classes=VI")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "Sys-Subdwarf-VI" in names
    assert "Sys-Giant-III" not in names

def test_luminosity_filter_degenerate_VII():
    """Filtering by luminosity VII should return degenerate (White Dwarf) stars."""
    res = client.get("/api/systems?q=Sys-&luminosity_classes=VII")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "Sys-Degenerate-WD" in names
    assert "Sys-Supergiant-I" not in names

def test_combined_spectral_and_luminosity_filter():
    """Spectral type M + Luminosity III should return Red Giants specifically."""
    res = client.get("/api/systems?q=Sys-&star_types=M&luminosity_classes=III")
    assert res.status_code == 200
    names = [s["star_system"] for s in res.json()["systems"]]
    assert "Sys-Giant-III" in names
    assert "Sys-Supergiant-I" not in names
    assert "Sys-Subdwarf-VI" not in names
