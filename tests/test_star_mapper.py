"""
Automated unit tests for Elite Dangerous Star Mapper.
"""

import pytest
from star_mapper.services.mapper_service import MapperService
from star_mapper.db.database import (
    init_db,
    upsert_cached_system,
    get_cached_system_by_name,
    get_cached_system_by_address
)


def test_database_caching():
    init_db()
    upsert_cached_system(
        system_address=123456789,
        name="Test Star System Alpha",
        pos_x=10.5,
        pos_y=-2.0,
        pos_z=45.0,
        first_discoverer="CMDR StarWalker",
        discovery_date="3308-01-01",
        is_registered=1,
        body_count=12,
        source="edsm"
    )

    by_addr = get_cached_system_by_address(123456789)
    assert by_addr is not None
    assert by_addr["name"] == "Test Star System Alpha"
    assert by_addr["first_discoverer"] == "CMDR StarWalker"
    assert by_addr["body_count"] == 12

    by_name = get_cached_system_by_name("test star system alpha")
    assert by_name is not None
    assert by_name["system_address"] == 123456789


def test_mapper_service_sorting():
    svc = MapperService()
    # Mock data
    with svc.systems_lock:
        svc.session_systems = {
            1: {"system_address": 1, "name": "Near Undisc", "distance": 2.1, "first_discoverer": None},
            2: {"system_address": 2, "name": "Far Disc", "distance": 18.5, "first_discoverer": "CMDR Alice"},
            3: {"system_address": 3, "name": "Mid Disc", "distance": 8.0, "first_discoverer": "CMDR Bob"},
            4: {"system_address": 4, "name": "Far Undisc", "distance": 22.0, "first_discoverer": None}
        }

    # 1. Distance Ascending
    asc = svc.get_systems(sort_by="distance_asc", filter_disc="all")
    assert [s["name"] for s in asc] == ["Near Undisc", "Mid Disc", "Far Disc", "Far Undisc"]

    # 2. Distance Descending
    desc = svc.get_systems(sort_by="distance_desc", filter_disc="all")
    assert [s["name"] for s in desc] == ["Far Undisc", "Far Disc", "Mid Disc", "Near Undisc"]

    # 3. Discoverer First
    disc_first = svc.get_systems(sort_by="discoverer_first", filter_disc="all")
    # Both Far Disc and Mid Disc have discoverers; secondary sort should be distance ascending (Mid Disc then Far Disc)
    assert disc_first[0]["name"] == "Mid Disc"
    assert disc_first[1]["name"] == "Far Disc"
    # Undiscovered follows
    assert "Undisc" in disc_first[2]["name"]
    assert "Undisc" in disc_first[3]["name"]

    # 4. Filter Discovered Only
    disc_only = svc.get_systems(sort_by="distance_asc", filter_disc="discovered_only")
    assert len(disc_only) == 2
    assert all(s["first_discoverer"] for s in disc_only)
