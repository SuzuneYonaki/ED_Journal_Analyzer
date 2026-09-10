import pytest
from fastapi.testclient import TestClient
from app.server.api import app
from app.db.database import get_db_connection, init_db
from app.services.footprint_service import footprint_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_footprint_local_db_skipped():
    """Test that systems in local DB return in_local_db=True and summary='local_db' without external call."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO systems (system_address, star_system, visit_count)
        VALUES (9999901, 'TestLocalSystem123', 2)
    """)
    conn.commit()
    conn.close()

    res = client.get("/api/external_footprint?system_name=TestLocalSystem123")
    assert res.status_code == 200
    data = res.json()
    assert data["in_local_db"] is True
    assert data["has_footprint"] is True
    assert data["summary"] == "local_db"

def test_footprint_fake_system_uncharted():
    """Test that a completely non-existent system returns has_footprint=False and summary='not_found'."""
    fake_name = "FakeSystem999999999_DefinitelyDoesNotExist"
    res = client.get(f"/api/external_footprint?system_name={fake_name}")
    assert res.status_code == 200
    data = res.json()
    assert data["in_local_db"] is False
    assert data["has_footprint"] is False
    assert data["summary"] == "not_found"

def test_footprint_caching():
    """Test that second query for the same system returns cached response."""
    test_name = "FakeCachedSystem123"
    res1 = client.get(f"/api/external_footprint?system_name={test_name}")
    assert res1.status_code == 200
    res2 = client.get(f"/api/external_footprint?system_name={test_name}")
    assert res2.status_code == 200
    assert res1.json() == res2.json()
