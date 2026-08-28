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

from app.config import DEFAULT_JOURNAL_DIR, BASE_DIR
from app.db.database import get_db_connection, init_db
from app.parser.journal_parser import JournalParser
from app.parser.watcher import JournalWatcher
from app.analyzer.orbit_analyzer import build_system_hierarchy

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

def start_watcher():
    global watcher_instance
    if DEFAULT_JOURNAL_DIR.exists():
        if watcher_instance:
            watcher_instance.stop()
        watcher_instance = JournalWatcher(
            journal_dir=str(DEFAULT_JOURNAL_DIR),
            interval=1.5,
            on_update_callback=on_journal_file_updated
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
    return last_journal_update

def get_current_cmdr_location(conn) -> Optional[dict]:
    try:
        c = conn.cursor()
        # First try: visits table joined with systems table to get coordinates of latest visit
        c.execute("""
            SELECT v.star_system, s.star_pos_x, s.star_pos_y, s.star_pos_z, v.timestamp 
            FROM visits v
            JOIN systems s ON v.system_address = s.system_address
            WHERE s.star_pos_x IS NOT NULL AND s.star_pos_y IS NOT NULL AND s.star_pos_z IS NOT NULL
            ORDER BY v.timestamp DESC LIMIT 1
        """)
        row = c.fetchone()
        if not row:
            # Second try: systems table by last_visited
            c.execute("""
                SELECT star_system, star_pos_x, star_pos_y, star_pos_z, last_visited as timestamp
                FROM systems 
                WHERE star_pos_x IS NOT NULL AND star_pos_y IS NOT NULL AND star_pos_z IS NOT NULL
                ORDER BY last_visited DESC LIMIT 1
            """)
            row = c.fetchone()
        if row:
            return {
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
def get_global_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
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
        FROM systems
    """)
    stats = dict(c.fetchone())

    # Fallback to bodies table if total_bio_signals in systems needs direct sum
    c.execute("SELECT COALESCE(SUM(bio_signals), 0) as sum_bio FROM bodies")
    bodies_bio_sum = c.fetchone()["sum_bio"]
    stats["total_bio_signals"] = max(stats.get("total_bio_signals", 0), bodies_bio_sum)

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

    # Fetch bodies
    c.execute("""
        SELECT * FROM bodies 
        WHERE system_address = ? 
        ORDER BY distance_from_arrival_ls ASC, body_id ASC
    """, (system_address,))
    bodies = []
    for r in c.fetchall():
        b = dict(r)
        if b.get("anomalies_json"):
            try:
                b["anomalies"] = json.loads(b["anomalies_json"])
            except Exception:
                b["anomalies"] = []
        else:
            b["anomalies"] = []

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

    # Deduplicate and group scanned organics by body_id / body_name
    organics_by_body = {}
    seen_species_system = set()
    system_scanned_organics = []

    for org in raw_organics:
        b_id = org.get("body_id")
        sp = org.get("species_localised") or org.get("species") or org.get("genus_localised") or org.get("genus") or "Unknown"
        
        # Unique per body
        if b_id not in organics_by_body:
            organics_by_body[b_id] = {}
        
        if sp not in organics_by_body[b_id]:
            organics_by_body[b_id][sp] = org

        # Unique per system
        if sp not in seen_species_system:
            seen_species_system.add(sp)
            system_scanned_organics.append(org)

    system_bio_total_base = 0
    system_bio_total_first = 0
    system_bio_signals_count = 0
    system_bio_scanned_count = len(system_scanned_organics)

    # Attach Exobiology information & totals to each body
    for b in bodies:
        b_id = b.get("body_id")
        b_name = b.get("body_name")
        bio_sig = b.get("bio_signals") or 0
        system_bio_signals_count += bio_sig

        # Scanned organics on this specific body
        body_scanned_map = organics_by_body.get(b_id, {})
        if not body_scanned_map and b_name in organics_by_body:
            body_scanned_map = organics_by_body[b_name]

        b_scanned_list = list(body_scanned_map.values())
        b["scanned_organics"] = b_scanned_list
        b["scanned_count"] = len(b_scanned_list)

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
        # Sum of scanned species + top predicted species for remaining bio signal slots
        body_base_val = sum(s.get("base_value", 0) for s in b_scanned_list)
        body_first_val = sum(s.get("first_discovery_value", 0) for s in b_scanned_list)

        remaining_slots = max(0, bio_sig - len(b_scanned_list))
        for i in range(min(remaining_slots, len(unscanned_predictions))):
            pred_item = unscanned_predictions[i]
            body_base_val += pred_item.get("base_value", 0)
            body_first_val += pred_item.get("first_discovery_value", 0)

        # Fallback if no prediction matched but bio_signals > 0
        if remaining_slots > len(unscanned_predictions) and remaining_slots > 0:
            unmatched_slots = remaining_slots - len(unscanned_predictions)
            body_base_val += unmatched_slots * 1689700  # Default Bacterium value
            body_first_val += unmatched_slots * (1689700 * 5)

        b["bio_total_base_value"] = body_base_val
        b["bio_total_first_value"] = body_first_val

        system_bio_total_base += body_base_val
        system_bio_total_first += body_first_val

    # Add system-level Exobiology summary
    system_data["bio_total_base_value"] = system_bio_total_base
    system_data["bio_total_first_value"] = system_bio_total_first
    system_data["bio_signals_count"] = system_bio_signals_count
    system_data["bio_scanned_count"] = system_bio_scanned_count

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
            "total_signals": system_bio_signals_count,
            "total_scanned": system_bio_scanned_count
        }
    }

def run_background_parse():
    global scan_state
    if scan_state["is_scanning"]:
        return
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
        tot = parser.parse_all_journals(str(DEFAULT_JOURNAL_DIR), progress_callback=cb)
        scan_state["current"] = tot
        scan_state["total"] = tot
        scan_state["percent"] = 100
        scan_state["filename"] = ""
        scan_state["message"] = f"Successfully parsed {tot} journal files."
    except Exception as e:
        scan_state["message"] = f"Error: {str(e)}"
    finally:
        scan_state["is_scanning"] = False
        manager.notify_update_from_thread(None)

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
