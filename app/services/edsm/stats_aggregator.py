"""
EDSM / Local DB Stats Aggregator.
Recalculates system-level aggregated statistics and mining scout candidate grades from bodies.
"""

def update_system_aggregated_stats(conn, system_address: int):
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

    # Evaluate mining scout candidate grade based on Pristine reserve and Metallic/Icy rings
    c.execute("SELECT system_reserve FROM systems WHERE system_address = ?", (system_address,))
    sys_res_row = c.fetchone()
    sys_reserve = sys_res_row["system_reserve"] if sys_res_row else ""
    is_pristine = (sys_reserve or "").strip().lower() in ["pristine", "$reserve_pristine;"]

    mining_grade = ""
    if is_pristine:
        c.execute("""
            SELECT 
                MAX(CASE WHEN rings LIKE '%Metallic%' THEN 1 ELSE 0 END) as has_metallic,
                MAX(CASE WHEN rings LIKE '%Icy%' THEN 1 ELSE 0 END) as has_icy
            FROM bodies
            WHERE system_address = ? AND rings IS NOT NULL AND rings != ''
        """, (system_address,))
        ring_row = c.fetchone()
        if ring_row:
            if ring_row["has_metallic"]:
                mining_grade = "High"
            elif ring_row["has_icy"]:
                mining_grade = "Medium"

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
            avg_landable_radius = ?,
            mining_scout_grade = ?
        WHERE system_address = ?
    """, (
        row["count"], row["main_star"], row["sum_fss"] or 0, row["sum_dss"] or 0,
        row["sum_max"] or 0, row["sum_bio"] or 0, row["elw"] or 0,
        row["ww"] or 0, row["ammonia"] or 0, row["tf"] or 0, row["bio"] or 0,
        row["landable"] or 0, row["high_g"] or 0, row["anomalies"] or 0,
        row["avg_landable_radius"] or 0,
        mining_grade,
        system_address
    ))
