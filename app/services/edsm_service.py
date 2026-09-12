"""
EDSM (Elite Dangerous Star Map) API Integration Service.
Provides asynchronous rate-limited queries (minimum 1.0s delay per request)
to query system registration, discovery status, and celestial body discoveries.
Results are persisted into the local SQLite database as a permanent cache.

All code, strings, and comments in this module are strictly English ASCII.
"""

import json
import time
import urllib.parse
import urllib.request
import threading
import queue
from typing import Dict, Any, Optional

from app.db.database import get_db_connection
from app.parser.value_calculator import calculate_body_value, STAR_VALUES
from app.analyzer.anomaly_finder import detect_anomalies
from app.parser.exobiology import predict_exobiology_candidates

EDSM_SYSTEM_API = "https://www.edsm.net/api-v1/system"
EDSM_BODIES_API = "https://www.edsm.net/api-system-v1/bodies"

# Feature flag: Enable external body completion from EDSM
ENABLE_EDSM_BODY_COMPLETION = True
REQUEST_DELAY_SEC = 1.0  # Respectful community delay between external API calls
UNREGISTERED_RECHECK_COOLDOWN_SEC = 1800.0  # 30-minute in-memory cooldown before re-querying unregistered system


def _extract_star_type(b: dict) -> str:
    """Extract standard Elite star type code matching STAR_VALUES from EDSM body data."""
    subtype = b.get("subType", "") or ""
    sub_lower = subtype.lower()

    if "supermassive" in sub_lower and "black hole" in sub_lower:
        return "SupermassiveBlackHole"
    if "black hole" in sub_lower:
        return "H"
    if "neutron" in sub_lower:
        return "N"
    if "white dwarf" in sub_lower:
        for wd in ["DA", "DAB", "DAO", "DAZ", "DAV", "DB", "DBZ", "DBV", "DO", "DOV", "DQ", "DC", "DCV", "DX", "D"]:
            if f"({wd.lower()})" in sub_lower or f" {wd.lower()} " in f" {sub_lower} ":
                return wd
        return "D"

    spec = b.get("spectralClass")
    if spec and spec in STAR_VALUES:
        return spec

    # Token-based match (e.g. "M (Red dwarf) Star" -> "M", "TTS (T Tauri) Star" -> "TTS")
    token = subtype.split()[0] if subtype else "M"
    token_clean = token.split("(")[0].strip()
    if token_clean in STAR_VALUES:
        return token_clean

    return spec or "M"


class EDSMService:
    def __init__(self):
        self.high_priority_queue: queue.Queue = queue.Queue()
        self.low_priority_queue: queue.Queue = queue.Queue()
        self.queued_systems = set()
        self.priority_systems = set()
        self.recent_unregistered_cache: Dict[int, float] = {}
        self.last_request_time = 0.0
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def queue_system_check(self, system_address: int, system_name: str, force_recheck: bool = False, priority: bool = False):
        """Queue a system for EDSM registration and discovery verification.
        priority=True bypasses low-priority background queue and executes immediately."""
        if not system_address or not system_name:
            return

        # If priority requested, skip if already queued in high priority
        if priority:
            if system_address in self.priority_systems:
                return
        else:
            if system_address in self.queued_systems or system_address in self.priority_systems:
                return

        # Check in-memory cooldown for recent unregistered checks
        now = time.time()
        if not force_recheck and system_address in self.recent_unregistered_cache:
            if (now - self.recent_unregistered_cache[system_address]) < UNREGISTERED_RECHECK_COOLDOWN_SEC:
                return

        # Check if already cached in DB as REGISTERED
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT edsm_checked, edsm_registered, edsm_body_count FROM systems WHERE system_address = ?", (system_address,))
        row = c.fetchone()
        
        needs_body_completion = False
        if row and row["edsm_checked"] == 1 and row["edsm_registered"] == 1:
            if ENABLE_EDSM_BODY_COMPLETION and (row["edsm_body_count"] or 0) > 0:
                c.execute("SELECT COUNT(*) as cnt FROM bodies WHERE system_address = ?", (system_address,))
                b_row = c.fetchone()
                if b_row and b_row["cnt"] == 0:
                    needs_body_completion = True
        conn.close()

        # If already registered on EDSM (edsm_registered == 1), keep permanent cache
        # unless body completion is needed or force_recheck is specified
        if not force_recheck and row and row["edsm_checked"] == 1 and row["edsm_registered"] == 1:
            if not needs_body_completion:
                return

        if priority:
            self.priority_systems.add(system_address)
            self.high_priority_queue.put((system_address, system_name))
        else:
            self.queued_systems.add(system_address)
            self.low_priority_queue.put((system_address, system_name))

    def _worker_loop(self):
        """Background worker loop that processes queued systems with strict rate limiting.
        Always drains high_priority_queue before handling low_priority_queue."""
        while self.is_running:
            item = None
            is_priority = False
            try:
                item = self.high_priority_queue.get_nowait()
                is_priority = True
            except queue.Empty:
                try:
                    item = self.low_priority_queue.get(timeout=1.0)
                    is_priority = False
                except queue.Empty:
                    continue

            system_address, system_name = item
            try:
                self._throttle_delay()
                self._fetch_and_update_system(system_address, system_name)
            except Exception as e:
                print(f"[EDSM Service] Error checking {system_name} ({system_address}): {e}")
            finally:
                if is_priority:
                    self.priority_systems.discard(system_address)
                    self.high_priority_queue.task_done()
                else:
                    self.queued_systems.discard(system_address)
                    self.low_priority_queue.task_done()

    def _throttle_delay(self):
        """Enforces a strict minimum delay between external HTTP requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY_SEC:
            time.sleep(REQUEST_DELAY_SEC - elapsed)
        self.last_request_time = time.time()

    def fetch_and_update_system_sync(self, system_address: int, system_name: str) -> dict:
        """Synchronously fetch system and bodies from EDSM (honoring rate limits) and update DB."""
        self._throttle_delay()
        return self._fetch_and_update_system(system_address, system_name)

    def import_unvisited_system_by_name(self, system_name: str) -> dict:
        """
        Fetches an unvisited system by name directly from EDSM and inserts/updates it into
        the database with is_external = 1, visit_count = 0.
        Also fetches and completes all celestial bodies so the user can inspect it immediately.
        """
        clean_name = (system_name or "").strip()
        if not clean_name:
            return {"success": False, "error": "System name is empty"}

        self._throttle_delay()
        encoded_name = urllib.parse.quote(clean_name)
        sys_url = f"{EDSM_SYSTEM_API}?systemName={encoded_name}&showInformation=1&showCoordinates=1"

        req = urllib.request.Request(
            sys_url,
            headers={"User-Agent": "ED_Journal_Analyzer/v0.1.3 (External System Import)"}
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
        security = info.get("security")
        population = info.get("population") or 0

        # Fetch bodies from EDSM
        self._throttle_delay()
        bodies_url = f"{EDSM_BODIES_API}?systemName={encoded_name}"
        bodies_req = urllib.request.Request(
            bodies_url,
            headers={"User-Agent": "ED_Journal_Analyzer/v0.1.3 (External System Import)"}
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
                    system_security = COALESCE(?, system_security),
                    population = CASE WHEN ? > 0 THEN ? ELSE population END,
                    edsm_checked = 1,
                    edsm_registered = 1,
                    edsm_first_discoverer = ?,
                    edsm_submitted_at = ?,
                    edsm_body_count = ?
                WHERE system_address = ?
            """, (
                star_sys_name, pos_x, pos_y, pos_z, sol_dist, sol_dist,
                allegiance, government, economy, security, population, population,
                first_discoverer, submitted_at, body_count, system_address
            ))
        else:
            c.execute("""
                INSERT INTO systems (
                    system_address, star_system, star_pos_x, star_pos_y, star_pos_z, sol_distance_ly,
                    system_allegiance, system_government, system_economy, system_security, population,
                    first_visited, last_visited, visit_count, is_external,
                    edsm_checked, edsm_registered, edsm_first_discoverer, edsm_submitted_at, edsm_body_count
                ) VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    NULL, NULL, 0, 1,
                    1, 1, ?, ?, ?
                )
            """, (
                system_address, star_sys_name, pos_x, pos_y, pos_z, sol_dist,
                allegiance, government, economy, security, population,
                first_discoverer, submitted_at, body_count
            ))

        completed_count = 0
        if bodies_list:
            completed_count = self._import_and_complete_bodies(conn, system_address, star_sys_name, bodies_list)

        self._update_system_aggregated_stats(conn, system_address)

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

    def _fetch_and_update_system(self, system_address: int, system_name: str) -> dict:
        """Fetches system info and body discoveries from EDSM and updates the database."""
        encoded_name = urllib.parse.quote(system_name)
        sys_url = f"{EDSM_SYSTEM_API}?systemName={encoded_name}&showInformation=1&showCoordinates=1"

        req = urllib.request.Request(
            sys_url,
            headers={"User-Agent": "ED_Journal_Analyzer/v0.1.3 (EDSM Discovery Integration)"}
        )

        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                if resp.status != 200:
                    self._mark_checked_unregistered(system_address)
                    return {"registered": False, "status": "http_error", "code": resp.status}
                sys_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            self._mark_checked_unregistered(system_address)
            return {"registered": False, "status": "error", "error": str(e)}

        # An empty dictionary or missing name indicates system is not in EDSM
        if not sys_data or not isinstance(sys_data, dict) or not sys_data.get("name"):
            self._mark_checked_unregistered(system_address)
            return {"registered": False, "status": "not_found"}

        # System is registered on EDSM
        # Check bodies for first discoverer and complete celestial bodies
        self._throttle_delay()
        bodies_url = f"{EDSM_BODIES_API}?systemName={encoded_name}"
        bodies_req = urllib.request.Request(
            bodies_url,
            headers={"User-Agent": "ED_Journal_Analyzer/v0.1.3 (EDSM Discovery Integration)"}
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
                edsm_body_count = ?
            WHERE system_address = ?
        """, (first_discoverer, submitted_at, body_count, system_address))

        # Import or backfill missing bodies from EDSM
        completed_count = 0
        if bodies_list and ENABLE_EDSM_BODY_COMPLETION:
            completed_count = self._import_and_complete_bodies(conn, system_address, system_name, bodies_list)

        # Recalculate and update aggregated system statistics
        self._update_system_aggregated_stats(conn, system_address)

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

    def _import_and_complete_bodies(self, conn, system_address: int, star_system: str, bodies_list: list) -> int:
        """
        Completes missing celestial bodies from EDSM for known systems where player
        did not receive FSS Scan journal events. Respects and preserves any existing
        player-scanned records (AutoScan, Detailed, NavBeacon).
        Returns number of completed/imported bodies.
        """
        c = conn.cursor()
        completed_count = 0

        # Query existing bodies for this system
        c.execute("SELECT id, body_id, body_name, scan_type, scan_timestamp FROM bodies WHERE system_address = ?", (system_address,))
        existing_rows = c.fetchall()
        existing_by_name = {r["body_name"]: dict(r) for r in existing_rows}
        existing_by_id = {r["body_id"]: dict(r) for r in existing_rows if r["body_id"] is not None}

        for b in bodies_list:
            b_name = b.get("name")
            b_id = b.get("bodyId")
            if not b_name:
                continue

            disc = b.get("discovery") or {}
            discoverer = disc.get("commander")
            discovered_at = disc.get("date")

            existing = existing_by_name.get(b_name) or (existing_by_id.get(b_id) if b_id is not None else None)

            # If body already exists and was scanned by player, preserve local data and only update discoverer
            if existing and existing.get("scan_type") and existing.get("scan_type") != "EDSM_Known":
                if discoverer:
                    c.execute("""
                        UPDATE bodies SET
                            edsm_discovered_by = ?,
                            edsm_discovered_at = ?
                        WHERE id = ?
                    """, (discoverer, discovered_at, existing["id"]))
                continue

            # Determine whether this body is a star or planet
            b_type = (b.get("type") or "").strip()
            subtype = (b.get("subType") or "").strip()
            is_star = (b_type.lower() == "star") or ("star" in subtype.lower() and "gas giant" not in subtype.lower())

            dist_ls = b.get("distanceToArrival")
            semi_major_m = (b.get("semiMajorAxis") * 149597870700.0) if b.get("semiMajorAxis") is not None else None
            eccentricity = b.get("orbitalEccentricity")
            inclination = b.get("orbitalInclination")
            periapsis = b.get("argOfPeriapsis")
            orbital_period_s = (b.get("orbitalPeriod") * 86400.0) if b.get("orbitalPeriod") is not None else None
            rotation_period_s = (b.get("rotationalPeriod") * 86400.0) if b.get("rotationalPeriod") is not None else None
            axial_tilt = b.get("axialTilt")

            parents_json = json.dumps(b.get("parents")) if b.get("parents") else None
            rings_json = json.dumps(b.get("belts") or b.get("rings")) if (b.get("belts") or b.get("rings")) else None
            materials_json = json.dumps(b.get("materials")) if b.get("materials") else None

            if is_star:
                star_type = _extract_star_type(b)
                planet_class = None
                stellar_mass = b.get("solarMasses") or 1.0
                radius_m = (b.get("solarRadius") * 696340000.0) if b.get("solarRadius") else ((b.get("radius") * 1000.0) if b.get("radius") else None)
                surface_temp = b.get("surfaceTemperature")
                abs_mag = b.get("absoluteMagnitude")
                luminosity = b.get("spectralClass")
                mass_em = None
                gravity_g = None
                gravity_raw = None
                surface_pressure = None
                landable = 0
                volcanism = None
                atmosphere = None
                atmosphere_type = None
                terraforming = None
                calc_arg = {"star_type": star_type, "stellar_mass": stellar_mass}
            else:
                star_type = None
                luminosity = None
                stellar_mass = None
                abs_mag = None
                planet_class = subtype or "Icy body"
                radius_m = (b.get("radius") * 1000.0) if b.get("radius") is not None else None
                surface_temp = b.get("surfaceTemperature")
                mass_em = b.get("earthMasses")
                g_val = b.get("gravity")
                gravity_g = round(g_val, 4) if g_val is not None else None
                gravity_raw = (g_val * 9.80665) if g_val is not None else None
                p_val = b.get("surfacePressure")
                surface_pressure = (p_val * 101325.0) if p_val is not None else None
                landable = 1 if b.get("isLandable") else 0
                volcanism = b.get("volcanismType")
                atmosphere = b.get("atmosphereType")
                atmosphere_type = b.get("atmosphereType")
                terraforming = b.get("terraformingState")
                calc_arg = {
                    "planet_class": planet_class,
                    "mass_em": mass_em or 0.001,
                    "terraforming_state": terraforming
                }

            # Value calculation
            val_res = calculate_body_value(calc_arg)
            fss_val = val_res.get("fss_value", 0)
            dss_val = val_res.get("dss_value", 0)
            fd_fss = val_res.get("first_discovered_fss", 0)
            fm_dss = val_res.get("first_mapped_dss", 0)
            max_pot = val_res.get("max_potential_value", 0)

            # Anomaly & Exobiology detection
            anomaly_arg = {
                "body_name": b_name,
                "star_system": star_system,
                "star_type": star_type,
                "planet_class": planet_class,
                "distance_from_arrival_ls": dist_ls,
                "semi_major_axis": semi_major_m,
                "orbital_period": orbital_period_s,
                "rotation_period": rotation_period_s,
                "eccentricity": eccentricity,
                "orbital_inclination": inclination,
                "landable": landable,
                "surface_gravity_g": gravity_g,
                "rings": rings_json,
                "volcanism": volcanism,
                "terraforming_state": terraforming,
                "parents": parents_json
            }
            anomalies = detect_anomalies(anomaly_arg)
            anomalies_json = json.dumps(anomalies)

            # Exobiology predictions
            bio_preds = []
            if not is_star and (atmosphere or landable):
                bio_preds = predict_exobiology_candidates(anomaly_arg)
            bio_pred_json = json.dumps(bio_preds)

            if existing:
                # Update existing EDSM_Known record
                c.execute("""
                    UPDATE bodies SET
                        body_id = COALESCE(?, body_id),
                        body_name = ?,
                        star_system = ?,
                        distance_from_arrival_ls = ?,
                        star_type = ?,
                        luminosity = ?,
                        stellar_mass = ?,
                        absolute_magnitude = ?,
                        radius = ?,
                        surface_temperature = ?,
                        planet_class = ?,
                        atmosphere = ?,
                        atmosphere_type = ?,
                        mass_em = ?,
                        surface_gravity = ?,
                        surface_gravity_g = ?,
                        surface_pressure = ?,
                        landable = ?,
                        volcanism = ?,
                        terraforming_state = ?,
                        semi_major_axis = ?,
                        eccentricity = ?,
                        orbital_inclination = ?,
                        periapsis = ?,
                        orbital_period = ?,
                        rotation_period = ?,
                        axial_tilt = ?,
                        rings = ?,
                        materials = ?,
                        parents = ?,
                        was_discovered = 1,
                        was_mapped = CASE WHEN ? IS NOT NULL THEN 1 ELSE was_mapped END,
                        edsm_discovered_by = ?,
                        edsm_discovered_at = ?,
                        fss_value = ?,
                        dss_value = ?,
                        first_discovered_fss = ?,
                        first_mapped_dss = ?,
                        max_potential_value = ?,
                        anomalies_json = ?,
                        exobiology_predictions = ?
                    WHERE id = ?
                """, (
                    b_id, b_name, star_system, dist_ls,
                    star_type, luminosity, stellar_mass, abs_mag, radius_m, surface_temp,
                    planet_class, atmosphere, atmosphere_type,
                    mass_em, gravity_raw, gravity_g, surface_pressure, landable,
                    volcanism, terraforming, semi_major_m, eccentricity,
                    inclination, periapsis, orbital_period_s, rotation_period_s,
                    axial_tilt, rings_json, materials_json, parents_json,
                    discoverer, discoverer, discovered_at,
                    fss_val, dss_val, fd_fss, fm_dss, max_pot,
                    anomalies_json, bio_pred_json, existing["id"]
                ))
                completed_count += 1
            else:
                # Insert new EDSM_Known body
                c.execute("""
                    INSERT INTO bodies (
                        system_address, body_id, body_name, star_system,
                        distance_from_arrival_ls, star_type, luminosity, stellar_mass,
                        absolute_magnitude, radius, surface_temperature, planet_class,
                        atmosphere, atmosphere_type, mass_em, surface_gravity,
                        surface_gravity_g, surface_pressure, landable, volcanism,
                        terraforming_state, semi_major_axis, eccentricity,
                        orbital_inclination, periapsis, orbital_period, rotation_period,
                        axial_tilt, rings, materials, parents, was_discovered, was_mapped,
                        scan_type, edsm_discovered_by, edsm_discovered_at,
                        fss_value, dss_value, first_discovered_fss, first_mapped_dss,
                        max_potential_value, anomalies_json, exobiology_predictions
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, 1, ?,
                        'EDSM_Known', ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?
                    )
                """, (
                    system_address, b_id, b_name, star_system,
                    dist_ls, star_type, luminosity, stellar_mass,
                    abs_mag, radius_m, surface_temp, planet_class,
                    atmosphere, atmosphere_type, mass_em, gravity_raw,
                    gravity_g, surface_pressure, landable, volcanism,
                    terraforming, semi_major_m, eccentricity,
                    inclination, periapsis, orbital_period_s, rotation_period_s,
                    axial_tilt, rings_json, materials_json, parents_json,
                    1 if discoverer else 0,
                    discoverer, discovered_at,
                    fss_val, dss_val, fd_fss, fm_dss,
                    max_pot, anomalies_json, bio_pred_json
                ))
                completed_count += 1

        return completed_count

    def _update_system_aggregated_stats(self, conn, system_address: int):
        """Recalculates system-level exploration values and flags from celestial bodies."""
        c = conn.cursor()
        c.execute("""
            SELECT 
                COUNT(*) as count,
                MAX(star_system) as sys_name,
                (SELECT star_type FROM bodies WHERE system_address = ? AND star_type IS NOT NULL ORDER BY distance_from_arrival_ls ASC, body_id ASC LIMIT 1) as main_star,
                SUM(fss_value) as sum_fss,
                SUM(dss_value) as sum_dss,
                SUM(max_potential_value) as sum_max,
                SUM(bio_signals) as sum_bio,
                MAX(CASE WHEN LOWER(planet_class) LIKE '%earthlike%' OR LOWER(planet_class) LIKE '%earth-like%' THEN 1 ELSE 0 END) as elw,
                MAX(CASE WHEN LOWER(planet_class) LIKE '%water world%' THEN 1 ELSE 0 END) as ww,
                MAX(CASE WHEN LOWER(planet_class) LIKE '%ammonia%' THEN 1 ELSE 0 END) as ammonia,
                MAX(CASE WHEN LOWER(terraforming_state) LIKE '%terraform%' THEN 1 ELSE 0 END) as tf,
                MAX(CASE WHEN bio_signals > 0 THEN 1 ELSE 0 END) as bio,
                MAX(CASE WHEN landable = 1 THEN 1 ELSE 0 END) as landable,
                MAX(CASE WHEN landable = 1 AND surface_gravity_g >= 3.0 THEN 1 ELSE 0 END) as high_g,
                MAX(CASE WHEN anomalies_json != '[]' AND anomalies_json IS NOT NULL THEN 1 ELSE 0 END) as anomalies,
                ROUND(AVG(CASE WHEN landable = 1 AND radius IS NOT NULL AND radius > 0 THEN radius ELSE NULL END), 1) as avg_landable_radius
            FROM bodies 
            WHERE system_address = ? 
              AND (star_type IS NOT NULL OR planet_class IS NOT NULL)
        """, (system_address, system_address))
        row = c.fetchone()
        if not row or row["count"] == 0:
            return

        c.execute("""
            UPDATE systems SET
                scanned_bodies = ?,
                main_star_type = COALESCE(main_star_type, ?),
                total_fss_value = ?,
                total_dss_value = ?,
                total_potential_value = ?,
                total_bio_signals = ?,
                has_elw = ?,
                has_water_world = ?,
                has_ammonia = ?,
                has_terraformable = ?,
                has_bio = ?,
                has_landable = ?,
                has_high_g = ?,
                has_anomalies = ?,
                avg_landable_radius = ?
            WHERE system_address = ?
        """, (
            row["count"], row["main_star"], row["sum_fss"] or 0, row["sum_dss"] or 0,
            row["sum_max"] or 0, row["sum_bio"] or 0, row["elw"] or 0,
            row["ww"] or 0, row["ammonia"] or 0, row["tf"] or 0, row["bio"] or 0,
            row["landable"] or 0, row["high_g"] or 0, row["anomalies"] or 0,
            row["avg_landable_radius"] or 0,
            system_address
        ))

    def _mark_checked_unregistered(self, system_address: int):
        """Mark system as checked and unregistered on EDSM in SQLite."""
        self.recent_unregistered_cache[system_address] = time.time()
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""
            UPDATE systems SET
                edsm_checked = 1,
                edsm_registered = 0,
                edsm_first_discoverer = NULL,
                edsm_submitted_at = NULL
            WHERE system_address = ?
        """, (system_address,))
        conn.commit()
        conn.close()


# Singleton instance
edsm_service = EDSMService()

