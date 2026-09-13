"""
EDSM Stations and Planetary Settlements Importer.
Fetches stations and settlements, evaluates large pad capabilities,
and updates the stations table in SQLite.
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from app.services.edsm.constants import EDSM_STATIONS_API, USER_AGENT


def import_and_complete_stations(client, conn, system_address: int, system_name: str, is_uninhabited: bool = False) -> int:
    """
    Fetches stations and planetary settlements from EDSM and stores/updates in the stations table.
    Optimized: Skips query completely if system is confirmed uninhabited.
    """
    if is_uninhabited:
        return 0

    encoded_name = urllib.parse.quote(system_name)
    stations_url = f"{EDSM_STATIONS_API}?systemName={encoded_name}"
    stations_req = urllib.request.Request(
        stations_url,
        headers={"User-Agent": USER_AGENT}
    )
    stations_list = []
    try:
        if client:
            client.throttle_delay()
        with urllib.request.urlopen(stations_req, timeout=8.0) as st_resp:
            if st_resp.status == 200:
                st_data = json.loads(st_resp.read().decode("utf-8"))
                if isinstance(st_data, dict):
                    stations_list = st_data.get("stations", [])
    except Exception as e:
        print(f"[EDSM Service] Error fetching stations for {system_name}: {e}")
        return 0

    if not stations_list:
        return 0

    c = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    count = 0
    for st in stations_list:
        st_name = st.get("name")
        if not st_name:
            continue
        st_type = st.get("type")
        m_id = st.get("marketId")
        dist_arr = st.get("distanceToArrival")
        b_obj = st.get("body") or {}
        b_name = b_obj.get("name") if isinstance(b_obj, dict) else None
        b_id = b_obj.get("id") if isinstance(b_obj, dict) else None
        lat = b_obj.get("latitude") if isinstance(b_obj, dict) else None
        lon = b_obj.get("longitude") if isinstance(b_obj, dict) else None
        is_planet = 1 if (lat is not None and lon is not None) or (st_type and ("Planetary" in st_type or "Settlement" in st_type)) else 0
        alleg = st.get("allegiance")
        econ = st.get("economy")
        gov = st.get("government")
        ctrl_fac = st.get("controllingFaction", {})
        ctrl_name = ctrl_fac.get("name") if isinstance(ctrl_fac, dict) else ctrl_fac

        large_pad_types = [
            "starport", "coriolis", "orbis", "ocellus", "asteroid", "megaship",
            "mega ship", "fleetcarrier", "fleet carrier", "planetary port"
        ]
        st_type_lower = (st_type or "").lower()
        has_large_pad = 1 if any(t in st_type_lower for t in large_pad_types) else 0

        try:
            c.execute("""
                INSERT INTO stations (
                    system_address, market_id, station_name, station_type, body_name, body_id,
                    latitude, longitude, distance_to_arrival_ls, allegiance, economy, government,
                    controlling_faction, is_planetary, has_large_pad, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address, station_name) DO UPDATE SET
                    market_id = COALESCE(excluded.market_id, stations.market_id),
                    station_type = COALESCE(excluded.station_type, stations.station_type),
                    body_name = COALESCE(excluded.body_name, stations.body_name),
                    body_id = COALESCE(excluded.body_id, stations.body_id),
                    latitude = COALESCE(excluded.latitude, stations.latitude),
                    longitude = COALESCE(excluded.longitude, stations.longitude),
                    distance_to_arrival_ls = COALESCE(excluded.distance_to_arrival_ls, stations.distance_to_arrival_ls),
                    allegiance = COALESCE(excluded.allegiance, stations.allegiance),
                    economy = COALESCE(excluded.economy, stations.economy),
                    government = COALESCE(excluded.government, stations.government),
                    controlling_faction = COALESCE(excluded.controlling_faction, stations.controlling_faction),
                    is_planetary = CASE WHEN excluded.is_planetary = 1 THEN 1 ELSE stations.is_planetary END,
                    has_large_pad = CASE WHEN excluded.has_large_pad = 1 THEN 1 ELSE stations.has_large_pad END,
                    updated_at = excluded.updated_at
            """, (
                system_address, m_id, st_name, st_type, b_name, b_id,
                lat, lon, dist_arr, alleg, econ, gov,
                ctrl_name, is_planet, has_large_pad, now_iso
            ))
            count += 1
        except Exception:
            pass
    return count
