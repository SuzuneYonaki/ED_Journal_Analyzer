import json
import os
import threading
import time
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import DEFAULT_JOURNAL_DIR, BASE_DIR, DATA_DIR
from app.db.database import get_db_connection, init_db
from app.parser.journal_parser import JournalParser
from app.parser.watcher import JournalWatcher
from app.analyzer.orbit_analyzer import build_system_hierarchy
from app.parser.exobiology import predict_exobiology_candidates, predict_system_exobiology_candidates
from app.services.edsm_service import edsm_service

app = FastAPI(title="Elite Dangerous Journal Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global scan status
scan_state = {
    "is_scanning": False,
    "current": 0,
    "total": 0,
    "percent": 0,
    "filename": "",
    "message": "Ready"
}

# Live update event tracking
last_journal_update = {
    "timestamp": time.time(),
    "version": 0,
    "file": None
}
last_journal_event = {
    "event": None,
    "data": None,
    "timestamp": 0.0,
    "version": 0
}

class LiveConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

    def notify_update_from_thread(self, file_path: Optional[str] = None):
        global last_journal_update
        last_journal_update["timestamp"] = time.time()
        last_journal_update["version"] += 1
        last_journal_update["file"] = file_path

        payload = {
            "type": "journal_updated",
            "version": last_journal_update["version"],
            "timestamp": last_journal_update["timestamp"],
            "file": file_path
        }
        if self.loop and self.loop.is_running() and self.active_connections:
            asyncio.run_coroutine_threadsafe(self.broadcast_json(payload), self.loop)

    def notify_event_from_thread(self, event_name: str, event_data: dict):
        global last_journal_event
        last_journal_event["version"] += 1
        last_journal_event["event"] = event_name
        last_journal_event["data"] = event_data
        last_journal_event["timestamp"] = time.time()

        payload = {
            "type": "journal_event",
            "event": event_name,
            "data": event_data,
            "version": last_journal_event["version"],
            "timestamp": last_journal_event["timestamp"]
        }
        if self.loop and self.loop.is_running() and self.active_connections:
            asyncio.run_coroutine_threadsafe(self.broadcast_json(payload), self.loop)

manager = LiveConnectionManager()
watcher_instance: Optional[JournalWatcher] = None

@app.on_event("startup")
async def on_startup():
    manager.loop = asyncio.get_running_loop()
    init_db()
    start_watcher()
    # Trigger background parse automatically on startup in separate thread
    threading.Thread(target=run_background_parse, daemon=True).start()

def on_journal_file_updated(file_path: Optional[str] = None):
    manager.notify_update_from_thread(file_path)

def on_journal_event(event_name: str, event_data: dict):
    manager.notify_event_from_thread(event_name, event_data)

def start_watcher():
    global watcher_instance
    if watcher_instance:
        watcher_instance.stop()

    candidate_dirs = [
        get_saved_journal_dir(),
        DEFAULT_JOURNAL_DIR,
        BASE_DIR,
        Path.cwd()
    ]
    # Filter unique existing or potential directories
    watched_dirs = []
    seen = set()
    for d in candidate_dirs:
        p = Path(d).resolve()
        if str(p) not in seen:
            seen.add(str(p))
            watched_dirs.append(p)

    print(f"[Watcher] Starting JournalWatcher on dirs: {[str(d) for d in watched_dirs]}")
    watcher_instance = JournalWatcher(
        journal_dirs=watched_dirs,
        interval=0.4,
        on_update_callback=on_journal_file_updated,
        on_event_callback=on_journal_event
    )
    watcher_instance.start()

@app.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial sync state
        await websocket.send_json({
            "type": "connected",
            "version": last_journal_update["version"],
            "timestamp": last_journal_update["timestamp"]
        })
        while True:
            # Keep connection open & handle ping/pong
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.get("/api/events/latest")
def get_latest_event():
    return {
        "version": last_journal_update["version"],
        "timestamp": last_journal_update["timestamp"],
        "event_version": last_journal_event["version"],
        "last_event": last_journal_event
    }

def get_current_cmdr_location(conn) -> Optional[dict]:
    try:
        c = conn.cursor()
        # First try: visits table joined with systems table to get coordinates of latest visit
        c.execute("""
            SELECT v.system_address, v.star_system, s.star_pos_x, s.star_pos_y, s.star_pos_z, v.timestamp 
            FROM visits v
            JOIN systems s ON v.system_address = s.system_address
            WHERE s.star_pos_x IS NOT NULL AND s.star_pos_y IS NOT NULL AND s.star_pos_z IS NOT NULL
            ORDER BY v.timestamp DESC LIMIT 1
        """)
        row = c.fetchone()
        if not row:
            # Second try: systems table by last_visited
            c.execute("""
                SELECT system_address, star_system, star_pos_x, star_pos_y, star_pos_z, last_visited as timestamp
                FROM systems 
                WHERE star_pos_x IS NOT NULL AND star_pos_y IS NOT NULL AND star_pos_z IS NOT NULL
                ORDER BY last_visited DESC LIMIT 1
            """)
            row = c.fetchone()
        if row:
            return {
                "system_address": row["system_address"],
                "star_system": row["star_system"],
                "star_pos_x": row["star_pos_x"],
                "star_pos_y": row["star_pos_y"],
                "star_pos_z": row["star_pos_z"],
                "timestamp": row["timestamp"]
            }
    except Exception as err:
        print("Warning: get_current_cmdr_location failed:", err)
    return None

@app.get("/api/stats")
def get_global_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    date_field: Optional[str] = "last_visited"
):
    conn = get_db_connection()
    c = conn.cursor()

    where_clauses = []
    params = []

    if date_from or date_to:
        if date_field == "first_visited":
            if date_from:
                where_clauses.append("first_visited >= ?")
                params.append(f"{date_from}T00:00:00")
            if date_to:
                where_clauses.append("first_visited <= ?")
                params.append(f"{date_to}T23:59:59")
        elif date_field == "any_visit":
            sub_conds = []
            sub_params = []
            if date_from:
                sub_conds.append("timestamp >= ?")
                sub_params.append(f"{date_from}T00:00:00")
            if date_to:
                sub_conds.append("timestamp <= ?")
                sub_params.append(f"{date_to}T23:59:59")
            where_clauses.append(f"system_address IN (SELECT DISTINCT system_address FROM visits WHERE {' AND '.join(sub_conds)})")
            params.extend(sub_params)
        else:
            if date_from:
                where_clauses.append("last_visited >= ?")
                params.append(f"{date_from}T00:00:00")
            if date_to:
                where_clauses.append("last_visited <= ?")
                params.append(f"{date_to}T23:59:59")

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    c.execute(f"""
        SELECT 
            COUNT(*) as total_systems,
            COALESCE(SUM(visit_count), 0) as total_visits,
            COALESCE(SUM(scanned_bodies), 0) as total_bodies,
            COALESCE(SUM(total_potential_value), 0) as total_potential_value,
            COALESCE(SUM(has_elw), 0) as elw_systems,
            COALESCE(SUM(has_water_world), 0) as ww_systems,
            COALESCE(SUM(has_ammonia), 0) as ammonia_systems,
            COALESCE(SUM(has_terraformable), 0) as terraformable_systems,
            COALESCE(SUM(has_bio), 0) as bio_systems,
            COALESCE(SUM(total_bio_signals), 0) as total_bio_signals,
            COALESCE(SUM(has_landable), 0) as landable_systems,
            COALESCE(SUM(has_anomalies), 0) as anomaly_systems
        FROM systems {where_sql}
    """, params)
    stats = dict(c.fetchone())

    # Bio signals sum in matching systems
    if where_sql:
        c.execute(f"SELECT COALESCE(SUM(bio_signals), 0) as sum_bio FROM bodies WHERE system_address IN (SELECT system_address FROM systems {where_sql})", params)
        stats["total_bio_signals"] = c.fetchone()["sum_bio"]
    else:
        c.execute("SELECT COALESCE(SUM(bio_signals), 0) as sum_bio FROM bodies")
        stats["total_bio_signals"] = max(stats.get("total_bio_signals", 0), c.fetchone()["sum_bio"])

    c.execute("SELECT COUNT(*) as count FROM scanned_organics")
    stats["total_scanned_organics"] = c.fetchone()["count"]

    stats["current_location"] = get_current_cmdr_location(conn)
    conn.close()
    return stats

@app.get("/api/systems")
def get_systems(
    q: Optional[str] = "",
    has_elw: Optional[bool] = False,
    has_water_world: Optional[bool] = False,
    has_ammonia: Optional[bool] = False,
    has_terraformable: Optional[bool] = False,
    has_bio: Optional[bool] = False,
    has_landable: Optional[bool] = False,
    has_high_g: Optional[bool] = False,
    has_anomalies: Optional[bool] = False,
    has_first_discover: Optional[bool] = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    date_field: Optional[str] = "last_visited",
    cmdr_x: Optional[float] = None,
    cmdr_y: Optional[float] = None,
    cmdr_z: Optional[float] = None,
    sort_by: Optional[str] = "total_potential_value",
    sort_order: Optional[str] = "desc",
    sort_by_2: Optional[str] = None,
    sort_order_2: Optional[str] = "desc",
    page: int = 1,
    limit: int = 50
):
    conn = get_db_connection()
    c = conn.cursor()

    page = max(1, page or 1)
    limit = min(500, max(1, limit or 50))

    # Determine CMDR location if not provided
    cur_loc = get_current_cmdr_location(conn)
    cx = cmdr_x if cmdr_x is not None else (cur_loc["star_pos_x"] if cur_loc else None)
    cy = cmdr_y if cmdr_y is not None else (cur_loc["star_pos_y"] if cur_loc else None)
    cz = cmdr_z if cmdr_z is not None else (cur_loc["star_pos_z"] if cur_loc else None)

    conditions = []
    params = []

    if q and q.strip():
        conditions.append("star_system LIKE ?")
        params.append(f"%{q.strip()}%")

    if has_elw:
        conditions.append("has_elw = 1")
    if has_water_world:
        conditions.append("has_water_world = 1")
    if has_ammonia:
        conditions.append("has_ammonia = 1")
    if has_terraformable:
        conditions.append("has_terraformable = 1")
    if has_bio:
        conditions.append("has_bio = 1")
    if has_landable:
        conditions.append("has_landable = 1")
    if has_high_g:
        conditions.append("has_high_g = 1")
    if has_anomalies:
        conditions.append("has_anomalies = 1")
    if has_first_discover:
        conditions.append("has_first_discover = 1")

    # Date range filtering
    target_date_col = "first_visited" if date_field == "first_visited" else "last_visited"
    if date_field == "any_visit":
        visit_conds = ["v.system_address = systems.system_address"]
        visit_params = []
        if date_from and date_from.strip():
            from_ts = date_from.strip() if "T" in date_from else f"{date_from.strip()}T00:00:00"
            visit_conds.append("v.timestamp >= ?")
            visit_params.append(from_ts)
        if date_to and date_to.strip():
            to_ts = date_to.strip() if "T" in date_to else f"{date_to.strip()}T23:59:59"
            visit_conds.append("v.timestamp <= ?")
            visit_params.append(to_ts)
        if len(visit_conds) > 1:
            conditions.append(f"EXISTS (SELECT 1 FROM visits v WHERE {' AND '.join(visit_conds)})")
            params.extend(visit_params)
    else:
        if date_from and date_from.strip():
            from_ts = date_from.strip() if "T" in date_from else f"{date_from.strip()}T00:00:00"
            conditions.append(f"{target_date_col} >= ?")
            params.append(from_ts)
        if date_to and date_to.strip():
            to_ts = date_to.strip() if "T" in date_to else f"{date_to.strip()}T23:59:59"
            conditions.append(f"{target_date_col} <= ?")
            params.append(to_ts)

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    allowed_sort = {
        "last_visited": "last_visited",
        "first_visited": "first_visited",
        "star_system": "star_system",
        "total_potential_value": "total_potential_value",
        "total_fss_value": "total_fss_value",
        "total_bio_signals": "total_bio_signals",
        "sol_distance_ly": "sol_distance_ly",
        "cmdr_distance_ly": "cmdr_distance_ly",
        "first_discovered_bodies": "first_discovered_bodies",
        "scanned_bodies": "scanned_bodies",
        "visit_count": "visit_count"
    }

    def build_order_clause(col_name, direction):
        if col_name == "cmdr_distance_ly":
            return f"cmdr_distance_ly IS NULL ASC, cmdr_distance_ly {direction}"
        return f"{col_name} {direction}"

    sort_col_1 = allowed_sort.get(sort_by, "total_potential_value")
    order_dir_1 = "ASC" if sort_order and sort_order.lower() == "asc" else "DESC"
    order_clauses = [build_order_clause(sort_col_1, order_dir_1)]

    if sort_by_2 and sort_by_2 in allowed_sort and sort_by_2 != sort_by:
        sort_col_2 = allowed_sort[sort_by_2]
        order_dir_2 = "ASC" if sort_order_2 and sort_order_2.lower() == "asc" else "DESC"
        order_clauses.append(build_order_clause(sort_col_2, order_dir_2))

    # Fallback deterministic order
    if "star_system" not in [sort_by, sort_by_2]:
        order_clauses.append("star_system ASC")

    order_sql = "ORDER BY " + ", ".join(order_clauses)

    # Count total
    c.execute(f"SELECT COUNT(*) as cnt FROM systems {where_clause}", params)
    total_count = c.fetchone()["cnt"]

    offset = (page - 1) * limit
    
    # Select with dynamic cmdr_distance_ly
    cmdr_dist_expr = "NULL"
    dist_params = []
    if cx is not None and cy is not None and cz is not None:
        cmdr_dist_expr = "CASE WHEN star_pos_x IS NOT NULL THEN ROUND(SQRT((star_pos_x - ?)*(star_pos_x - ?)+(star_pos_y - ?)*(star_pos_y - ?)+(star_pos_z - ?)*(star_pos_z - ?)), 1) ELSE NULL END"
        dist_params = [cx, cx, cy, cy, cz, cz]

    select_sql = f"""
        SELECT 
            systems.*,
            {cmdr_dist_expr} AS cmdr_distance_ly
        FROM systems
        {where_clause}
        {order_sql}
        LIMIT ? OFFSET ?
    """

    c.execute(select_sql, dist_params + params + [limit, offset])

    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "current_location": cur_loc,
        "systems": rows
    }

@app.get("/api/system/{system_address}")
def get_system_detail(system_address: int):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM systems WHERE system_address = ?", (system_address,))
    sys_row = c.fetchone()
    if not sys_row:
        conn.close()
        return JSONResponse({"error": "System not found"}, status_code=404)

    system_data = dict(sys_row)

    # Queue EDSM verification if not yet checked
    if not system_data.get("edsm_checked"):
        sys_name = system_data.get("star_system")
        if sys_name:
            edsm_service.queue_system_check(system_address, sys_name)

    # Fetch bodies
    c.execute("""
        SELECT * FROM bodies 
        WHERE system_address = ? 
        ORDER BY distance_from_arrival_ls ASC, body_id ASC
    """, (system_address,))
    main_star = system_data.get("main_star_type") or "F"
    bodies = []
    for r in c.fetchall():
        b = dict(r)
        b["main_star_type"] = main_star
        b["system_main_star_type"] = main_star
        b["star_system"] = system_data.get("system_name", "")

        if b.get("anomalies_json"):
            try:
                b["anomalies"] = json.loads(b["anomalies_json"])
            except Exception:
                b["anomalies"] = []
        else:
            b["anomalies"] = []

        # Always calculate latest exobiology predictions dynamically using full planet attributes & main star class
        try:
            b["exobiology"] = predict_exobiology_candidates(b)
        except Exception:
            if b.get("exobiology_predictions"):
                try:
                    b["exobiology"] = json.loads(b["exobiology_predictions"])
                except Exception:
                    b["exobiology"] = []
            else:
                b["exobiology"] = []

        if b.get("rings"):
            try:
                b["rings_list"] = json.loads(b["rings"])
            except Exception:
                b["rings_list"] = []
        else:
            b["rings_list"] = []

        if b.get("materials"):
            try:
                b["materials_list"] = json.loads(b["materials"])
            except Exception:
                b["materials_list"] = []
        else:
            b["materials_list"] = []

        bodies.append(b)

    # Fetch visits timeline
    c.execute("SELECT * FROM visits WHERE system_address = ? ORDER BY timestamp DESC", (system_address,))
    visits = [dict(r) for r in c.fetchall()]

    # Fetch scanned organics
    c.execute("SELECT * FROM scanned_organics WHERE system_address = ? ORDER BY timestamp DESC", (system_address,))
    raw_organics = [dict(r) for r in c.fetchall()]

    conn.close()

    # Process and deduplicate scanned organics
    organics_by_body = {}
    seen_species_system = {}
    stage_priority = {"log": 1, "sample": 2, "analyse": 3, "analyze": 3}

    def normalize_species(raw_sp: str) -> str:
        if not raw_sp:
            return "Unknown"
        s = raw_sp.strip()
        if " - " in s:
            s = s.split(" - ")[0].strip()
        return s

    for org in raw_organics:
        b_id = org.get("body_id")
        b_name = org.get("body_name")
        raw_sp = org.get("species_localised") or org.get("species") or org.get("genus_localised") or org.get("genus") or "Unknown"
        sp = normalize_species(raw_sp)
        stype = (org.get("scan_type") or "").lower()
        sp_priority = stage_priority.get(stype, 1)

        # Index by both body_id (int/str) and body_name for 100% robust lookup
        keys_to_index = []
        if b_id is not None:
            keys_to_index.extend([b_id, str(b_id)])
        if b_name:
            keys_to_index.append(b_name)

        for k in keys_to_index:
            if k not in organics_by_body:
                organics_by_body[k] = {}
            
            if sp not in organics_by_body[k]:
                org_copy = dict(org)
                org_copy["species_localised"] = sp
                org_copy["stage_level"] = sp_priority
                org_copy["is_completed"] = (sp_priority == 3)
                organics_by_body[k][sp] = org_copy
            else:
                existing_stage = organics_by_body[k][sp].get("stage_level", 1)
                if sp_priority >= existing_stage:
                    org_copy = dict(org)
                    org_copy["species_localised"] = sp
                    org_copy["stage_level"] = max(sp_priority, existing_stage)
                    org_copy["is_completed"] = (org_copy["stage_level"] == 3)
                    organics_by_body[k][sp] = org_copy

        # Unique per system
        if sp not in seen_species_system or sp_priority > seen_species_system[sp].get("stage_level", 1):
            org_sys = dict(org)
            org_sys["species_localised"] = sp
            org_sys["stage_level"] = sp_priority
            org_sys["is_completed"] = (sp_priority == 3)
            seen_species_system[sp] = org_sys

    system_scanned_organics = list(seen_species_system.values())
    system_bio_total_base = 0
    system_bio_total_first = 0
    system_bio_scanned_base = 0
    system_bio_scanned_first = 0
    system_bio_signals_count = 0
    system_bio_completed_count = sum(1 for s in system_scanned_organics if s.get("is_completed"))

    # Attach Exobiology information & totals to each body
    for b in bodies:
        b_id = b.get("body_id")
        b_name = b.get("body_name")
        bio_sig = b.get("bio_signals") or 0
        system_bio_signals_count += bio_sig

        # Scanned organics on this specific body
        body_scanned_map = (
            organics_by_body.get(b_id) or 
            organics_by_body.get(str(b_id)) or 
            organics_by_body.get(b_name) or 
            {}
        )

        b_scanned_list = list(body_scanned_map.values())
        b["scanned_organics"] = b_scanned_list
        b["scanned_count"] = len(b_scanned_list)
        b["scanned_species"] = [s.get("species_localised") or s.get("species") for s in b_scanned_list if s.get("species_localised") or s.get("species")]

    # Run system-wide exobiology prediction with cross-body co-occurrence & consistency weighting
    predict_system_exobiology_candidates(bodies, system_data)

    # Attach Exobiology totals and potential predictions to each body
    for b in bodies:
        b_id = b.get("body_id")
        b_name = b.get("body_name")
        bio_sig = b.get("bio_signals") or 0
        b_scanned_list = b.get("scanned_organics", [])

        completed_count = sum(1 for s in b_scanned_list if s.get("is_completed"))
        b["completed_bio_count"] = completed_count
        # A body is fully completed if it has bio signals and all are analysed, OR if bio_sig == 0 but scanned >= 1 completed
        b["is_bio_completed"] = (bio_sig > 0 and completed_count >= bio_sig) or (bio_sig == 0 and completed_count > 0)

        # Candidate exobiology predictions (filtering out already scanned species)
        scanned_species_names = {
            (s.get("species_localised") or s.get("species") or "").lower() for s in b_scanned_list
        }
        scanned_genus_names = {
            (s.get("genus_localised") or s.get("genus") or "").lower() for s in b_scanned_list
        }

        unscanned_predictions = []
        for pred in b.get("exobiology", []):
            p_sp = (pred.get("species") or "").lower()
            p_gen = (pred.get("genus") or "").lower()
            if p_sp not in scanned_species_names and p_gen not in scanned_genus_names:
                unscanned_predictions.append(pred)

        b["potential_exobiology"] = unscanned_predictions

        # Calculate body bio payouts:
        # 1. Scanned / confirmed species amount
        body_scanned_base_val = sum(s.get("base_value", 0) for s in b_scanned_list)
        body_scanned_first_val = sum(s.get("first_discovery_value", 0) for s in b_scanned_list)

        b["bio_scanned_base_value"] = body_scanned_base_val
        b["bio_scanned_first_value"] = body_scanned_first_val
        system_bio_scanned_base += body_scanned_base_val
        system_bio_scanned_first += body_scanned_first_val

        # 2. Total estimated payouts (Scanned + remaining potential slots)
        body_total_base_val = body_scanned_base_val
        body_total_first_val = body_scanned_first_val

        remaining_slots = max(0, bio_sig - len(b_scanned_list))
        for i in range(min(remaining_slots, len(unscanned_predictions))):
            pred_item = unscanned_predictions[i]
            body_total_base_val += pred_item.get("base_value", 0)
            body_total_first_val += pred_item.get("first_discovery_value", 0)

        # Fallback if no prediction matched but bio_signals > 0
        if remaining_slots > len(unscanned_predictions) and remaining_slots > 0:
            unmatched_slots = remaining_slots - len(unscanned_predictions)
            body_total_base_val += unmatched_slots * 1689700  # Default Bacterium value
            body_total_first_val += unmatched_slots * (1689700 * 5)

        b["bio_total_base_value"] = body_total_base_val
        b["bio_total_first_value"] = body_total_first_val

        system_bio_total_base += body_total_base_val
        system_bio_total_first += body_total_first_val

    # Add system-level Exobiology summary
    system_data["bio_total_base_value"] = system_bio_total_base
    system_data["bio_total_first_value"] = system_bio_total_first
    system_data["bio_scanned_base_value"] = system_bio_scanned_base
    system_data["bio_scanned_first_value"] = system_bio_scanned_first
    system_data["bio_signals_count"] = system_bio_signals_count
    system_data["bio_scanned_count"] = len(system_scanned_organics)
    system_data["bio_completed_count"] = system_bio_completed_count

    # Build hierarchy tree
    hierarchy = build_system_hierarchy(bodies)

    return {
        "system": system_data,
        "bodies": bodies,
        "hierarchy": hierarchy,
        "visits": visits,
        "organics": raw_organics,
        "system_bio_summary": {
            "total_base_value": system_bio_total_base,
            "total_first_value": system_bio_total_first,
            "scanned_base_value": system_bio_scanned_base,
            "scanned_first_value": system_bio_scanned_first,
            "total_signals": system_bio_signals_count,
            "total_scanned": len(system_scanned_organics),
            "total_completed": system_bio_completed_count
        }
    }

APP_SETTINGS_FILE = DATA_DIR / "app_settings.json"

def get_saved_journal_dir() -> Path:
    if APP_SETTINGS_FILE.exists():
        try:
            with open(APP_SETTINGS_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if cfg.get("journal_dir"):
                    p = Path(cfg["journal_dir"])
                    if p.exists() and p.is_dir():
                        return p
        except Exception:
            pass
    return DEFAULT_JOURNAL_DIR

def run_background_parse():
    global scan_state
    scan_state["is_scanning"] = True
    scan_state["current"] = 0
    scan_state["total"] = 0
    scan_state["percent"] = 0
    scan_state["filename"] = ""
    scan_state["message"] = "Scanning journal logs..."

    def cb(curr, tot, fname=None):
        scan_state["current"] = curr
        scan_state["total"] = tot
        scan_state["filename"] = fname or ""
        scan_state["percent"] = round((curr / tot) * 100, 1) if tot > 0 else 0
        if fname:
            scan_state["message"] = f"Processing {curr}/{tot} ({scan_state['percent']}%): {fname}"
        else:
            scan_state["message"] = f"Processed {curr}/{tot} journal files..."

    try:
        parser = JournalParser()
        target_dir = get_saved_journal_dir()
        tot = parser.parse_all_journals(str(target_dir), progress_callback=cb)
        scan_state["current"] = tot
        scan_state["total"] = tot
        scan_state["percent"] = 100
        scan_state["filename"] = ""
        scan_state["message"] = f"Successfully parsed {tot} journal files from {target_dir}."
    except Exception as e:
        scan_state["message"] = f"Error: {str(e)}"
    finally:
        scan_state["is_scanning"] = False
        manager.notify_update_from_thread(None)

@app.get("/api/app_settings")
def get_app_settings():
    current_dir = get_saved_journal_dir()
    return {
        "journal_dir": str(current_dir),
        "default_journal_dir": str(DEFAULT_JOURNAL_DIR),
        "is_default": str(current_dir) == str(DEFAULT_JOURNAL_DIR)
    }

@app.post("/api/app_settings")
def save_app_settings_endpoint(settings: dict):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(APP_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        start_watcher()
        return {"status": "saved", "settings": settings}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/scan_now")
def trigger_scan(background_tasks: BackgroundTasks):
    global scan_state
    if scan_state["is_scanning"]:
        return {"status": "already_scanning", "state": scan_state}
    background_tasks.add_task(run_background_parse)
    return {"status": "started", "state": scan_state}

@app.get("/api/scan_status")
def get_scan_status():
    return scan_state

# TTS Settings Persistence Endpoints
TTS_SETTINGS_FILE = DATA_DIR / "tts_settings.json"

@app.get("/api/tts_settings")
def get_tts_settings():
    default_settings = {
        "enabled": False,
        "engine": "web_speech",
        "webVoiceURI": "",
        "voicevoxSpeakerId": "3",
        "voicevoxUrl": "http://127.0.0.1:50021",
        "customText": "First discover.",
        "volume": 1.0,
        "rate": 1.0
    }
    if TTS_SETTINGS_FILE.exists():
        try:
            with open(TTS_SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_settings.update(saved)
        except Exception:
            pass
    return default_settings

@app.post("/api/tts_settings")
def save_tts_settings_endpoint(settings: dict):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(TTS_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return {"status": "saved", "settings": settings}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# Mount static files UI
ui_dir = BASE_DIR / "app" / "ui"
ui_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")

@app.get("/css/{file_path:path}")
def get_css(file_path: str):
    f = ui_dir / "css" / file_path
    if f.exists():
        return FileResponse(f)
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/js/{file_path:path}")
def get_js(file_path: str):
    f = ui_dir / "js" / file_path
    if f.exists():
        return FileResponse(f)
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/icon.png")
def get_icon():
    f = ui_dir / "icon.png"
    if f.exists():
        return FileResponse(f)
    return JSONResponse({"error": "not found"}, status_code=404)

@app.get("/")
def index():
    index_file = ui_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "UI not initialized"}
