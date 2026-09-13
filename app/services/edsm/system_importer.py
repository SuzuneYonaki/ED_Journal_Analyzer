"""
EDSM System Importer.
Handles fetching system information, coordinates, allegiance, economy, factions,
and orchestrating body, station, and stats completion.
"""

import json
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any

from app.db.database import get_db_connection
from app.services.edsm.constants import (
    EDSM_SYSTEM_API,
    EDSM_BODIES_API,
    EDSM_FACTIONS_API,
    ENABLE_EDSM_BODY_COMPLETION,
    USER_AGENT
)


def import_unvisited_system_by_name(
    client,
    system_name: str,
    body_importer_func,
    station_importer_func,
    stats_aggregator_func
) -> dict:
    """
    Fetches an unvisited system by name directly from EDSM and inserts/updates it into
    the database with is_external = 1, visit_count = 0.
    Also fetches and completes all celestial bodies so the user can inspect it immediately.
    """
    clean_name = (system_name or "").strip()
    if not clean_name:
        return {"success": False, "error": "System name is empty"}

    if client:
        client.throttle_delay()
    encoded_name = urllib.parse.quote(clean_name)
    sys_url = f"{EDSM_SYSTEM_API}?systemName={encoded_name}&showInformation=1&showCoordinates=1&showId=1"

    req = urllib.request.Request(
        sys_url,
        headers={"User-Agent": USER_AGENT}
    )

    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            if resp.status != 200:
                return {"success": False, "error": f"EDSM HTTP {resp.status}"}
            sys_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e)}

    if not sys_data or not isinstance(sys_data, dict) or not sys_data.get("name"):
        return {"success": False, "error": f"System '{clean_name}' not found on EDSM"}

    star_sys_name = sys_data.get("name")
    system_address = sys_data.get("id64")
    if not system_address:
        system_address = sys_data.get("id")

    if not system_address:
        return {"success": False, "error": "System address (id64) not found in EDSM response"}

    coords = sys_data.get("coords") or {}
    pos_x = coords.get("x")
    pos_y = coords.get("y")
    pos_z = coords.get("z")

    sol_dist = 0.0
    if pos_x is not None and pos_y is not None and pos_z is not None:
        sol_dist = round((pos_x * pos_x + pos_y * pos_y + pos_z * pos_z) ** 0.5, 1)

    info = sys_data.get("information") or {}
    allegiance = info.get("allegiance")
    government = info.get("government")
    economy = info.get("economy")
    second_economy = info.get("secondEconomy")
    security = info.get("security")
    population = info.get("population") or 0
    faction = info.get("faction")
    faction_state = info.get("factionState")
    reserve = info.get("reserve")

    # Fetch detailed factions if populated (skip if unpopulated exploration system)
    factions_json = "[]"
    if faction or population > 0:
        try:
            if client:
                client.throttle_delay()
            factions_url = f"{EDSM_FACTIONS_API}?systemName={encoded_name}"
            factions_req = urllib.request.Request(
                factions_url,
                headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(factions_req, timeout=8.0) as f_resp:
                if f_resp.status == 200:
                    f_data = json.loads(f_resp.read().decode("utf-8"))
                    if isinstance(f_data, dict) and "factions" in f_data:
                        factions_json = json.dumps(f_data.get("factions", []))
        except Exception as e:
            print(f"[EDSM Service] Error fetching factions for {star_sys_name}: {e}")

    # Fetch bodies from EDSM
    if client:
        client.throttle_delay()
    bodies_url = f"{EDSM_BODIES_API}?systemName={encoded_name}"
    bodies_req = urllib.request.Request(
        bodies_url,
        headers={"User-Agent": USER_AGENT}
    )

    first_discoverer = None
    submitted_at = None
    body_count = 0
    bodies_list = []

    try:
        with urllib.request.urlopen(bodies_req, timeout=10.0) as b_resp:
            if b_resp.status == 200:
                b_data = json.loads(b_resp.read().decode("utf-8"))
                if isinstance(b_data, dict):
                    body_count = b_data.get("bodyCount", 0)
                    bodies_list = b_data.get("bodies", [])
    except Exception as e:
        print(f"[EDSM Service] Error fetching bodies for {star_sys_name}: {e}")

    for b in bodies_list:
        disc = b.get("discovery")
        if isinstance(disc, dict) and disc.get("commander"):
            if not first_discoverer:
                first_discoverer = disc.get("commander")
                submitted_at = disc.get("date")
            break

    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT system_address, visit_count, is_external FROM systems WHERE system_address = ?", (system_address,))
    existing_sys = c.fetchone()

    if existing_sys:
        c.execute("""
            UPDATE systems SET
                star_system = ?,
                star_pos_x = COALESCE(?, star_pos_x),
                star_pos_y = COALESCE(?, star_pos_y),
                star_pos_z = COALESCE(?, star_pos_z),
                sol_distance_ly = CASE WHEN ? > 0 THEN ? ELSE sol_distance_ly END,
                system_allegiance = COALESCE(?, system_allegiance),
                system_government = COALESCE(?, system_government),
                system_economy = COALESCE(?, system_economy),
                system_second_economy = COALESCE(?, system_second_economy),
                system_security = COALESCE(?, system_security),
                system_state = COALESCE(NULLIF(?, ''), system_state),
                controlling_faction = COALESCE(NULLIF(?, ''), controlling_faction),
                system_reserve = COALESCE(NULLIF(?, ''), system_reserve),
                edsm_factions_json = CASE WHEN ? != '[]' THEN ? ELSE edsm_factions_json END,
                population = CASE WHEN ? > 0 THEN ? ELSE population END,
                edsm_checked = 1,
                edsm_registered = 1,
                edsm_first_discoverer = ?,
                edsm_submitted_at = ?,
                edsm_body_count = ?
            WHERE system_address = ?
        """, (
            star_sys_name, pos_x, pos_y, pos_z, sol_dist, sol_dist,
            allegiance, government, economy, second_economy, security,
            faction_state, faction, reserve,
            factions_json, factions_json,
            population, population,
            first_discoverer, submitted_at, body_count, system_address
        ))
    else:
        c.execute("""
            INSERT INTO systems (
                system_address, star_system, star_pos_x, star_pos_y, star_pos_z, sol_distance_ly,
                system_allegiance, system_government, system_economy, system_second_economy,
                system_security, system_state, controlling_faction, system_reserve, edsm_factions_json,
                population, first_visited, last_visited, visit_count, is_external,
                edsm_checked, edsm_registered, edsm_first_discoverer, edsm_submitted_at, edsm_body_count
            ) VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, NULL, NULL, 0, 1,
                1, 1, ?, ?, ?
            )
        """, (
            system_address, star_sys_name, pos_x, pos_y, pos_z, sol_dist,
            allegiance, government, economy, second_economy,
            security, faction_state or "", faction or "", reserve or "", factions_json,
            population,
            first_discoverer, submitted_at, body_count
        ))

    completed_count = 0
    if bodies_list and body_importer_func:
        completed_count = body_importer_func(conn, system_address, star_sys_name, bodies_list)

    if station_importer_func:
        try:
            is_uninhabited = (population == 0 and not faction and not allegiance)
            station_importer_func(client, conn, system_address, star_sys_name, is_uninhabited=is_uninhabited)
        except Exception as e:
            print(f"[EDSM Service] Error importing stations for unvisited system: {e}")

    if stats_aggregator_func:
        stats_aggregator_func(conn, system_address)

    conn.commit()
    conn.close()

    try:
        from app.server.api import manager
        manager.notify_update_from_thread(None)
    except Exception:
        pass

    return {
        "success": True,
        "system_address": system_address,
        "star_system": star_sys_name,
        "first_discoverer": first_discoverer,
        "body_count": body_count,
        "completed_bodies": completed_count,
        "is_external": 1 if not existing_sys or existing_sys["visit_count"] == 0 else 0
    }


def fetch_and_update_system(
    client,
    system_address: int,
    system_name: str,
    body_importer_func,
    station_importer_func,
    stats_aggregator_func
) -> dict:
    """Fetches system info and body discoveries from EDSM and updates the database."""
    encoded_name = urllib.parse.quote(system_name)
    sys_url = f"{EDSM_SYSTEM_API}?systemName={encoded_name}&showInformation=1&showCoordinates=1&showId=1"

    req = urllib.request.Request(
        sys_url,
        headers={"User-Agent": USER_AGENT}
    )

    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            if resp.status != 200:
                if client:
                    client.mark_checked_unregistered(system_address)
                return {"registered": False, "status": "http_error", "code": resp.status}
            sys_data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        if client:
            client.mark_checked_unregistered(system_address)
        return {"registered": False, "status": "error", "error": str(e)}

    # An empty dictionary or missing name indicates system is not in EDSM
    if not sys_data or not isinstance(sys_data, dict) or not sys_data.get("name"):
        if client:
            client.mark_checked_unregistered(system_address)
        return {"registered": False, "status": "not_found"}

    # Extract information (economy, government, allegiance, state, faction, reserve)
    info = sys_data.get("information") or {}
    allegiance = info.get("allegiance")
    government = info.get("government")
    economy = info.get("economy")
    second_economy = info.get("secondEconomy")
    security = info.get("security")
    population = info.get("population") or 0
    faction = info.get("faction")
    faction_state = info.get("factionState")
    reserve = info.get("reserve")

    # Fetch detailed factions if populated (skip for unpopulated exploration systems)
    factions_json = "[]"
    if faction or population > 0:
        try:
            if client:
                client.throttle_delay()
            factions_url = f"{EDSM_FACTIONS_API}?systemName={encoded_name}"
            factions_req = urllib.request.Request(
                factions_url,
                headers={"User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(factions_req, timeout=8.0) as f_resp:
                if f_resp.status == 200:
                    f_data = json.loads(f_resp.read().decode("utf-8"))
                    if isinstance(f_data, dict) and "factions" in f_data:
                        factions_json = json.dumps(f_data.get("factions", []))
        except Exception as e:
            print(f"[EDSM Service] Error fetching factions for {system_name}: {e}")

    # Check bodies for first discoverer and complete celestial bodies
    if client:
        client.throttle_delay()
    bodies_url = f"{EDSM_BODIES_API}?systemName={encoded_name}"
    bodies_req = urllib.request.Request(
        bodies_url,
        headers={"User-Agent": USER_AGENT}
    )

    first_discoverer = None
    submitted_at = None
    body_count = 0
    bodies_list = []

    try:
        with urllib.request.urlopen(bodies_req, timeout=10.0) as b_resp:
            if b_resp.status == 200:
                b_data = json.loads(b_resp.read().decode("utf-8"))
                if isinstance(b_data, dict):
                    body_count = b_data.get("bodyCount", 0)
                    bodies_list = b_data.get("bodies", [])
    except Exception as e:
        print(f"[EDSM Service] Error fetching bodies for {system_name}: {e}")

    # Extract discoverer from primary star or bodies
    for b in bodies_list:
        disc = b.get("discovery")
        if isinstance(disc, dict) and disc.get("commander"):
            if not first_discoverer:
                first_discoverer = disc.get("commander")
                submitted_at = disc.get("date")
            break

    # Save to SQLite
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE systems SET
            edsm_checked = 1,
            edsm_registered = 1,
            edsm_first_discoverer = ?,
            edsm_submitted_at = ?,
            edsm_body_count = ?,
            system_allegiance = COALESCE(?, system_allegiance),
            system_government = COALESCE(?, system_government),
            system_economy = COALESCE(?, system_economy),
            system_second_economy = COALESCE(?, system_second_economy),
            system_security = COALESCE(?, system_security),
            system_state = COALESCE(NULLIF(?, ''), system_state),
            controlling_faction = COALESCE(NULLIF(?, ''), controlling_faction),
            system_reserve = COALESCE(NULLIF(?, ''), system_reserve),
            edsm_factions_json = CASE WHEN ? != '[]' THEN ? ELSE edsm_factions_json END,
            population = CASE WHEN ? > 0 THEN ? ELSE population END
        WHERE system_address = ?
    """, (
        first_discoverer, submitted_at, body_count,
        allegiance, government, economy, second_economy, security,
        faction_state, faction, reserve,
        factions_json, factions_json,
        population, population,
        system_address
    ))

    # Import or backfill missing bodies from EDSM
    completed_count = 0
    if bodies_list and ENABLE_EDSM_BODY_COMPLETION and body_importer_func:
        completed_count = body_importer_func(conn, system_address, system_name, bodies_list)

    # Import stations from EDSM (optimized to skip uninhabited systems)
    if station_importer_func:
        try:
            is_uninhabited = (population == 0 and not faction and not allegiance)
            station_importer_func(client, conn, system_address, system_name, is_uninhabited=is_uninhabited)
        except Exception as e:
            print(f"[EDSM Service] Error importing stations: {e}")

    # Recalculate and update aggregated system statistics
    if stats_aggregator_func:
        stats_aggregator_func(conn, system_address)

    conn.commit()
    conn.close()

    # Notify front-end via WebSocket if available
    try:
        from app.server.api import manager
        manager.notify_update_from_thread(None)
    except Exception:
        pass

    return {
        "registered": True,
        "status": "success",
        "first_discoverer": first_discoverer,
        "body_count": body_count,
        "completed_bodies": completed_count
    }
