import os
import re
import json
import glob
from pathlib import Path
from datetime import datetime

from app.db.database import get_db_connection, save_or_merge_mining_site
from app.parser.value_calculator import calculate_body_value
from app.parser.exobiology import predict_exobiology_candidates, get_species_value
from app.analyzer.anomaly_finder import detect_anomalies
from app.services.edsm_service import edsm_service
from app.live.rhino.note_integrator import update_body_note_in_db
from app.live.telemetry import telemetry_tracker

class JournalParser:
    def __init__(self, db_conn=None, event_callback=None, is_live: bool = False):
        self.conn = db_conn or get_db_connection()
        self.cursor = self.conn.cursor()
        self.dirty_systems = set()
        self.event_callback = event_callback
        self.is_live = is_live
        
        # State tracking for SRV and surface activities
        self.current_system_address = None
        self.current_star_system = None
        self.current_body_id = None
        self.current_body_name = None
        self.current_body_type = None
        self.in_srv = False
        self.srv_type = None
        self.current_latitude = None
        self.current_longitude = None

    def flush_dirty_systems(self):
        """Update system-level stats for all modified systems during parsing."""
        if not self.dirty_systems:
            return
        for sys_addr in self.dirty_systems:
            self._update_system_stats(sys_addr)
        self.dirty_systems.clear()
        self.conn.commit()

    def process_journal_line(self, line: str):
        if not line or not line.strip():
            return
        try:
            event_data = json.loads(line.strip())
        except Exception:
            return

        event = event_data.get("event")
        timestamp = event_data.get("timestamp", "")

        # Update context if present
        if event_data.get("SystemAddress"):
            self.current_system_address = event_data["SystemAddress"]
        if event_data.get("StarSystem"):
            self.current_star_system = event_data["StarSystem"]
        if "BodyID" in event_data:
            self.current_body_id = event_data["BodyID"]
        if event_data.get("BodyName"):
            self.current_body_name = event_data["BodyName"]
        elif event_data.get("Body") and isinstance(event_data.get("Body"), str):
            self.current_body_name = event_data["Body"]

        if "Latitude" in event_data and "Longitude" in event_data:
            self.current_latitude = event_data["Latitude"]
            self.current_longitude = event_data["Longitude"]
            if self.current_system_address and self.current_body_id is not None:
                self.cursor.execute("""
                    UPDATE surface_mining_activities
                    SET latitude = ?, longitude = ?
                    WHERE system_address = ? AND body_id = ? AND latitude IS NULL
                """, (self.current_latitude, self.current_longitude, self.current_system_address, self.current_body_id))
        elif "Latitude" in event_data:
            self.current_latitude = event_data["Latitude"]
        elif "Longitude" in event_data:
            self.current_longitude = event_data["Longitude"]

        if event == "StartJump":
            if self.event_callback:
                self.event_callback("StartJump", event_data)
        elif event in ["FSDJump", "Location", "CarrierJump"]:
            self._handle_jump_or_location(event_data, timestamp)
            if self.event_callback:
                self.event_callback(event, event_data)
        elif event == "FSSDiscoveryScan":
            self._handle_fss_discovery_scan(event_data)
            if self.event_callback:
                self.event_callback("FSSDiscoveryScan", event_data)
        elif event == "Scan":
            self._handle_scan(event_data, timestamp)
            self._update_last_targeted_body(event_data.get("SystemAddress"), event_data.get("BodyID"), event_data.get("BodyName"))
            if self.event_callback:
                self.event_callback("Scan", event_data)
        elif event in ["FSSBodySignals", "SAASignalsFound"]:
            self._handle_signals(event_data)
            self._update_last_targeted_body(event_data.get("SystemAddress"), event_data.get("BodyID"), event_data.get("BodyName"))
            if self.event_callback:
                self.event_callback(event, event_data)
        elif event == "SAAScanComplete":
            self._handle_saa_scan_complete(event_data)
            self._update_last_targeted_body(event_data.get("SystemAddress"), event_data.get("BodyID"), event_data.get("BodyName"))
            if self.event_callback:
                self.event_callback("SAAScanComplete", event_data)
        elif event == "ScanOrganic":
            self._handle_scan_organic(event_data, timestamp)
            self._update_last_targeted_body(event_data.get("SystemAddress"), event_data.get("Body") or event_data.get("BodyID"))
            if self.event_callback:
                self.event_callback("ScanOrganic", event_data)
        elif event == "CodexEntry":
            self._handle_codex_entry(event_data, timestamp)
            if self.event_callback:
                self.event_callback("CodexEntry", event_data)
        elif event in ["ApproachBody", "Touchdown"]:
            self._update_last_targeted_body(event_data.get("SystemAddress"), event_data.get("BodyID"), event_data.get("Body"))
        elif event == "LaunchSRV":
            self.in_srv = True
            self.srv_type = event_data.get("SRVType") or "srv"
            if self.event_callback:
                self.event_callback("LaunchSRV", event_data)
        elif event == "DockSRV":
            self.in_srv = False
            self.srv_type = None
            if self.event_callback:
                self.event_callback("DockSRV", event_data)
        elif event == "MaterialCollected":
            self._handle_material_collected(event_data, timestamp)
            if self.event_callback:
                self.event_callback("MaterialCollected", event_data)
        elif event == "MiningRefined":
            self._handle_mining_refined(event_data, timestamp)
            if self.event_callback:
                self.event_callback("MiningRefined", event_data)

    def _update_last_targeted_body(self, sys_addr: int, body_id=None, body_name=None):
        if not sys_addr:
            return
        if body_id is None and body_name:
            self.cursor.execute("SELECT body_id FROM bodies WHERE system_address = ? AND body_name = ?", (sys_addr, body_name))
            row = self.cursor.fetchone()
            if row:
                body_id = row["body_id"]

        if body_id is not None:
            self.cursor.execute("UPDATE systems SET last_targeted_body_id = ? WHERE system_address = ?", (body_id, sys_addr))
            self.dirty_systems.add(sys_addr)

    def _handle_jump_or_location(self, data: dict, timestamp: str):
        sys_addr = data.get("SystemAddress")
        star_sys = data.get("StarSystem")
        if not sys_addr or not star_sys:
            return

        if data.get("event") in ["FSDJump", "CarrierJump"]:
            self.current_latitude = None
            self.current_longitude = None
            self.in_srv = False
            self.srv_type = None
            self.current_body_id = None
            self.current_body_name = None

        star_pos = data.get("StarPos", [0, 0, 0])
        pos_x, pos_y, pos_z = (star_pos[0], star_pos[1], star_pos[2]) if len(star_pos) >= 3 else (0, 0, 0)
        sol_dist = round((pos_x**2 + pos_y**2 + pos_z**2)**0.5, 1) if (pos_x is not None and pos_y is not None and pos_z is not None) else 0

        star_class = data.get("StarClass") or data.get("StarType")
        allegiance = data.get("SystemAllegiance")
        economy = data.get("SystemEconomy_Localised") or data.get("SystemEconomy")
        if economy and economy.startswith("$economy_"):
            economy = economy.replace("$economy_", "").rstrip(";").capitalize()
        govt = data.get("SystemGovernment_Localised") or data.get("SystemGovernment")
        sec = data.get("SystemSecurity_Localised") or data.get("SystemSecurity")
        pop = data.get("Population", 0)

        # SystemFaction & State
        sys_faction_obj = data.get("SystemFaction")
        controlling_faction = None
        system_state = None
        if isinstance(sys_faction_obj, dict):
            controlling_faction = sys_faction_obj.get("Name")
            system_state = sys_faction_obj.get("FactionState")
        elif isinstance(sys_faction_obj, str):
            controlling_faction = sys_faction_obj
            system_state = data.get("FactionState")
        if not system_state:
            system_state = data.get("FactionState")

        sec_economy = data.get("SystemSecondEconomy_Localised") or data.get("SystemSecondEconomy")
        if sec_economy and sec_economy.startswith("$economy_"):
            sec_economy = sec_economy.replace("$economy_", "").rstrip(";").capitalize()

        reserve_lvl = data.get("SystemReserve_Localised") or data.get("SystemReserve")
        if reserve_lvl and reserve_lvl.startswith("$reserve_"):
            reserve_lvl = reserve_lvl.replace("$reserve_", "").rstrip(";").capitalize()

        # Check existing system
        self.cursor.execute("SELECT first_visited, visit_count FROM systems WHERE system_address = ?", (sys_addr,))
        row = self.cursor.fetchone()

        if row:
            first_visited = row["first_visited"] or timestamp
            visit_count = (row["visit_count"] or 1) + (1 if data.get("event") == "FSDJump" else 0)
            self.cursor.execute("""
                UPDATE systems SET
                    star_system = COALESCE(?, star_system),
                    star_pos_x = COALESCE(?, star_pos_x),
                    star_pos_y = COALESCE(?, star_pos_y),
                    star_pos_z = COALESCE(?, star_pos_z),
                    sol_distance_ly = CASE WHEN ? > 0 THEN ? ELSE sol_distance_ly END,
                    main_star_type = COALESCE(?, main_star_type),
                    population = CASE WHEN ? > 0 THEN ? ELSE population END,
                    system_allegiance = COALESCE(?, system_allegiance),
                    system_economy = COALESCE(?, system_economy),
                    system_second_economy = COALESCE(?, system_second_economy),
                    system_government = COALESCE(?, system_government),
                    system_security = COALESCE(?, system_security),
                    system_state = COALESCE(NULLIF(?, ''), system_state),
                    controlling_faction = COALESCE(NULLIF(?, ''), controlling_faction),
                    system_reserve = COALESCE(NULLIF(?, ''), system_reserve),
                    last_visited = ?,
                    visit_count = visit_count + 1
                WHERE system_address = ?
            """, (
                star_sys, pos_x, pos_y, pos_z, sol_dist, sol_dist, star_class,
                pop, pop, allegiance, economy, sec_economy, govt, sec,
                system_state, controlling_faction, reserve_lvl,
                timestamp, sys_addr
            ))
        else:
            self.cursor.execute("""
                INSERT INTO systems (
                    system_address, star_system, star_pos_x, star_pos_y, star_pos_z, sol_distance_ly,
                    main_star_type, system_allegiance, system_economy, system_second_economy,
                    system_government, system_security, system_state, controlling_faction, system_reserve,
                    population, first_visited, last_visited, visit_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sys_addr, star_sys, pos_x, pos_y, pos_z, sol_dist,
                star_class, allegiance, economy, sec_economy,
                govt, sec, system_state or "", controlling_faction or "", reserve_lvl or "",
                pop, timestamp, timestamp, 1
            ))

        # Record visit timeline if FSDJump
        if data.get("event") == "FSDJump":
            jump_dist = data.get("JumpDist", 0)
            fuel = data.get("FuelUsed", 0)
            taxi = 1 if data.get("Taxi", False) else 0
            self.cursor.execute("""
                INSERT INTO visits (system_address, star_system, timestamp, star_pos_x, star_pos_y, star_pos_z, jump_dist, fuel_used, is_taxi)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sys_addr, star_sys, timestamp, pos_x, pos_y, pos_z, jump_dist, fuel, taxi))

        # Queue background EDSM discovery verification
        if sys_addr and star_sys:
            try:
                if self.is_live:
                    edsm_service.queue_system_check(sys_addr, star_sys, priority=True)
            except Exception:
                pass

    def _handle_fss_discovery_scan(self, data: dict):
        sys_addr = data.get("SystemAddress")
        body_count = data.get("BodyCount", 0)
        star_sys = data.get("SystemName") or self.current_star_system
        if sys_addr:
            self.cursor.execute("""
                UPDATE systems SET total_bodies = MAX(total_bodies, ?) WHERE system_address = ?
            """, (body_count, sys_addr))
            if star_sys:
                try:
                    if self.is_live:
                        edsm_service.queue_system_check(sys_addr, star_sys, priority=True)
                except Exception:
                    pass

    def _handle_scan(self, data: dict, timestamp: str):
        sys_addr = data.get("SystemAddress")
        body_id = data.get("BodyID")
        body_name = data.get("BodyName")
        star_sys = data.get("StarSystem")

        if sys_addr is None or body_id is None or not body_name:
            return

        # Skip Barycentres, Belt Clusters, and Rings that are not actual stars or planets
        scan_type = data.get("ScanType", "")
        if scan_type == "Barycentre" or "barycentre" in body_name.lower():
            return
        if "belt cluster" in body_name.lower() or " ring" in body_name.lower():
            return

        star_type = data.get("StarType")
        luminosity = data.get("Luminosity")
        stellar_mass = data.get("StellarMass")
        planet_class = data.get("PlanetClass")
        if not star_type and not planet_class:
            return
        dist_ls = data.get("DistanceFromArrivalLS", 0.0)
        radius = data.get("Radius")
        surface_temp = data.get("SurfaceTemperature")
        mass_em = data.get("MassEM")

        gravity_raw = data.get("SurfaceGravity")
        # SurfaceGravity in journal is m/s^2. G value = gravity / 9.80665
        gravity_g = round(gravity_raw / 9.80665, 4) if gravity_raw is not None else None

        surface_pressure = data.get("SurfacePressure")
        landable = 1 if data.get("Landable", False) else 0
        volcanism = data.get("Volcanism", "")
        terraforming = data.get("TerraformState", "")
        tidal_lock = 1 if data.get("TidalLock", False) else 0

        semi_major_axis = data.get("SemiMajorAxis")
        eccentricity = data.get("Eccentricity")
        inclination = data.get("OrbitalInclination")
        periapsis = data.get("Periapsis")
        orbital_period = data.get("OrbitalPeriod")
        ascending_node = data.get("AscendingNode")
        mean_anomaly = data.get("MeanAnomaly")
        rotation_period = data.get("RotationPeriod")
        axial_tilt = data.get("AxialTilt")

        atmosphere = data.get("Atmosphere", "")
        atmosphere_type = data.get("AtmosphereType", "")
        atmosphere_comp = json.dumps(data.get("AtmosphereComposition", [])) if data.get("AtmosphereComposition") else None
        rings = json.dumps(data.get("Rings", [])) if data.get("Rings") else None
        materials = json.dumps(data.get("Materials", [])) if data.get("Materials") else None
        parents = json.dumps(data.get("Parents", [])) if data.get("Parents") else None

        scan_type = data.get("ScanType", "")
        was_discovered = 1 if data.get("WasDiscovered", False) else 0
        was_mapped = 1 if data.get("WasMapped", False) else 0

        # Check if system is known to be populated
        is_populated = False
        self.cursor.execute("SELECT population FROM systems WHERE system_address = ?", (sys_addr,))
        pop_row = self.cursor.fetchone()
        if pop_row and pop_row["population"] and pop_row["population"] > 0:
            is_populated = True

        # NavBeacon scans, already mapped bodies, or populated systems cannot be first discoveries
        if scan_type in ["NavBeacon", "NavBeaconDetail"] or was_mapped == 1 or is_populated:
            was_discovered = 1

        reserve_level = data.get("ReserveLevel")

        # Calculate values
        body_dict = {
            "system_address": sys_addr,
            "body_id": body_id,
            "body_name": body_name,
            "star_system": star_sys,
            "distance_from_arrival_ls": dist_ls,
            "semi_major_axis": semi_major_axis,
            "parents": parents,
            "star_type": star_type,
            "luminosity": luminosity,
            "stellar_mass": stellar_mass,
            "planet_class": planet_class,
            "mass_em": mass_em,
            "terraforming_state": terraforming,
            "landable": landable,
            "surface_temperature": surface_temp,
            "surface_gravity": gravity_raw,
            "surface_gravity_g": gravity_g,
            "surface_pressure": surface_pressure,
            "atmosphere": atmosphere,
            "atmosphere_type": atmosphere_type,
            "atmosphere_composition": atmosphere_comp,
            "materials": materials,
            "volcanism": volcanism,
            "eccentricity": eccentricity,
            "orbital_period": orbital_period,
            "rotation_period": rotation_period,
            "orbital_inclination": inclination,
            "rings": rings,
            "reserve_level": reserve_level,
            "bio_signals": 0
        }

        # Check if already had bio_signals / geo_signals / mining_signals / confirmed_genuses in existing body record
        self.cursor.execute("SELECT bio_signals, geo_signals, mining_signals, is_mapped_by_user, confirmed_genuses FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
        existing_b = self.cursor.fetchone()
        existing_bio = existing_b["bio_signals"] if existing_b else 0
        existing_geo = existing_b["geo_signals"] if existing_b else 0
        existing_mining = existing_b["mining_signals"] if (existing_b and "mining_signals" in existing_b.keys()) else 0
        existing_mapped = existing_b["is_mapped_by_user"] if existing_b else 0
        existing_genuses = existing_b["confirmed_genuses"] if existing_b else None
        body_dict["bio_signals"] = existing_bio
        body_dict["mining_signals"] = existing_mining
        if existing_genuses:
            body_dict["confirmed_genuses"] = existing_genuses

        values = calculate_body_value(body_dict)
        fss_val = values.get("fss_value", 0)
        dss_val = values.get("dss_value", 0)
        fd_fss = values.get("first_discovered_fss", 0)
        fm_dss = values.get("first_mapped_dss", 0)
        max_pot = values.get("max_potential_value", 0)

        # Predict Exobiology candidates and preserve locked/confirmed organics
        bio_predictions = predict_exobiology_candidates(body_dict)
        self._lock_confirmed_organics_into_predictions(sys_addr, body_id, bio_predictions)
        bio_pred_json = json.dumps(bio_predictions)

        # Detect Anomalies
        anomalies = detect_anomalies(body_dict)
        anomalies_json = json.dumps(anomalies)

        self.cursor.execute("""
            INSERT INTO bodies (
                system_address, body_id, body_name, star_system, distance_from_arrival_ls,
                star_type, luminosity, stellar_mass, absolute_magnitude, radius, surface_temperature,
                planet_class, atmosphere, atmosphere_type, atmosphere_composition,
                mass_em, surface_gravity, surface_gravity_g, surface_pressure, landable,
                volcanism, terraforming_state, tidal_lock, semi_major_axis, eccentricity,
                orbital_inclination, periapsis, orbital_period, ascending_node, mean_anomaly,
                rotation_period, axial_tilt, rings, materials, parents, was_discovered, was_mapped,
                is_mapped_by_user, bio_signals, geo_signals, mining_signals, reserve_level, fss_value, dss_value,
                first_discovered_fss, first_mapped_dss, max_potential_value,
                confirmed_genuses, exobiology_predictions, anomalies_json, scan_type, scan_timestamp, updated_timestamp
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(system_address, body_id) DO UPDATE SET
                body_name = excluded.body_name,
                star_system = COALESCE(excluded.star_system, bodies.star_system),
                distance_from_arrival_ls = excluded.distance_from_arrival_ls,
                star_type = COALESCE(excluded.star_type, bodies.star_type),
                luminosity = COALESCE(excluded.luminosity, bodies.luminosity),
                stellar_mass = COALESCE(excluded.stellar_mass, bodies.stellar_mass),
                radius = COALESCE(excluded.radius, bodies.radius),
                surface_temperature = COALESCE(excluded.surface_temperature, bodies.surface_temperature),
                planet_class = COALESCE(excluded.planet_class, bodies.planet_class),
                atmosphere = COALESCE(excluded.atmosphere, bodies.atmosphere),
                atmosphere_type = COALESCE(excluded.atmosphere_type, bodies.atmosphere_type),
                atmosphere_composition = COALESCE(excluded.atmosphere_composition, bodies.atmosphere_composition),
                mass_em = COALESCE(excluded.mass_em, bodies.mass_em),
                surface_gravity = COALESCE(excluded.surface_gravity, bodies.surface_gravity),
                surface_gravity_g = COALESCE(excluded.surface_gravity_g, bodies.surface_gravity_g),
                surface_pressure = COALESCE(excluded.surface_pressure, bodies.surface_pressure),
                landable = excluded.landable,
                volcanism = COALESCE(excluded.volcanism, bodies.volcanism),
                terraforming_state = COALESCE(excluded.terraforming_state, bodies.terraforming_state),
                tidal_lock = excluded.tidal_lock,
                semi_major_axis = COALESCE(excluded.semi_major_axis, bodies.semi_major_axis),
                eccentricity = COALESCE(excluded.eccentricity, bodies.eccentricity),
                orbital_inclination = COALESCE(excluded.orbital_inclination, bodies.orbital_inclination),
                orbital_period = COALESCE(excluded.orbital_period, bodies.orbital_period),
                rotation_period = COALESCE(excluded.rotation_period, bodies.rotation_period),
                rings = COALESCE(excluded.rings, bodies.rings),
                materials = COALESCE(excluded.materials, bodies.materials),
                parents = COALESCE(excluded.parents, bodies.parents),
                was_discovered = CASE WHEN bodies.was_discovered = 1 OR excluded.was_discovered = 1 THEN 1 ELSE 0 END,
                was_mapped = CASE WHEN bodies.was_mapped = 1 OR excluded.was_mapped = 1 THEN 1 ELSE 0 END,
                scan_type = COALESCE(excluded.scan_type, bodies.scan_type),
                reserve_level = COALESCE(excluded.reserve_level, bodies.reserve_level),
                fss_value = excluded.fss_value,
                dss_value = excluded.dss_value,
                first_discovered_fss = excluded.first_discovered_fss,
                first_mapped_dss = excluded.first_mapped_dss,
                max_potential_value = excluded.max_potential_value,
                exobiology_predictions = excluded.exobiology_predictions,
                anomalies_json = excluded.anomalies_json,
                updated_timestamp = excluded.updated_timestamp
        """, (
            sys_addr, body_id, body_name, star_sys, dist_ls,
            star_type, luminosity, stellar_mass, data.get("AbsoluteMagnitude"), radius, surface_temp,
            planet_class, atmosphere, atmosphere_type, atmosphere_comp,
            mass_em, gravity_raw, gravity_g, surface_pressure, landable,
            volcanism, terraforming, tidal_lock, semi_major_axis, eccentricity,
            inclination, periapsis, orbital_period, ascending_node, mean_anomaly,
            rotation_period, axial_tilt, rings, materials, parents, was_discovered, was_mapped,
            existing_mapped, existing_bio, existing_geo, existing_mining, reserve_level, fss_val, dss_val,
            fd_fss, fm_dss, max_pot,
            existing_genuses, bio_pred_json, anomalies_json, scan_type, timestamp, timestamp
        ))

        self.dirty_systems.add(sys_addr)

        # Backfill body_type for any prior mining activity recorded before Scan arrived
        if planet_class:
            b_type = self._get_body_type_category(sys_addr, body_id, body_name)
            self.cursor.execute("""
                UPDATE surface_mining_activities 
                SET body_type = ? 
                WHERE system_address = ? 
                  AND (body_id = ? OR body_name = ?)
                  AND (body_type IS NULL OR body_type = 'Unknown')
            """, (b_type, sys_addr, body_id, body_name))

    def _handle_signals(self, data: dict):
        sys_addr = data.get("SystemAddress")
        body_id = data.get("BodyID")
        body_name = data.get("BodyName")
        signals = data.get("Signals", [])
        event_name = data.get("event", "")

        if sys_addr is None:
            return

        bio_count = 0
        geo_count = 0
        mining_count = 0
        for s in signals:
            stype = s.get("Type", "")
            scount = s.get("Count", 0)
            if "$SAA_SignalType_Biological" in stype or "biological" in stype.lower() or "bio" in stype.lower():
                bio_count += scount
            elif "$SAA_SignalType_Geological" in stype or "geological" in stype.lower() or "geo" in stype.lower():
                geo_count += scount
            elif "$PlanetaryMiningLocation" in stype or "mining" in stype.lower():
                mining_count += scount

        # Extract confirmed Genuses from SAASignalsFound if present
        confirmed_genuses_list = []
        if "Genuses" in data and isinstance(data["Genuses"], list):
            for g in data["Genuses"]:
                g_name = g.get("Genus_Localised") or g.get("Genus") or ""
                if g_name:
                    clean_g = re.sub(r"^\$Codex_Ent_|_Genus_Name;?$", "", g_name, flags=re.IGNORECASE).strip()
                    if clean_g:
                        confirmed_genuses_list.append(clean_g)
        
        confirmed_genuses_json = json.dumps(confirmed_genuses_list) if confirmed_genuses_list else None
        is_saa_signals = (event_name == "SAASignalsFound")

        # Check if body exists
        if body_id is not None:
            self.cursor.execute("SELECT * FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
        elif body_name:
            self.cursor.execute("SELECT * FROM bodies WHERE system_address = ? AND body_name = ?", (sys_addr, body_name))
        else:
            return

        existing = self.cursor.fetchone()
        if existing:
            b_dict = dict(existing)
            b_dict["bio_signals"] = bio_count
            b_dict["geo_signals"] = geo_count
            b_dict["mining_signals"] = mining_count
            if is_saa_signals:
                b_dict["is_mapped_by_user"] = 1

            if confirmed_genuses_list:
                b_dict["confirmed_genuses"] = confirmed_genuses_list
            elif existing["confirmed_genuses"]:
                b_dict["confirmed_genuses"] = existing["confirmed_genuses"]
            
            bio_predictions = predict_exobiology_candidates(b_dict)
            self._lock_confirmed_organics_into_predictions(sys_addr, body_id or existing["body_id"], bio_predictions)
            bio_pred_json = json.dumps(bio_predictions)
            anomalies = detect_anomalies(b_dict)
            anomalies_json = json.dumps(anomalies)

            mapped_val = 1 if is_saa_signals else existing["is_mapped_by_user"]
            self.cursor.execute("""
                UPDATE bodies SET
                    bio_signals = ?,
                    geo_signals = ?,
                    mining_signals = ?,
                    is_mapped_by_user = ?,
                    confirmed_genuses = COALESCE(?, confirmed_genuses),
                    exobiology_predictions = ?,
                    anomalies_json = ?
                WHERE id = ?
            """, (bio_count, geo_count, mining_count, mapped_val, confirmed_genuses_json, bio_pred_json, anomalies_json, existing["id"]))
        else:
            # Insert stub body record if Scan hasn't occurred yet
            b_dict = {
                "system_address": sys_addr,
                "body_id": body_id or 0,
                "body_name": body_name or f"Body {body_id}",
                "bio_signals": bio_count,
                "geo_signals": geo_count,
                "mining_signals": mining_count,
                "is_mapped_by_user": 1 if is_saa_signals else 0,
                "confirmed_genuses": confirmed_genuses_list if confirmed_genuses_list else None
            }
            bio_predictions = predict_exobiology_candidates(b_dict)
            self._lock_confirmed_organics_into_predictions(sys_addr, body_id or 0, bio_predictions)
            bio_pred_json = json.dumps(bio_predictions)
            anomalies = detect_anomalies(b_dict)
            anomalies_json = json.dumps(anomalies)

            self.cursor.execute("""
                INSERT INTO bodies (
                    system_address, body_id, body_name, bio_signals, geo_signals, mining_signals,
                    is_mapped_by_user, confirmed_genuses, exobiology_predictions, anomalies_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address, body_id) DO UPDATE SET
                    bio_signals = excluded.bio_signals,
                    geo_signals = excluded.geo_signals,
                    mining_signals = excluded.mining_signals,
                    is_mapped_by_user = CASE WHEN excluded.is_mapped_by_user = 1 THEN 1 ELSE bodies.is_mapped_by_user END,
                    confirmed_genuses = COALESCE(excluded.confirmed_genuses, bodies.confirmed_genuses),
                    exobiology_predictions = excluded.exobiology_predictions,
                    anomalies_json = excluded.anomalies_json
            """, (sys_addr, body_id or 0, body_name or f"Body {body_id}", bio_count, geo_count, mining_count, 1 if is_saa_signals else 0, confirmed_genuses_json, bio_pred_json, anomalies_json))

        self.dirty_systems.add(sys_addr)

    def _lock_confirmed_organics_into_predictions(self, sys_addr: int, body_id: int, predictions: list):
        """Promote scanned organics to confirmed and lock them in the predictions list."""
        if not sys_addr or body_id is None:
            return
        self.cursor.execute("""
            SELECT species_localised, species, genus_localised, genus, scan_type
            FROM scanned_organics
            WHERE system_address = ? AND body_id = ?
        """, (sys_addr, body_id))
        rows = self.cursor.fetchall()
        if not rows:
            return

        for row in rows:
            sp_name = row["species_localised"] or row["species"] or ""
            stype = (row["scan_type"] or "").lower()
            stage_num = 3 if stype in ["analyse", "analyze"] else (2 if stype == "sample" else 1)

            # Check if species matches any prediction
            matched = False
            for p in predictions:
                if sp_name.lower() in p["species"].lower() or p["species"].lower() in sp_name.lower():
                    p["confidence"] = "confirmed"
                    p["status"] = "Confirmed"
                    p["stage_level"] = stage_num
                    p["locked"] = True
                    matched = True
                    break

            # If not in predictions (rare edge case), append as confirmed
            if not matched and sp_name:
                val_info = get_species_value(sp_name, row["genus_localised"] or row["genus"])
                base_v = val_info.get("base_value", 1000000)
                predictions.insert(0, {
                    "species": sp_name,
                    "genus": row["genus_localised"] or row["genus"] or sp_name.split()[0],
                    "species_variant": sp_name,
                    "variant_color": "",
                    "base_value": base_v,
                    "first_discovery_value": base_v * 5,
                    "colony_distance_m": val_info.get("colony_distance_m", 500),
                    "fit_score": 1.0,
                    "confidence": "confirmed",
                    "status": "Confirmed",
                    "stage_level": stage_num,
                    "locked": True
                })

    def _handle_saa_scan_complete(self, data: dict):
        sys_addr = data.get("SystemAddress")
        body_id = data.get("BodyID")
        body_name = data.get("BodyName")

        if sys_addr is not None:
            if body_id is not None:
                self.cursor.execute("""
                    UPDATE bodies SET is_mapped_by_user = 1 WHERE system_address = ? AND body_id = ?
                """, (sys_addr, body_id))
                self.dirty_systems.add(sys_addr)
            elif body_name:
                self.cursor.execute("""
                    UPDATE bodies SET is_mapped_by_user = 1 WHERE system_address = ? AND body_name = ?
                """, (sys_addr, body_name))
                self.dirty_systems.add(sys_addr)

    def _handle_scan_organic(self, data: dict, timestamp: str):
        sys_addr = data.get("SystemAddress")
        body_id = data.get("Body") if data.get("Body") is not None else data.get("BodyID")
        scan_type = data.get("ScanType", "")
        genus = data.get("Genus", "")
        genus_loc = data.get("Genus_Localised", "")
        species = data.get("Species", "")
        species_loc = data.get("Species_Localised", "")
        variant = data.get("Variant", "")
        variant_loc = data.get("Variant_Localised", "")

        val_info = get_species_value(species_loc or species, genus_loc or genus)
        base_val = val_info.get("base_value", 0)
        fd_val = val_info.get("first_discovery_value", 0)

        body_name = None
        if sys_addr is not None and body_id is not None:
            self.cursor.execute("SELECT body_name FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
            b_row = self.cursor.fetchone()
            if b_row:
                body_name = b_row["body_name"]

        if sys_addr is not None:
            self.cursor.execute("""
                INSERT INTO scanned_organics (
                    system_address, body_id, body_name, timestamp, scan_type, genus, genus_localised,
                    species, species_localised, variant, variant_localised, base_value, first_discovery_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sys_addr, body_id, body_name, timestamp, scan_type, genus, genus_loc,
                species, species_loc, variant, variant_loc, base_val, fd_val
            ))

            # Re-lock predictions on existing body if present
            if body_id is not None:
                self.cursor.execute("SELECT id, exobiology_predictions FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
                body_row = self.cursor.fetchone()
                if body_row and body_row["exobiology_predictions"]:
                    try:
                        preds = json.loads(body_row["exobiology_predictions"])
                        self._lock_confirmed_organics_into_predictions(sys_addr, body_id, preds)
                        self.cursor.execute("UPDATE bodies SET exobiology_predictions = ? WHERE id = ?", (json.dumps(preds), body_row["id"]))
                    except Exception:
                        pass

            self.dirty_systems.add(sys_addr)

    def _handle_codex_entry(self, data: dict, timestamp: str):
        cat = data.get("Category", "")
        cat_loc = (data.get("Category_Localised") or "").lower()
        subcat = data.get("SubCategory", "")
        
        # Check if biological
        is_bio = ("biology" in cat.lower() or "biology" in cat_loc or "organic" in subcat.lower())
        if not is_bio:
            return

        sys_addr = data.get("SystemAddress")
        body_id = data.get("BodyID") if data.get("BodyID") is not None else data.get("Body")
        entry_name_loc = data.get("Name_Localised") or data.get("Name", "")
        
        # Extract species/genus
        val_info = get_species_value(entry_name_loc)
        species_loc = val_info.get("species", entry_name_loc)
        genus_loc = val_info.get("genus", "")
        base_val = val_info.get("base_value", 0)
        fd_val = val_info.get("first_discovery_value", 0)

        # Lookup body_name from bodies table if available
        body_name = None
        if sys_addr is not None and body_id is not None:
            self.cursor.execute("SELECT body_name FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
            b_row = self.cursor.fetchone()
            if b_row:
                body_name = b_row["body_name"]

        if sys_addr is not None:
            # Check if this species on this body is already recorded
            self.cursor.execute("""
                SELECT COUNT(*) FROM scanned_organics 
                WHERE system_address = ? AND body_id = ? AND species_localised = ?
            """, (sys_addr, body_id, species_loc))
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute("""
                    INSERT INTO scanned_organics (
                        system_address, body_id, body_name, timestamp, scan_type, genus, genus_localised,
                        species, species_localised, variant, variant_localised, base_value, first_discovery_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sys_addr, body_id, body_name, timestamp, "Log", "", genus_loc,
                    "", species_loc, "", entry_name_loc, base_val, fd_val
                ))
                self.dirty_systems.add(sys_addr)

    def _get_body_type_category(self, sys_addr: int, body_id=None, body_name=None) -> str:
        """Classifies body into one of: 'HMC', 'Metal Rich', 'Rocky', 'Icy', 'Icy Rocky', or fallback."""
        if not sys_addr:
            return "Unknown"
        p_class = None
        if body_id is not None:
            self.cursor.execute("SELECT planet_class FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
            row = self.cursor.fetchone()
            if row and row["planet_class"]:
                p_class = row["planet_class"]
        if not p_class and body_name:
            self.cursor.execute("SELECT planet_class FROM bodies WHERE system_address = ? AND body_name = ?", (sys_addr, body_name))
            row = self.cursor.fetchone()
            if row and row["planet_class"]:
                p_class = row["planet_class"]

        if not p_class:
            return "Unknown"

        p_lower = p_class.lower()
        if "high metal" in p_lower:
            return "HMC"
        elif "metal rich" in p_lower:
            return "Metal Rich"
        elif "rocky ice" in p_lower or "icy rocky" in p_lower:
            return "Icy Rocky"
        elif "rocky" in p_lower:
            return "Rocky"
        elif "icy" in p_lower:
            return "Icy"
        return p_class

    def _handle_material_collected(self, data: dict, timestamp: str):
        # Record surface raw material extraction
        cat = data.get("Category", "Raw")
        name = data.get("Name", "")
        name_loc = data.get("Name_Localised") or name
        count = data.get("Count", 1)

        sys_addr = self.current_system_address
        star_sys = self.current_star_system
        body_id = self.current_body_id
        body_name = self.current_body_name
        srv_type = self.srv_type or ("mev_rhino" if self.in_srv else None)

        # Classify body_type (Icy, Rocky, Icy Rocky, HMC, Metal Rich)
        body_type = self._get_body_type_category(sys_addr, body_id, body_name)

        # If in SRV and live, query live Status.json for latest surface coordinates
        if self.in_srv and self.is_live:
            lat, lon = telemetry_tracker.get_coordinates()
            if lat is not None and lon is not None:
                self.current_latitude = lat
                self.current_longitude = lon

        if sys_addr and name:
            self.cursor.execute("""
                INSERT INTO surface_mining_activities (
                    system_address, star_system, body_id, body_name, body_type,
                    srv_type, material_name, material_name_localised, category,
                    count, latitude, longitude, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sys_addr, star_sys, body_id, body_name, body_type,
                srv_type, name, name_loc, cat,
                count, self.current_latitude, self.current_longitude, timestamp
            ))
            self.dirty_systems.add(sys_addr)

            # Record into dedicated surface_mining_sites table (with top 2 digits / ~0.2 deg grouping)
            if self.in_srv and self.current_latitude is not None and self.current_longitude is not None:
                try:
                    save_or_merge_mining_site(
                        conn=self.conn,
                        system_address=sys_addr,
                        star_system=star_sys or "Unknown",
                        body_id=body_id,
                        body_name=body_name or (f"Body {body_id}" if body_id is not None else "Surface"),
                        latitude=self.current_latitude,
                        longitude=self.current_longitude,
                        material_name=name_loc or name,
                        timestamp=timestamp
                    )
                except Exception as e:
                    print(f"[Mining Site Save Warning] {e}")

    def _handle_mining_refined(self, data: dict, timestamp: str):
        # Only track surface/SRV mining refined commodities
        if not self.in_srv:
            return

        raw_type = data.get("Type", "")
        clean_type = raw_type.replace("$", "").replace("_name;", "").replace(";", "").strip()
        type_loc = data.get("Type_Localised") or clean_type

        # If in SRV and live, query live Status.json for latest surface coordinates
        if self.is_live:
            lat, lon = telemetry_tracker.get_coordinates()
            if lat is not None and lon is not None:
                self.current_latitude = lat
                self.current_longitude = lon

        sys_addr = self.current_system_address
        star_sys = self.current_star_system
        body_id = self.current_body_id
        body_name = self.current_body_name
        srv_type = self.srv_type or "mev_rhino"

        body_type = self._get_body_type_category(sys_addr, body_id, body_name)

        if sys_addr and clean_type:
            self.cursor.execute("""
                INSERT INTO surface_mining_activities (
                    system_address, star_system, body_id, body_name, body_type,
                    srv_type, material_name, material_name_localised, category,
                    count, latitude, longitude, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sys_addr, star_sys, body_id, body_name, body_type,
                srv_type, clean_type, type_loc, "Refined",
                1, self.current_latitude, self.current_longitude, timestamp
            ))
            self.dirty_systems.add(sys_addr)

            # Record into dedicated surface_mining_sites table (with top 2 digits / ~0.2 deg grouping)
            if self.current_latitude is not None and self.current_longitude is not None:
                try:
                    save_or_merge_mining_site(
                        conn=self.conn,
                        system_address=sys_addr,
                        star_system=star_sys or "Unknown",
                        body_id=body_id,
                        body_name=body_name or (f"Body {body_id}" if body_id is not None else "Surface"),
                        latitude=self.current_latitude,
                        longitude=self.current_longitude,
                        material_name=type_loc or clean_type,
                        timestamp=timestamp
                    )
                except Exception as e:
                    print(f"[Mining Site Save Warning] {e}")

    def _update_system_stats(self, sys_addr: int):
        self.cursor.execute("""
            SELECT 
                COUNT(*) as count,
                MAX(star_system) as sys_name,
                MAX(scan_timestamp) as latest_ts,
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
                SUM(CASE WHEN was_discovered = 0 THEN 1 ELSE 0 END) as first_disc_count,
                MAX(CASE WHEN was_discovered = 0 THEN 1 ELSE 0 END) as has_first_disc,
                ROUND(AVG(CASE WHEN landable = 1 AND radius IS NOT NULL AND radius > 0 THEN radius ELSE NULL END), 1) as avg_landable_radius
            FROM bodies 
            WHERE system_address = ? 
              AND (star_type IS NOT NULL OR planet_class IS NOT NULL)
        """, (sys_addr, sys_addr))
        row = self.cursor.fetchone()
        if row and row["count"] > 0:
            sys_name = row["sys_name"] or f"System {sys_addr}"
            ts = row["latest_ts"] or datetime.now().isoformat()
            main_star = row["main_star"]

            # Check if system is populated - populated bubble systems are never CMDR first discoveries
            self.cursor.execute("SELECT population FROM systems WHERE system_address = ?", (sys_addr,))
            pop_row = self.cursor.fetchone()
            is_populated = bool(pop_row and pop_row["population"] and pop_row["population"] > 0)
            first_disc_count = 0 if is_populated else (row["first_disc_count"] or 0)
            has_first_disc = 0 if is_populated else (row["has_first_disc"] or 0)

            self.cursor.execute("""
                INSERT INTO systems (
                    system_address, star_system, first_visited, last_visited,
                    scanned_bodies, main_star_type, total_fss_value, total_dss_value,
                    total_potential_value, total_bio_signals, has_elw,
                    has_water_world, has_ammonia, has_terraformable, has_bio,
                    has_landable, has_high_g, has_anomalies, first_discovered_bodies, has_first_discover,
                    avg_landable_radius
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address) DO UPDATE SET
                    scanned_bodies = excluded.scanned_bodies,
                    main_star_type = COALESCE(excluded.main_star_type, systems.main_star_type),
                    total_fss_value = excluded.total_fss_value,
                    total_dss_value = excluded.total_dss_value,
                    total_potential_value = excluded.total_potential_value,
                    total_bio_signals = excluded.total_bio_signals,
                    has_elw = excluded.has_elw,
                    has_water_world = excluded.has_water_world,
                    has_ammonia = excluded.has_ammonia,
                    has_terraformable = excluded.has_terraformable,
                    has_bio = excluded.has_bio,
                    has_landable = excluded.has_landable,
                    has_high_g = excluded.has_high_g,
                    has_anomalies = excluded.has_anomalies,
                    first_discovered_bodies = excluded.first_discovered_bodies,
                    has_first_discover = excluded.has_first_discover,
                    avg_landable_radius = excluded.avg_landable_radius
            """, (
                sys_addr, sys_name, ts, ts,
                row["count"], main_star, row["sum_fss"] or 0, row["sum_dss"] or 0,
                row["sum_max"] or 0, row["sum_bio"] or 0, row["elw"] or 0,
                row["ww"] or 0, row["ammonia"] or 0, row["tf"] or 0, row["bio"] or 0,
                row["landable"] or 0, row["high_g"] or 0, row["anomalies"] or 0,
                first_disc_count, has_first_disc,
                row["avg_landable_radius"] or 0
            ))

    def parse_file(self, filepath: str, progress_callback=None):
        path = Path(filepath)
        if not path.exists():
            return

        try:
            stat = path.stat()
            file_size = stat.st_size
            last_mod = stat.st_mtime
        except (OSError, PermissionError):
            # File might be temporarily locked or being created by Elite Dangerous; retry safely later
            return

        filename = path.name

        self.cursor.execute("SELECT file_size, last_modified, last_line_offset FROM parsed_files WHERE filename = ?", (filename,))
        row = self.cursor.fetchone()

        start_offset = 0
        if row:
            if row["file_size"] == file_size and row["last_modified"] == last_mod:
                # Already up to date
                return
            start_offset = row["last_line_offset"] or 0
            # If file was truncated or recreated, reset offset to start of file
            if file_size < start_offset:
                start_offset = 0

        # Non-blocking safe read: Open file in binary read-only mode for exact byte offsets.
        # To prevent race conditions with Elite Dangerous disk flushes, read line by line
        # ensuring any trailing incomplete line (missing newline) is NOT processed and offset is wound back.
        try:
            with open(filepath, "rb") as f:
                if start_offset > 0:
                    f.seek(start_offset)

                valid_bytes_processed = start_offset
                while True:
                    line_start_pos = f.tell()
                    raw_bytes = f.readline()
                    if not raw_bytes:
                        break

                    # Check if line was completely written (must end with newline b'\n' or b'\r')
                    # If file ends without newline, Elite Dangerous is currently buffering/writing this line!
                    if not raw_bytes.endswith(b"\n") and not raw_bytes.endswith(b"\r"):
                        # Incomplete line! Do NOT advance offset past line_start_pos
                        break

                    line = raw_bytes.decode("utf-8", errors="replace")
                    self.process_journal_line(line)
                    valid_bytes_processed = f.tell()

                current_offset = valid_bytes_processed
        except (PermissionError, OSError) as read_err:
            # If Elite Dangerous is holding an exclusive write/flush handle, don't crash or corrupt.
            # The next watcher cycle will safely pick it up.
            print(f"[Journal Read Warning] File locked or unavailable ({filename}): {read_err}")
            return

        # Batch-update systems modified during this file's parse
        self.flush_dirty_systems()

        now_str = datetime.now().isoformat()
        self.cursor.execute("""
            INSERT INTO parsed_files (filename, file_size, last_modified, parsed_at, last_line_offset)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(filename) DO UPDATE SET
                file_size = excluded.file_size,
                last_modified = excluded.last_modified,
                parsed_at = excluded.parsed_at,
                last_line_offset = excluded.last_line_offset
        """, (filename, file_size, last_mod, now_str, current_offset))

        self.conn.commit()

    def parse_all_journals(self, journal_dir: str, progress_callback=None) -> int:
        files = sorted(glob.glob(os.path.join(journal_dir, "Journal.*.log")))
        total = len(files)
        count = 0
        for fpath in files:
            self.parse_file(fpath)
            count += 1
            if progress_callback:
                progress_callback(count, total, Path(fpath).name)
        self.flush_dirty_systems()
        self.conn.commit()
        return count
