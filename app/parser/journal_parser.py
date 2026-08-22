import os
import json
import glob
from pathlib import Path
from datetime import datetime

from app.db.database import get_db_connection
from app.parser.value_calculator import calculate_body_value
from app.parser.exobiology import predict_exobiology_candidates, get_species_value
from app.analyzer.anomaly_finder import detect_anomalies

class JournalParser:
    def __init__(self, db_conn=None):
        self.conn = db_conn or get_db_connection()
        self.cursor = self.conn.cursor()

    def process_journal_line(self, line: str):
        if not line or not line.strip():
            return
        try:
            event_data = json.loads(line.strip())
        except Exception:
            return

        event = event_data.get("event")
        timestamp = event_data.get("timestamp", "")

        if event in ["FSDJump", "Location", "CarrierJump"]:
            self._handle_jump_or_location(event_data, timestamp)
        elif event == "FSSDiscoveryScan":
            self._handle_fss_discovery_scan(event_data)
        elif event == "Scan":
            self._handle_scan(event_data, timestamp)
        elif event in ["FSSBodySignals", "SAASignalsFound"]:
            self._handle_signals(event_data)
        elif event == "SAAScanComplete":
            self._handle_saa_scan_complete(event_data)
        elif event == "ScanOrganic":
            self._handle_scan_organic(event_data, timestamp)

    def _handle_jump_or_location(self, data: dict, timestamp: str):
        sys_addr = data.get("SystemAddress")
        star_sys = data.get("StarSystem")
        if not sys_addr or not star_sys:
            return

        star_pos = data.get("StarPos", [0, 0, 0])
        pos_x, pos_y, pos_z = (star_pos[0], star_pos[1], star_pos[2]) if len(star_pos) >= 3 else (0, 0, 0)
        sol_dist = round((pos_x**2 + pos_y**2 + pos_z**2)**0.5, 1) if (pos_x is not None and pos_y is not None and pos_z is not None) else 0

        star_class = data.get("StarClass") or data.get("StarType")
        allegiance = data.get("SystemAllegiance")
        economy = data.get("SystemEconomy_Localised") or data.get("SystemEconomy")
        govt = data.get("SystemGovernment_Localised") or data.get("SystemGovernment")
        sec = data.get("SystemSecurity_Localised") or data.get("SystemSecurity")
        pop = data.get("Population", 0)

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
                    last_visited = ?,
                    visit_count = visit_count + 1
                WHERE system_address = ?
            """, (star_sys, pos_x, pos_y, pos_z, sol_dist, sol_dist, star_class, timestamp, sys_addr))
        else:
            self.cursor.execute("""
                INSERT INTO systems (
                    system_address, star_system, star_pos_x, star_pos_y, star_pos_z, sol_distance_ly,
                    main_star_type, system_allegiance, system_economy, system_government, system_security,
                    population, first_visited, last_visited, visit_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (sys_addr, star_sys, pos_x, pos_y, pos_z, sol_dist, star_class, allegiance, economy, govt, sec, pop, timestamp, timestamp, 1))

        # Record visit timeline if FSDJump
        if data.get("event") == "FSDJump":
            jump_dist = data.get("JumpDist", 0)
            fuel = data.get("FuelUsed", 0)
            taxi = 1 if data.get("Taxi", False) else 0
            self.cursor.execute("""
                INSERT INTO visits (system_address, star_system, timestamp, jump_dist, fuel_used, is_taxi)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sys_addr, star_sys, timestamp, jump_dist, fuel, taxi))

    def _handle_fss_discovery_scan(self, data: dict):
        sys_addr = data.get("SystemAddress")
        body_count = data.get("BodyCount", 0)
        if sys_addr:
            self.cursor.execute("""
                UPDATE systems SET total_bodies = MAX(total_bodies, ?) WHERE system_address = ?
            """, (body_count, sys_addr))

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

        was_discovered = 1 if data.get("WasDiscovered", False) else 0
        was_mapped = 1 if data.get("WasMapped", False) else 0

        # Calculate values
        body_dict = {
            "star_type": star_type,
            "stellar_mass": stellar_mass,
            "planet_class": planet_class,
            "mass_em": mass_em,
            "terraforming_state": terraforming,
            "landable": landable,
            "surface_temperature": surface_temp,
            "surface_gravity": gravity_raw,
            "surface_gravity_g": gravity_g,
            "atmosphere": atmosphere,
            "volcanism": volcanism,
            "eccentricity": eccentricity,
            "orbital_period": orbital_period,
            "rotation_period": rotation_period,
            "orbital_inclination": inclination,
            "rings": rings,
            "bio_signals": 0
        }

        # Check if already had bio_signals in existing body record
        self.cursor.execute("SELECT bio_signals, geo_signals, is_mapped_by_user FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
        existing_b = self.cursor.fetchone()
        existing_bio = existing_b["bio_signals"] if existing_b else 0
        existing_geo = existing_b["geo_signals"] if existing_b else 0
        existing_mapped = existing_b["is_mapped_by_user"] if existing_b else 0
        body_dict["bio_signals"] = existing_bio

        values = calculate_body_value(body_dict)
        fss_val = values.get("fss_value", 0)
        dss_val = values.get("dss_value", 0)
        fd_fss = values.get("first_discovered_fss", 0)
        fm_dss = values.get("first_mapped_dss", 0)
        max_pot = values.get("max_potential_value", 0)

        # Predict Exobiology candidates
        bio_predictions = predict_exobiology_candidates(body_dict)
        bio_pred_json = json.dumps(bio_predictions)

        # Detect Anomalies
        anomalies = detect_anomalies(body_dict)
        anomalies_json = json.dumps(anomalies)

        self.cursor.execute("""
            INSERT INTO bodies (
                system_address, body_id, body_name, star_system, distance_from_arrival_ls,
                star_type, stellar_mass, absolute_magnitude, radius, surface_temperature,
                planet_class, atmosphere, atmosphere_type, atmosphere_composition,
                mass_em, surface_gravity, surface_gravity_g, surface_pressure, landable,
                volcanism, terraforming_state, tidal_lock, semi_major_axis, eccentricity,
                orbital_inclination, periapsis, orbital_period, ascending_node, mean_anomaly,
                rotation_period, axial_tilt, rings, materials, parents, was_discovered, was_mapped,
                is_mapped_by_user, bio_signals, geo_signals, fss_value, dss_value,
                first_discovered_fss, first_mapped_dss, max_potential_value,
                exobiology_predictions, anomalies_json, scan_timestamp, updated_timestamp
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(system_address, body_id) DO UPDATE SET
                body_name = excluded.body_name,
                star_system = COALESCE(excluded.star_system, bodies.star_system),
                distance_from_arrival_ls = excluded.distance_from_arrival_ls,
                star_type = COALESCE(excluded.star_type, bodies.star_type),
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
                was_discovered = excluded.was_discovered,
                was_mapped = excluded.was_mapped,
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
            star_type, stellar_mass, data.get("AbsoluteMagnitude"), radius, surface_temp,
            planet_class, atmosphere, atmosphere_type, atmosphere_comp,
            mass_em, gravity_raw, gravity_g, surface_pressure, landable,
            volcanism, terraforming, tidal_lock, semi_major_axis, eccentricity,
            inclination, periapsis, orbital_period, ascending_node, mean_anomaly,
            rotation_period, axial_tilt, rings, materials, parents, was_discovered, was_mapped,
            existing_mapped, existing_bio, existing_geo, fss_val, dss_val,
            fd_fss, fm_dss, max_pot,
            bio_pred_json, anomalies_json, timestamp, timestamp
        ))

        self._update_system_stats(sys_addr)

    def _handle_signals(self, data: dict):
        sys_addr = data.get("SystemAddress")
        body_id = data.get("BodyID")
        body_name = data.get("BodyName")
        signals = data.get("Signals", [])

        if sys_addr is None:
            return

        bio_count = 0
        geo_count = 0
        for s in signals:
            stype = s.get("Type", "")
            scount = s.get("Count", 0)
            if "$SAA_SignalType_Biological" in stype or "biological" in stype.lower() or "bio" in stype.lower():
                bio_count += scount
            elif "$SAA_SignalType_Geological" in stype or "geological" in stype.lower() or "geo" in stype.lower():
                geo_count += scount

        # Check if body exists
        if body_id is not None:
            self.cursor.execute("SELECT * FROM bodies WHERE system_address = ? AND body_id = ?", (sys_addr, body_id))
        elif body_name:
            self.cursor.execute("SELECT * FROM bodies WHERE system_address = ? AND body_name = ?", (sys_addr, body_name))
        else:
            return

        existing = self.cursor.fetchone()
        if existing:
            # Update existing record and recalculate bio predictions / anomalies
            b_dict = dict(existing)
            b_dict["bio_signals"] = bio_count
            b_dict["geo_signals"] = geo_count
            
            bio_predictions = predict_exobiology_candidates(b_dict)
            bio_pred_json = json.dumps(bio_predictions)
            anomalies = detect_anomalies(b_dict)
            anomalies_json = json.dumps(anomalies)

            self.cursor.execute("""
                UPDATE bodies SET
                    bio_signals = ?,
                    geo_signals = ?,
                    exobiology_predictions = ?,
                    anomalies_json = ?
                WHERE id = ?
            """, (bio_count, geo_count, bio_pred_json, anomalies_json, existing["id"]))
        else:
            # Insert stub body record if Scan hasn't occurred yet
            b_dict = {
                "system_address": sys_addr,
                "body_id": body_id or 0,
                "body_name": body_name or f"Body {body_id}",
                "bio_signals": bio_count,
                "geo_signals": geo_count
            }
            bio_predictions = predict_exobiology_candidates(b_dict)
            bio_pred_json = json.dumps(bio_predictions)
            anomalies = detect_anomalies(b_dict)
            anomalies_json = json.dumps(anomalies)

            self.cursor.execute("""
                INSERT INTO bodies (
                    system_address, body_id, body_name, bio_signals, geo_signals,
                    exobiology_predictions, anomalies_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(system_address, body_id) DO UPDATE SET
                    bio_signals = excluded.bio_signals,
                    geo_signals = excluded.geo_signals,
                    exobiology_predictions = excluded.exobiology_predictions,
                    anomalies_json = excluded.anomalies_json
            """, (sys_addr, body_id or 0, body_name or f"Body {body_id}", bio_count, geo_count, bio_pred_json, anomalies_json))

        self._update_system_stats(sys_addr)

    def _handle_saa_scan_complete(self, data: dict):
        sys_addr = data.get("SystemAddress")
        body_id = data.get("BodyID")
        body_name = data.get("BodyName")

        if sys_addr is not None:
            if body_id is not None:
                self.cursor.execute("""
                    UPDATE bodies SET is_mapped_by_user = 1 WHERE system_address = ? AND body_id = ?
                """, (sys_addr, body_id))
            elif body_name:
                self.cursor.execute("""
                    UPDATE bodies SET is_mapped_by_user = 1 WHERE system_address = ? AND body_name = ?
                """, (sys_addr, body_name))

    def _handle_scan_organic(self, data: dict, timestamp: str):
        sys_addr = data.get("SystemAddress")
        body_id = data.get("BodyID")
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

        if sys_addr is not None:
            self.cursor.execute("""
                INSERT INTO scanned_organics (
                    system_address, body_id, timestamp, scan_type, genus, genus_localised,
                    species, species_localised, variant, variant_localised, base_value, first_discovery_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sys_addr, body_id, timestamp, scan_type, genus, genus_loc,
                species, species_loc, variant, variant_loc, base_val, fd_val
            ))

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
                MAX(CASE WHEN was_discovered = 0 THEN 1 ELSE 0 END) as has_first_disc
            FROM bodies 
            WHERE system_address = ? 
              AND (star_type IS NOT NULL OR planet_class IS NOT NULL)
        """, (sys_addr, sys_addr))
        row = self.cursor.fetchone()
        if row and row["count"] > 0:
            sys_name = row["sys_name"] or f"System {sys_addr}"
            ts = row["latest_ts"] or datetime.now().isoformat()
            main_star = row["main_star"]
            self.cursor.execute("""
                INSERT INTO systems (
                    system_address, star_system, first_visited, last_visited,
                    scanned_bodies, main_star_type, total_fss_value, total_dss_value,
                    total_potential_value, total_bio_signals, has_elw,
                    has_water_world, has_ammonia, has_terraformable, has_bio,
                    has_landable, has_high_g, has_anomalies, first_discovered_bodies, has_first_discover
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    has_first_discover = excluded.has_first_discover
            """, (
                sys_addr, sys_name, ts, ts,
                row["count"], main_star, row["sum_fss"] or 0, row["sum_dss"] or 0,
                row["sum_max"] or 0, row["sum_bio"] or 0, row["elw"] or 0,
                row["ww"] or 0, row["ammonia"] or 0, row["tf"] or 0, row["bio"] or 0,
                row["landable"] or 0, row["high_g"] or 0, row["anomalies"] or 0,
                row["first_disc_count"] or 0, row["has_first_disc"] or 0
            ))

    def parse_file(self, filepath: str, progress_callback=None):
        path = Path(filepath)
        if not path.exists():
            return

        stat = path.stat()
        file_size = stat.st_size
        last_mod = stat.st_mtime
        filename = path.name

        self.cursor.execute("SELECT file_size, last_modified, last_line_offset FROM parsed_files WHERE filename = ?", (filename,))
        row = self.cursor.fetchone()

        start_offset = 0
        if row:
            if row["file_size"] == file_size and row["last_modified"] == last_mod:
                # Already up to date
                return
            start_offset = row["last_line_offset"] or 0

        line_count = 0
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            if start_offset > 0:
                f.seek(start_offset)
            for line in f:
                self.process_journal_line(line)
                line_count += 1
            current_offset = f.tell()

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
            if progress_callback and count % 50 == 0:
                progress_callback(count, total)
        self.conn.commit()
        return total
