"""
Rhino Mining Tracker.
Tracks and aggregates surface mining activities (both Raw materials and Refined commodities)
and interfaces with the note integrator.
"""

from typing import List, Dict, Any, Optional
import sqlite3
from app.live.rhino.note_integrator import update_body_note_in_db

def extract_all_mining_materials_for_body(
    conn: sqlite3.Connection,
    system_address: int,
    body_id: int
) -> List[Dict[str, Any]]:
    """
    Extracts all surface mining activities for a celestial body grouped by coordinate.
    Includes both Raw materials and Refined minerals.
    """
    c = conn.cursor()
    c.execute("""
        SELECT material_name, material_name_localised, latitude, longitude, timestamp
        FROM surface_mining_activities
        WHERE system_address = ? AND body_id = ?
        ORDER BY timestamp ASC
    """, (system_address, body_id))
    rows = c.fetchall()

    sites_map: Dict[tuple, Dict[str, Any]] = {}
    for r in rows:
        lat = r["latitude"]
        lon = r["longitude"]
        if lat is not None and lon is not None:
            coord_key = (round(float(lat), 4), round(float(lon), 4))
        else:
            coord_key = (None, None)

        m_name = r["material_name_localised"] or r["material_name"]
        if not m_name:
            continue

        if coord_key not in sites_map:
            sites_map[coord_key] = {
                "latitude": coord_key[0],
                "longitude": coord_key[1],
                "minerals": set()
            }
        sites_map[coord_key]["minerals"].add(m_name)

    result = []
    for data in sites_map.values():
        result.append({
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "minerals": sorted(list(data["minerals"]))
        })
    return result

def sync_body_mining_to_note(
    conn: sqlite3.Connection,
    system_address: int,
    body_id: int,
    body_name: str,
    star_system: str,
    target_lat: Optional[float] = None,
    target_lon: Optional[float] = None
) -> str:
    """
    Syncs mining records to the body's note.
    If target_lat and target_lon are given, syncs only that specific site.
    Otherwise, syncs all recorded sites for this body.
    """
    sites = extract_all_mining_materials_for_body(conn, system_address, body_id)
    if not sites:
        return ""

    updated_note = ""
    for site in sites:
        if target_lat is not None and target_lon is not None:
            if site["latitude"] != round(target_lat, 4) or site["longitude"] != round(target_lon, 4):
                continue
        updated_note = update_body_note_in_db(
            conn=conn,
            system_address=system_address,
            body_id=body_id,
            body_name=body_name,
            star_system=star_system,
            lat=site["latitude"],
            lon=site["longitude"],
            minerals=site["minerals"]
        )
    return updated_note
