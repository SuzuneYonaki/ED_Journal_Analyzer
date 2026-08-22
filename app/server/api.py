import json
import os
import threading
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Query, BackgroundTasks
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
    "message": "Ready"
}

watcher_instance: Optional[JournalWatcher] = None

@app.on_event("startup")
def on_startup():
    init_db()
    start_watcher()

def start_watcher():
    global watcher_instance
    if DEFAULT_JOURNAL_DIR.exists():
        if watcher_instance:
            watcher_instance.stop()
        watcher_instance = JournalWatcher(str(DEFAULT_JOURNAL_DIR))
        watcher_instance.start()

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
    sort_by: Optional[str] = "total_potential_value",
    sort_order: Optional[str] = "desc",
    sort_by_2: Optional[str] = None,
    sort_order_2: Optional[str] = "desc",
    page: int = 1,
    limit: int = 50
):
    conn = get_db_connection()
    c = conn.cursor()

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

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

    allowed_sort = {
        "last_visited": "last_visited",
        "first_visited": "first_visited",
        "star_system": "star_system",
        "total_potential_value": "total_potential_value",
        "total_fss_value": "total_fss_value",
        "total_bio_signals": "total_bio_signals",
        "sol_distance_ly": "sol_distance_ly",
        "first_discovered_bodies": "first_discovered_bodies",
        "scanned_bodies": "scanned_bodies",
        "visit_count": "visit_count"
    }
    sort_col_1 = allowed_sort.get(sort_by, "total_potential_value")
    order_dir_1 = "ASC" if sort_order and sort_order.lower() == "asc" else "DESC"

    order_clauses = [f"{sort_col_1} {order_dir_1}"]

    if sort_by_2 and sort_by_2 in allowed_sort and sort_by_2 != sort_by:
        sort_col_2 = allowed_sort[sort_by_2]
        order_dir_2 = "ASC" if sort_order_2 and sort_order_2.lower() == "asc" else "DESC"
        order_clauses.append(f"{sort_col_2} {order_dir_2}")

    # Fallback deterministic order
    if "star_system" not in [sort_by, sort_by_2]:
        order_clauses.append("star_system ASC")

    order_sql = "ORDER BY " + ", ".join(order_clauses)

    # Count total
    c.execute(f"SELECT COUNT(*) as cnt FROM systems {where_clause}", params)
    total_count = c.fetchone()["cnt"]

    offset = (page - 1) * limit
    c.execute(f"""
        SELECT * FROM systems
        {where_clause}
        {order_sql}
        LIMIT ? OFFSET ?
    """, params + [limit, offset])

    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
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
    organics = [dict(r) for r in c.fetchall()]

    conn.close()

    # Build hierarchy tree
    hierarchy = build_system_hierarchy(bodies)

    return {
        "system": system_data,
        "bodies": bodies,
        "hierarchy": hierarchy,
        "visits": visits,
        "organics": organics
    }

def run_background_parse():
    global scan_state
    scan_state["is_scanning"] = True
    scan_state["message"] = "Scanning journal logs..."

    def cb(curr, tot):
        scan_state["current"] = curr
        scan_state["total"] = tot
        scan_state["message"] = f"Processed {curr}/{tot} journal files..."

    try:
        parser = JournalParser()
        tot = parser.parse_all_journals(str(DEFAULT_JOURNAL_DIR), progress_callback=cb)
        scan_state["current"] = tot
        scan_state["total"] = tot
        scan_state["message"] = f"Successfully parsed {tot} journal files."
    except Exception as e:
        scan_state["message"] = f"Error: {str(e)}"
    finally:
        scan_state["is_scanning"] = False

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
