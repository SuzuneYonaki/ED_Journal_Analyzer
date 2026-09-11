import sqlite3
import json
from pathlib import Path
from app.config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn

def checkpoint_wal(conn=None):
    """Flushes and truncates WAL journal file into main database."""
    close_after = False
    try:
        if conn is None:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0, check_same_thread=False)
            close_after = True
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except Exception as e:
        print(f"[DB] WAL checkpoint warning: {e}")
    finally:
        if close_after and conn:
            try:
                conn.close()
            except Exception:
                pass

def verify_db_integrity(conn=None) -> bool:
    """Verifies SQLite database integrity on startup."""
    close_after = False
    try:
        if conn is None:
            conn = sqlite3.connect(str(DB_PATH), timeout=10.0, check_same_thread=False)
            close_after = True
        res = conn.execute("PRAGMA quick_check;").fetchone()
        status = res[0] if res else "unknown"
        if status != "ok":
            print(f"[DB] Quick check status: {status}")
            return False
        return True
    except Exception as e:
        print(f"[DB] Integrity check error: {e}")
        return False
    finally:
        if close_after and conn:
            try:
                conn.close()
            except Exception:
                pass

def init_db(conn=None):
    close_after = False
    if conn is None:
        conn = get_db_connection()
        close_after = True
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Systems table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS systems (
        system_address INTEGER PRIMARY KEY,
        star_system TEXT NOT NULL,
        star_pos_x REAL,
        star_pos_y REAL,
        star_pos_z REAL,
        system_allegiance TEXT,
        system_economy TEXT,
        system_government TEXT,
        system_security TEXT,
        population INTEGER,
        first_visited TEXT,
        last_visited TEXT,
        visit_count INTEGER DEFAULT 1,
        total_bodies INTEGER DEFAULT 0,
        scanned_bodies INTEGER DEFAULT 0,
        main_star_type TEXT,
        total_potential_value INTEGER DEFAULT 0,
        total_fss_value INTEGER DEFAULT 0,
        total_dss_value INTEGER DEFAULT 0,
        total_bio_value INTEGER DEFAULT 0,
        total_bio_signals INTEGER DEFAULT 0,
        has_elw INTEGER DEFAULT 0,
        has_water_world INTEGER DEFAULT 0,
        has_ammonia INTEGER DEFAULT 0,
        has_terraformable INTEGER DEFAULT 0,
        has_bio INTEGER DEFAULT 0,
        has_landable INTEGER DEFAULT 0,
        has_high_g INTEGER DEFAULT 0,
        has_anomalies INTEGER DEFAULT 0,
        avg_landable_radius REAL DEFAULT 0,
        is_shared INTEGER DEFAULT 0,
        shared_by TEXT DEFAULT '',
        shared_at TEXT DEFAULT '',
        shared_notes TEXT DEFAULT ''
    );
    """)

    # Bodies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bodies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_address INTEGER NOT NULL,
        body_id INTEGER,
        body_name TEXT NOT NULL,
        star_system TEXT,
        distance_from_arrival_ls REAL,
        star_type TEXT,
        stellar_mass REAL,
        absolute_magnitude REAL,
        radius REAL,
        surface_temperature REAL,
        planet_class TEXT,
        atmosphere TEXT,
        atmosphere_type TEXT,
        atmosphere_composition TEXT,
        mass_em REAL,
        surface_gravity REAL,
        surface_gravity_g REAL,
        surface_pressure REAL,
        landable INTEGER DEFAULT 0,
        volcanism TEXT,
        terraforming_state TEXT,
        tidal_lock INTEGER DEFAULT 0,
        semi_major_axis REAL,
        eccentricity REAL,
        orbital_inclination REAL,
        periapsis REAL,
        orbital_period REAL,
        ascending_node REAL,
        mean_anomaly REAL,
        rotation_period REAL,
        axial_tilt REAL,
        rings TEXT,
        materials TEXT,
        parents TEXT,
        was_discovered INTEGER DEFAULT 0,
        was_mapped INTEGER DEFAULT 0,
        is_mapped_by_user INTEGER DEFAULT 0,
        is_first_discovered_by_user INTEGER DEFAULT 0,
        bio_signals INTEGER DEFAULT 0,
        geo_signals INTEGER DEFAULT 0,
        mining_signals INTEGER DEFAULT 0,
        reserve_level TEXT,
        fss_value INTEGER DEFAULT 0,
        dss_value INTEGER DEFAULT 0,
        first_discovered_fss INTEGER DEFAULT 0,
        first_mapped_dss INTEGER DEFAULT 0,
        max_potential_value INTEGER DEFAULT 0,
        confirmed_genuses TEXT,
        exobiology_predictions TEXT,
        anomalies_json TEXT,
        scan_type TEXT,
        luminosity TEXT,
        scan_timestamp TEXT,
        updated_timestamp TEXT,
        UNIQUE(system_address, body_id)
    );
    """)

    # Visits timeline table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_address INTEGER NOT NULL,
        star_system TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        star_pos_x REAL,
        star_pos_y REAL,
        star_pos_z REAL,
        jump_dist REAL,
        fuel_used REAL,
        ship TEXT,
        is_taxi INTEGER DEFAULT 0,
        is_carrier INTEGER DEFAULT 0
    );
    """)

    # Scanned organics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scanned_organics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_address INTEGER NOT NULL,
        body_id INTEGER,
        body_name TEXT,
        timestamp TEXT NOT NULL,
        scan_type TEXT,
        genus TEXT,
        genus_localised TEXT,
        species TEXT,
        species_localised TEXT,
        variant TEXT,
        variant_localised TEXT,
        base_value INTEGER DEFAULT 0,
        first_discovery_value INTEGER DEFAULT 0
    );
    """)

    # Surface mining activities (Rhino SRV & surface mining tracking)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS surface_mining_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_address INTEGER NOT NULL,
        star_system TEXT,
        body_id INTEGER,
        body_name TEXT,
        body_type TEXT,
        srv_type TEXT,
        material_name TEXT NOT NULL,
        material_name_localised TEXT,
        category TEXT,
        count INTEGER DEFAULT 1,
        latitude REAL,
        longitude REAL,
        timestamp TEXT NOT NULL
    );
    """)

    # Parsed files tracker
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parsed_files (
        filename TEXT PRIMARY KEY,
        file_size INTEGER,
        last_modified REAL,
        parsed_at TEXT,
        last_line_offset INTEGER DEFAULT 0
    );
    """)

    # Celestial body bookmarks and markdown notes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS body_bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        system_address INTEGER NOT NULL,
        body_id INTEGER NOT NULL,
        body_name TEXT NOT NULL,
        star_system TEXT NOT NULL,
        alias_name TEXT DEFAULT '',
        note_markdown TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(system_address, body_id)
    );
    """)

    # Astrophysical evaluations table (ED_Analysys / Stellar Physics Engine)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_physics_evaluations (
        system_address INTEGER PRIMARY KEY,
        star_system TEXT NOT NULL,
        rarity_score REAL NOT NULL,
        star_count INTEGER NOT NULL,
        planet_count INTEGER NOT NULL,
        anomalies_json TEXT NOT NULL,
        narrative_report TEXT NOT NULL,
        raw_features_json TEXT NOT NULL,
        evaluated_at TEXT NOT NULL,
        FOREIGN KEY (system_address) REFERENCES systems(system_address)
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_physics_eval_score ON system_physics_evaluations(rarity_score DESC);")

    # If dist/data/elite_journal.db has evaluations not in local DB, import them
    try:
        dist_db = Path(__file__).resolve().parent.parent.parent / "dist" / "data" / "elite_journal.db"
        if dist_db.exists() and dist_db.resolve() != Path(DB_PATH).resolve():
            with sqlite3.connect(dist_db) as d_conn:
                d_cur = d_conn.cursor()
                d_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_physics_evaluations'")
                if d_cur.fetchone():
                    d_cur.execute("SELECT system_address, star_system, rarity_score, star_count, planet_count, anomalies_json, narrative_report, raw_features_json, evaluated_at FROM system_physics_evaluations")
                    dist_rows = d_cur.fetchall()
                    for dr in dist_rows:
                        cursor.execute("""
                            INSERT OR IGNORE INTO system_physics_evaluations 
                            (system_address, star_system, rarity_score, star_count, planet_count, anomalies_json, narrative_report, raw_features_json, evaluated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, dr)
    except Exception as e:
        pass

    # Indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_name ON systems(star_system);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_last_visited ON systems(last_visited DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bodies_sys_addr ON bodies(system_address);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bodies_name ON bodies(body_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_sys_addr ON visits(system_address);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_ts ON visits(timestamp DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_organics_sys ON scanned_organics(system_address);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mining_act_sys ON surface_mining_activities(system_address);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mining_act_body ON surface_mining_activities(system_address, body_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_body_bookmarks_sys ON body_bookmarks(system_address);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_body_bookmarks_body ON body_bookmarks(system_address, body_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_body_bookmarks_alias ON body_bookmarks(alias_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bodies_sys_star ON bodies(system_address, star_type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_main_star ON systems(main_star_type);")

    # Migration for surface_mining_activities columns if table already existed
    for col_def in [
        ("body_type", "TEXT"),
        ("star_system", "TEXT"),
        ("material_name_localised", "TEXT"),
        ("latitude", "REAL"),
        ("longitude", "REAL"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE surface_mining_activities ADD COLUMN {col_def[0]} {col_def[1]};")
        except Exception:
            pass

    for col_def in [
        ("total_bio_signals", "INTEGER DEFAULT 0"),
        ("has_water_world", "INTEGER DEFAULT 0"),
        ("main_star_type", "TEXT"),
        ("sol_distance_ly", "REAL DEFAULT 0"),
        ("has_first_discover", "INTEGER DEFAULT 0"),
        ("first_discovered_bodies", "INTEGER DEFAULT 0"),
        ("last_targeted_body_id", "INTEGER"),
        ("edsm_checked", "INTEGER DEFAULT 0"),
        ("edsm_registered", "INTEGER DEFAULT 0"),
        ("edsm_first_discoverer", "TEXT"),
        ("edsm_submitted_at", "TEXT"),
        ("edsm_body_count", "INTEGER DEFAULT 0"),
        ("avg_landable_radius", "REAL DEFAULT 0"),
        ("is_shared", "INTEGER DEFAULT 0"),
        ("shared_by", "TEXT DEFAULT ''"),
        ("shared_at", "TEXT DEFAULT ''"),
        ("shared_notes", "TEXT DEFAULT ''"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE systems ADD COLUMN {col_def[0]} {col_def[1]};")
        except Exception:
            pass

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_systems_shared ON systems(is_shared);")

    for col_def in [
        ("star_pos_x", "REAL"),
        ("star_pos_y", "REAL"),
        ("star_pos_z", "REAL"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE visits ADD COLUMN {col_def[0]} {col_def[1]};")
        except Exception:
            pass

    for col_def in [
        ("confirmed_genuses", "TEXT"),
        ("edsm_discovered_by", "TEXT"),
        ("edsm_discovered_at", "TEXT"),
        ("mining_signals", "INTEGER DEFAULT 0"),
        ("reserve_level", "TEXT"),
        ("scan_type", "TEXT"),
        ("luminosity", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE bodies ADD COLUMN {col_def[0]} {col_def[1]};")
        except Exception:
            pass

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bodies_luminosity ON bodies(system_address, luminosity);")

    for col_def in [
        ("alias_name", "TEXT DEFAULT ''"),
        ("note_markdown", "TEXT DEFAULT ''"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE body_bookmarks ADD COLUMN {col_def[0]} {col_def[1]};")
        except Exception:
            pass

    # Clean up non-celestial records (Belt Clusters, Rings, Barycentres without star/planet type)
    cursor.execute("""
        DELETE FROM bodies 
        WHERE (star_type IS NULL AND planet_class IS NULL)
           OR LOWER(body_name) LIKE '%belt cluster%'
           OR LOWER(body_name) LIKE '% ring%';
    """)

    # Correct false first discovery caused by NavBeacon scans, already mapped bodies, or populated systems
    cursor.execute("""
        UPDATE bodies SET was_discovered = 1 
        WHERE was_discovered = 0 AND (
            was_mapped = 1 
            OR scan_type IN ('NavBeacon', 'NavBeaconDetail')
            OR system_address IN (SELECT system_address FROM systems WHERE population > 0)
        );
    """)

    # Ensure system flags, scanned bodies count, sol distance, and first discovery consistency
    cursor.execute("""
        UPDATE systems SET
            scanned_bodies = (
                SELECT COUNT(*) FROM bodies b
                WHERE b.system_address = systems.system_address
                  AND (b.star_type IS NOT NULL OR b.planet_class IS NOT NULL)
            ),
            sol_distance_ly = CASE 
                WHEN star_pos_x IS NOT NULL AND star_pos_y IS NOT NULL AND star_pos_z IS NOT NULL
                THEN ROUND(SQRT(star_pos_x * star_pos_x + star_pos_y * star_pos_y + star_pos_z * star_pos_z), 1)
                ELSE 0 
            END,
            main_star_type = COALESCE(main_star_type, (
                SELECT b.star_type FROM bodies b
                WHERE b.system_address = systems.system_address AND b.star_type IS NOT NULL
                ORDER BY b.distance_from_arrival_ls ASC, b.body_id ASC LIMIT 1
            )),
            has_water_world = COALESCE((
                SELECT MAX(CASE WHEN LOWER(b.planet_class) LIKE '%water world%' THEN 1 ELSE 0 END)
                FROM bodies b WHERE b.system_address = systems.system_address
            ), 0),
            total_bio_signals = COALESCE((
                SELECT SUM(b.bio_signals)
                FROM bodies b WHERE b.system_address = systems.system_address
            ), 0),
            has_bio = COALESCE((
                SELECT MAX(CASE WHEN b.bio_signals > 0 THEN 1 ELSE 0 END)
                FROM bodies b WHERE b.system_address = systems.system_address
            ), 0),
            has_high_g = COALESCE((
                SELECT MAX(CASE WHEN b.landable = 1 AND b.surface_gravity_g >= 3.0 THEN 1 ELSE 0 END)
                FROM bodies b WHERE b.system_address = systems.system_address
            ), 0),
            first_discovered_bodies = CASE 
                WHEN systems.population > 0 THEN 0
                ELSE COALESCE((
                    SELECT COUNT(*) FROM bodies b
                    WHERE b.system_address = systems.system_address 
                      AND b.was_discovered = 0
                      AND (b.star_type IS NOT NULL OR b.planet_class IS NOT NULL)
                ), 0)
            END,
            has_first_discover = CASE 
                WHEN systems.population > 0 THEN 0
                ELSE COALESCE((
                    SELECT MAX(CASE WHEN b.was_discovered = 0 THEN 1 ELSE 0 END)
                    FROM bodies b WHERE b.system_address = systems.system_address
                      AND (b.star_type IS NOT NULL OR b.planet_class IS NOT NULL)
                ), 0)
            END,
            avg_landable_radius = COALESCE((
                SELECT ROUND(AVG(b.radius), 1)
                FROM bodies b WHERE b.system_address = systems.system_address
                  AND b.landable = 1
                  AND b.radius IS NOT NULL
                  AND b.radius > 0
            ), 0);
    """)

    # Backfill heavy mass code and close binary anomalies on star bodies
    from app.analyzer.anomaly_finder import detect_anomalies
    import json

    cursor.execute("SELECT id, body_name, star_system, star_type, distance_from_arrival_ls, semi_major_axis, parents, eccentricity, orbital_period, rotation_period, orbital_inclination, landable, surface_gravity_g, rings, volcanism, planet_class, terraforming_state, anomalies_json FROM bodies WHERE star_type IS NOT NULL")
    star_rows = cursor.fetchall()
    for row in star_rows:
        body_dict = dict(row)
        anomalies = detect_anomalies(body_dict)
        new_json = json.dumps(anomalies)
        if new_json != (row["anomalies_json"] or "[]"):
            cursor.execute("UPDATE bodies SET anomalies_json = ? WHERE id = ?", (new_json, row["id"]))

    # Update systems has_anomalies flag
    cursor.execute("""
        UPDATE systems SET
            has_anomalies = COALESCE((
                SELECT MAX(CASE WHEN b.anomalies_json != '[]' AND b.anomalies_json IS NOT NULL THEN 1 ELSE 0 END)
                FROM bodies b WHERE b.system_address = systems.system_address
            ), 0);
    """)

    # Backfill star luminosity from journal logs if existing database records lack luminosity
    try:
        cursor.execute("SELECT COUNT(*) FROM bodies WHERE star_type IS NOT NULL AND (luminosity IS NULL OR luminosity = '')")
        missing_lum_count = cursor.fetchone()[0]
        if missing_lum_count > 0:
            import glob
            from app.config import DEFAULT_JOURNAL_DIR
            if DEFAULT_JOURNAL_DIR.exists():
                files = sorted(glob.glob(str(DEFAULT_JOURNAL_DIR / "Journal.*.log")))
                updates = []
                for fpath in files:
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as jf:
                            for line in jf:
                                if '"Scan"' in line and '"StarType"' in line and '"Luminosity"' in line:
                                    data = json.loads(line)
                                    lum = data.get("Luminosity")
                                    sys_addr = data.get("SystemAddress")
                                    body_id = data.get("BodyID")
                                    if lum and sys_addr and body_id is not None:
                                        updates.append((lum, sys_addr, body_id))
                    except Exception:
                        pass
                if updates:
                    cursor.executemany("""
                        UPDATE bodies SET luminosity = ?
                        WHERE system_address = ? AND body_id = ? AND (luminosity IS NULL OR luminosity = '')
                    """, updates)
    except Exception as e:
        print(f"Luminosity migration notice: {e}")

    conn.commit()
    if close_after:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
