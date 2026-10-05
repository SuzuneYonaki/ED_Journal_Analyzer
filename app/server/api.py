import json
import os
import subprocess
import sys
import threading
import time
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Union, Any
from pydantic import BaseModel
from fastapi import FastAPI, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import DEFAULT_JOURNAL_DIR, BASE_DIR, DATA_DIR, APP_VERSION
from app.db.database import (
    get_db_connection, init_db, get_mining_sites, checkpoint_wal,
    add_manual_mining_site, update_mining_site, delete_mining_site, save_or_merge_mining_site,
    get_celestial_statistics
)
from app.parser.journal_parser import JournalParser
from app.parser.watcher import JournalWatcher
from app.analyzer.orbit_analyzer import build_system_hierarchy
## NOTE: predict_exobiology_candidates / predict_system_exobiology_candidates
## are looked up via addon_manager.get_provider(...) below (see
## addons/exobiology_prediction/) instead of being imported directly, so
## disabling that addon also disables the live recompute in this file.
from app.services.edsm_service import edsm_service
from app.services.landmark_service import load_landmarks, calculate_landmark_distances
from app.services.footprint_service import footprint_service
from app.services.version_service import version_service
from app.live.rhino.note_integrator import update_body_note_in_db
from app.live.rhino.tracker import sync_body_mining_to_note, extract_all_mining_materials_for_body, extract_rhino_mining_sites
# app.services.export_service is imported inline (build_interactive_orrery in
# get_system_orrery); its export/import endpoints now live in addons/export_share/.
from app.analyzer.stellar_physics import (
    StellarPhysicsEngine,
    SystemNarrator,
    StellarDatabaseStorage,
    SystemData,
    ScanBody
)
from app.services.physics_translator import (
    translate_anomalies_list_to_ja,
    translate_narrative_report_to_ja
)

from app.addons import addon_manager

app = FastAPI(title="Elite Dangerous Journal Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/static/") or path.startswith("/css/") or path.startswith("/js/") or path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


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

# Addon discovery/import/route-mounting happens at import time, same as
# every other route in this file (all @app.get/@app.post decorators below
# run at import time too) -- so addon endpoints exist immediately, without
# depending on the ASGI startup lifecycle (e.g. bare TestClient(app) usage,
# which does not run @app.on_event("startup") unless used as `with ... as`).
# Disabled addons cost nothing beyond a manifest read. DB migrations still
# wait for on_startup below, since they require init_db() to have run first.
addon_manager.discover()
addon_manager.load_enabled(DATA_DIR / "addons")
addon_manager.mount(app)

def run_addon_migrations():
    conn = get_db_connection()
    try:
        addon_manager.run_migrations(conn)
    finally:
        conn.close()

@app.on_event("startup")
async def on_startup():
    manager.loop = asyncio.get_running_loop()
    init_db()
    run_addon_migrations()
    start_watcher()
    # TTS start + settings sync is owned by the tts addon (addons/tts/addon.py)
    # now; it registers its own startup hook via ctx.on_startup(...).
    await addon_manager.run_startup_hooks()
    # Trigger background parse automatically on startup in separate thread
    threading.Thread(target=run_background_parse, daemon=True).start()

@app.on_event("shutdown")
async def on_shutdown():
    await addon_manager.run_shutdown_hooks()

def on_journal_file_updated(file_path: Optional[str] = None):
    manager.notify_update_from_thread(file_path)

def on_journal_event(event_name: str, event_data: dict):
    manager.notify_event_from_thread(event_name, event_data)
    addon_manager.dispatch("journal_event", event_name=event_name, event_data=event_data)

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
    from app.live.telemetry import telemetry_tracker
    telemetry_tracker.set_journal_dir(str(get_saved_journal_dir()))

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

def get_cmdr_jump_stats(conn) -> dict:
    """
    Calculates total jump distance and straight-line distance from initial journal visit to current location.
    """
    res = {
        "total_jump_dist": 0.0,
        "jump_count": 0,
        "straight_dist": None,
        "initial_system": None,
        "initial_coords": None,
        "current_system": None,
        "current_coords": None
    }
    try:
        c = conn.cursor()
        # 1. Total jump distance and jump count from visits
        c.execute("""
            SELECT COALESCE(SUM(jump_dist), 0.0) as total_dist, COUNT(*) as cnt
            FROM visits
            WHERE jump_dist > 0
        """)
        row = c.fetchone()
        if row:
            res["total_jump_dist"] = round(float(row["total_dist"]), 1)
            res["jump_count"] = int(row["cnt"])

        # 2. Initial visit system and coords (earliest valid timestamp with coords)
        c.execute("""
            SELECT star_system, star_pos_x, star_pos_y, star_pos_z, timestamp
            FROM visits
            WHERE star_pos_x IS NOT NULL AND star_pos_y IS NOT NULL AND star_pos_z IS NOT NULL
            ORDER BY timestamp ASC LIMIT 1
        """)
        init_row = c.fetchone()
        if not init_row:
            c.execute("""
                SELECT star_system, star_pos_x, star_pos_y, star_pos_z, first_visited as timestamp
                FROM systems
                WHERE star_pos_x IS NOT NULL AND star_pos_y IS NOT NULL AND star_pos_z IS NOT NULL
                ORDER BY first_visited ASC LIMIT 1
            """)
            init_row = c.fetchone()

        # 3. Current visit system and coords (latest valid timestamp with coords)
        c.execute("""
            SELECT star_system, star_pos_x, star_pos_y, star_pos_z, timestamp
            FROM visits
            WHERE star_pos_x IS NOT NULL AND star_pos_y IS NOT NULL AND star_pos_z IS NOT NULL
            ORDER BY timestamp DESC LIMIT 1
        """)
        cur_row = c.fetchone()
        if not cur_row:
            c.execute("""
                SELECT star_system, star_pos_x, star_pos_y, star_pos_z, last_visited as timestamp
                FROM systems
                WHERE star_pos_x IS NOT NULL AND star_pos_y IS NOT NULL AND star_pos_z IS NOT NULL
                ORDER BY last_visited DESC LIMIT 1
            """)
            cur_row = c.fetchone()

        if init_row:
            res["initial_system"] = init_row["star_system"]
            res["initial_coords"] = [init_row["star_pos_x"], init_row["star_pos_y"], init_row["star_pos_z"]]
        if cur_row:
            res["current_system"] = cur_row["star_system"]
            res["current_coords"] = [cur_row["star_pos_x"], cur_row["star_pos_y"], cur_row["star_pos_z"]]

        if init_row and cur_row:
            dx = cur_row["star_pos_x"] - init_row["star_pos_x"]
            dy = cur_row["star_pos_y"] - init_row["star_pos_y"]
            dz = cur_row["star_pos_z"] - init_row["star_pos_z"]
            straight = (dx * dx + dy * dy + dz * dz) ** 0.5
            res["straight_dist"] = round(straight, 1)

    except Exception as err:
        logger.error(f"Failed to get cmdr jump stats: {err}")
    return res

@app.get("/api/cmdr/coordinates")
def get_cmdr_coordinates():
    """
    Returns live or latest surface coordinates from Status.json or latest journal parsing state.
    """
    from app.live.telemetry import telemetry_tracker
    
    # 1. Read live Status.json
    status = telemetry_tracker.read_status_json()
    lat = status.get("Latitude")
    lon = status.get("Longitude")
    altitude = status.get("Altitude")
    body_name = status.get("BodyName")
    
    conn = get_db_connection()
    c = conn.cursor()

    cmdr_loc = get_current_cmdr_location(conn)
    star_system = cmdr_loc.get("star_system", "") if cmdr_loc else ""
    sys_addr = cmdr_loc.get("system_address") if cmdr_loc else None

    # Fallback to journal parser in-memory or DB surface activities if Status.json has no coords
    if lat is None or lon is None:
        c.execute("""
            SELECT body_name, latitude, longitude, star_system, system_address
            FROM surface_mining_activities
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY timestamp DESC LIMIT 1
        """)
        act_row = c.fetchone()
        if act_row:
            lat = act_row["latitude"]
            lon = act_row["longitude"]
            body_name = body_name or act_row["body_name"]
            star_system = star_system or act_row["star_system"]
            sys_addr = sys_addr or act_row["system_address"]

    conn.close()

    is_surface = (lat is not None and lon is not None)
    lat_val = round(float(lat), 6) if lat is not None else None
    lon_val = round(float(lon), 6) if lon is not None else None

    formatted = ""
    if is_surface:
        b_str = body_name or (star_system + " Body" if star_system else "Surface Location")
        formatted = f"{b_str}\nLocation : {lat_val:+.4f} / {lon_val:+.4f}"

    return {
        "is_surface": is_surface,
        "has_coordinates": is_surface,
        "star_system": star_system,
        "system_address": sys_addr,
        "body_name": body_name,
        "latitude": lat_val,
        "longitude": lon_val,
        "altitude": altitude,
        "formatted": formatted,
        "formatted_text": formatted,
        "message": "" if is_surface else "No surface coordinates available (CMDR not on surface)"
    }

@app.get("/api/landmarks")
def get_landmarks_endpoint():
    """Return static galactic landmark coordinates and metadata."""
    return load_landmarks()

class BookmarkPayload(BaseModel):
    system_address: int
    body_id: int
    body_name: str
    star_system: str
    alias_name: Optional[str] = ""
    note_markdown: Optional[str] = ""

@app.get("/api/bookmark/{system_address}/{body_id}")
def get_body_bookmark(system_address: int, body_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (system_address, body_id))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return JSONResponse(status_code=404, content={"message": "Bookmark not found"})

@app.post("/api/bookmark")
def save_body_bookmark(payload: BookmarkPayload):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO body_bookmarks (system_address, body_id, body_name, star_system, alias_name, note_markdown, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(system_address, body_id) DO UPDATE SET
            body_name = excluded.body_name,
            star_system = excluded.star_system,
            alias_name = excluded.alias_name,
            note_markdown = excluded.note_markdown,
            updated_at = excluded.updated_at;
    """, (payload.system_address, payload.body_id, payload.body_name, payload.star_system, (payload.alias_name or "").strip(), payload.note_markdown or "", now, now))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Bookmark saved"}

@app.delete("/api/bookmark/{system_address}/{body_id}")
def delete_body_bookmark(system_address: int, body_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (system_address, body_id))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Bookmark deleted"}

class AppendMiningNotePayload(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    minerals: Optional[List[str]] = None

@app.post("/api/bookmark/{system_address}/{body_id}/append_mining")
def append_mining_to_bookmark_endpoint(system_address: int, body_id: int, payload: Optional[AppendMiningNotePayload] = None):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT body_name, star_system FROM bodies WHERE system_address = ? AND body_id = ?", (system_address, body_id))
        brow = c.fetchone()
        body_name = brow["body_name"] if brow else f"Body {body_id}"
        star_system = brow["star_system"] if brow else "Unknown"

        if payload and (payload.latitude is not None or payload.minerals):
            updated_note = update_body_note_in_db(
                conn=conn,
                system_address=system_address,
                body_id=body_id,
                body_name=body_name,
                star_system=star_system,
                lat=payload.latitude,
                lon=payload.longitude,
                minerals=payload.minerals or []
            )
        else:
            updated_note = sync_body_mining_to_note(
                conn=conn,
                system_address=system_address,
                body_id=body_id,
                body_name=body_name,
                star_system=star_system
            )

        c.execute("SELECT * FROM body_bookmarks WHERE system_address = ? AND body_id = ?", (system_address, body_id))
        saved = c.fetchone()
        return {
            "status": "ok",
            "bookmark": dict(saved) if saved else {"note_markdown": updated_note},
            "note_markdown": updated_note
        }
    finally:
        conn.close()

@app.get("/api/bookmarks")
def list_bookmarks(q: Optional[str] = None):
    conn = get_db_connection()
    c = conn.cursor()
    if q and q.strip():
        term = f"%{q.strip()}%"
        c.execute("SELECT * FROM body_bookmarks WHERE star_system LIKE ? OR body_name LIKE ? OR alias_name LIKE ? OR note_markdown LIKE ? ORDER BY updated_at DESC", (term, term, term, term))
    else:
        c.execute("SELECT * FROM body_bookmarks ORDER BY updated_at DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"bookmarks": rows}

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

    try:
        celestial_stats = get_celestial_statistics(conn)
        stats["celestial_counts"] = celestial_stats.get("planets", {})
    except Exception as e:
        logger.error(f"Failed to get celestial statistics for /api/stats: {e}")
        stats["celestial_counts"] = {}

    try:
        stats["current_location"] = get_current_cmdr_location(conn)
    except Exception:
        stats["current_location"] = None
    try:
        stats["jump_stats"] = get_cmdr_jump_stats(conn)
    except Exception:
        stats["jump_stats"] = None
    stats["app_version"] = APP_VERSION
    conn.close()
    return stats

@app.get("/api/stats/celestial_counts")
def get_celestial_counts():
    """
    Returns cumulative celestial body, special variant, and stellar spectral scan statistics across all systems.
    """
    stats = get_celestial_statistics()
    return {
        "status": "success",
        "data": {
            "summary": stats["summary"],
            "stars": stats["stars"],
            "planets": stats["planets"]
        }
    }

def _parse_filter_min_count(val: Any) -> int:
    """Parses filter parameter which can be bool, int, or string ('true', '2', etc.)."""
    if val is None or val is False or val == "" or str(val).lower() in ("false", "none", "0"):
        return 0
    if val is True or str(val).lower() == "true":
        return 1
    try:
        return max(0, int(val))
    except (ValueError, TypeError):
        return 0


@app.get("/api/systems")
def get_systems(
    q: Optional[str] = "",
    has_elw: Optional[Union[int, str]] = None,
    has_water_world: Optional[Union[int, str]] = None,
    has_ammonia: Optional[Union[int, str]] = None,
    has_terraformable: Optional[Union[int, str]] = None,
    has_bio: Optional[Union[int, str]] = None,
    has_landable: Optional[Union[int, str]] = None,
    has_high_g: Optional[Union[int, str]] = None,
    has_anomalies: Optional[Union[int, str]] = None,
    has_ggg: Optional[Union[int, str]] = None,
    has_first_discover: Optional[Union[int, str]] = None,
    has_landable_hmc: Optional[Union[int, str]] = None,
    has_landable_metal_rich: Optional[Union[int, str]] = None,
    has_landable_rocky: Optional[Union[int, str]] = None,
    has_landable_icy: Optional[Union[int, str]] = None,
    has_landable_rocky_ice: Optional[Union[int, str]] = None,
    has_landable_ringed: Optional[Union[int, str]] = None,
    has_mining_signals: Optional[Union[int, str]] = None,
    has_bookmarks: Optional[Union[int, str]] = None,
    is_shared: Optional[Union[int, str]] = None,
    age_lt_my: Optional[float] = None,
    age_gte_my: Optional[float] = None,
    star_types: Optional[List[str]] = Query(None),
    star_match_mode: Optional[str] = "any",
    luminosity_classes: Optional[List[str]] = Query(None),
    luminosity_match_mode: Optional[str] = "any",
    celestial_filters: Optional[List[str]] = Query(None),
    celestial_match_mode: Optional[str] = "all",
    mining_scout: Optional[str] = None,
    has_large_pad: Optional[bool] = False,
    max_arrival_dist_ls: Optional[float] = None,
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
    sort_by_3: Optional[str] = None,
    sort_order_3: Optional[str] = "desc",
    sort_mode: Optional[str] = "composite",
    page: int = 1,
    limit: int = 50
):
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='codex_entries'")
    has_codex_tbl = c.fetchone() is not None
    codex_ggg_check = """
                OR EXISTS (
                    SELECT 1 FROM codex_entries ce
                    WHERE ce.system_address = systems.system_address
                    AND ce.is_ggg = 1
                )
    """ if has_codex_tbl else ""

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
        term = f"%{q.strip()}%"
        conditions.append("""(
            systems.star_system LIKE ? OR EXISTS (
                SELECT 1 FROM body_bookmarks bb 
                WHERE bb.system_address = systems.system_address 
                AND (bb.alias_name LIKE ? OR bb.note_markdown LIKE ? OR bb.body_name LIKE ?)
            )
        )""")
        params.extend([term, term, term, term])

    c_bm = _parse_filter_min_count(has_bookmarks)
    if c_bm == 1:
        conditions.append("EXISTS (SELECT 1 FROM body_bookmarks bb WHERE bb.system_address = systems.system_address)")
    elif c_bm > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM body_bookmarks bb 
            WHERE bb.system_address = systems.system_address
        ) >= ?""")
        params.append(c_bm)

    if _parse_filter_min_count(is_shared):
        conditions.append("systems.is_shared = 1")

    c_elw = _parse_filter_min_count(has_elw)
    if c_elw == 1:
        conditions.append("systems.has_elw = 1")
    elif c_elw > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND (LOWER(b.planet_class) LIKE '%earthlike%' OR LOWER(b.planet_class) LIKE '%earth-like%')
        ) >= ?""")
        params.append(c_elw)

    c_ww = _parse_filter_min_count(has_water_world)
    if c_ww == 1:
        conditions.append("systems.has_water_world = 1")
    elif c_ww > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND LOWER(b.planet_class) LIKE '%water world%'
        ) >= ?""")
        params.append(c_ww)

    c_aw = _parse_filter_min_count(has_ammonia)
    if c_aw == 1:
        conditions.append("systems.has_ammonia = 1")
    elif c_aw > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND LOWER(b.planet_class) LIKE '%ammonia%'
        ) >= ?""")
        params.append(c_aw)

    c_tf = _parse_filter_min_count(has_terraformable)
    if c_tf == 1:
        conditions.append("systems.has_terraformable = 1")
    elif c_tf > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND LOWER(b.terraforming_state) LIKE '%terraform%'
        ) >= ?""")
        params.append(c_tf)

    c_bio = _parse_filter_min_count(has_bio)
    if c_bio == 1:
        conditions.append("systems.has_bio = 1")
    elif c_bio > 1:
        conditions.append("systems.total_bio_signals >= ?")
        params.append(c_bio)

    c_landable = _parse_filter_min_count(has_landable)
    if c_landable == 1:
        conditions.append("systems.has_landable = 1")
    elif c_landable > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1
        ) >= ?""")
        params.append(c_landable)

    # System age (million years); systems with unknown age never match either bound
    if age_lt_my is not None and age_lt_my > 0:
        conditions.append("systems.system_age_my IS NOT NULL AND systems.system_age_my < ?")
        params.append(age_lt_my)
    if age_gte_my is not None and age_gte_my > 0:
        conditions.append("systems.system_age_my IS NOT NULL AND systems.system_age_my >= ?")
        params.append(age_gte_my)

    c_hg = _parse_filter_min_count(has_high_g)
    if c_hg == 1:
        conditions.append("systems.has_high_g = 1")
    elif c_hg > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1 AND b.surface_gravity_g >= 3.0
        ) >= ?""")
        params.append(c_hg)

    c_anom = _parse_filter_min_count(has_anomalies)
    if c_anom == 1:
        conditions.append("systems.has_anomalies = 1")
    elif c_anom > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.anomalies_json IS NOT NULL 
            AND b.anomalies_json != '' 
            AND b.anomalies_json != '[]'
        ) >= ?""")
        params.append(c_anom)

    c_ggg = _parse_filter_min_count(has_ggg)
    if c_ggg == 1:
        conditions.append(f"""EXISTS (
            SELECT 1 FROM bodies b
            WHERE b.system_address = systems.system_address
            AND (
                b.anomalies_json LIKE '%Confirmed GGG%'
                {codex_ggg_check}
            )
        )""")
    elif c_ggg > 1:
        conditions.append(f"""(
            SELECT COUNT(*) FROM bodies b
            WHERE b.system_address = systems.system_address
            AND (
                b.anomalies_json LIKE '%Confirmed GGG%'
                {codex_ggg_check}
            )
        ) >= ?""")
        params.append(c_ggg)

    c_fd = _parse_filter_min_count(has_first_discover)
    if c_fd == 1:
        conditions.append("systems.has_first_discover = 1")
    elif c_fd > 1:
        conditions.append("systems.first_discovered_bodies >= ?")
        params.append(c_fd)

    # Landable Mining Target Class & Feature Filtering (ignores non-landable bodies)
    c_hmc = _parse_filter_min_count(has_landable_hmc)
    if c_hmc == 1:
        conditions.append("EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%high metal%')")
    elif c_hmc > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%high metal%'
        ) >= ?""")
        params.append(c_hmc)

    c_mr = _parse_filter_min_count(has_landable_metal_rich)
    if c_mr == 1:
        conditions.append("EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%metal rich%')")
    elif c_mr > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%metal rich%'
        ) >= ?""")
        params.append(c_mr)

    c_rocky = _parse_filter_min_count(has_landable_rocky)
    if c_rocky == 1:
        conditions.append("EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%rocky body%')")
    elif c_rocky > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%rocky body%'
        ) >= ?""")
        params.append(c_rocky)

    c_icy = _parse_filter_min_count(has_landable_icy)
    if c_icy == 1:
        conditions.append("EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%icy body%')")
    elif c_icy > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1 AND LOWER(b.planet_class) LIKE '%icy body%'
        ) >= ?""")
        params.append(c_icy)

    c_rocky_ice = _parse_filter_min_count(has_landable_rocky_ice)
    if c_rocky_ice == 1:
        conditions.append("EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.landable = 1 AND (LOWER(b.planet_class) LIKE '%rocky ice%' OR LOWER(b.planet_class) LIKE '%icy rocky%'))")
    elif c_rocky_ice > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1 AND (LOWER(b.planet_class) LIKE '%rocky ice%' OR LOWER(b.planet_class) LIKE '%icy rocky%')
        ) >= ?""")
        params.append(c_rocky_ice)

    c_ringed = _parse_filter_min_count(has_landable_ringed)
    if c_ringed == 1:
        conditions.append("EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.landable = 1 AND b.rings IS NOT NULL AND b.rings != '' AND b.rings != '[]' AND b.rings != '\"\"')")
    elif c_ringed > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.landable = 1 AND b.rings IS NOT NULL AND b.rings != '' AND b.rings != '[]' AND b.rings != '\"\"'
        ) >= ?""")
        params.append(c_ringed)

    c_mining_sig = _parse_filter_min_count(has_mining_signals)
    if c_mining_sig == 1:
        conditions.append("EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.mining_signals > 0)")
    elif c_mining_sig > 1:
        conditions.append("""(
            SELECT COUNT(*) FROM bodies b 
            WHERE b.system_address = systems.system_address 
            AND b.mining_signals > 0
        ) >= ?""")
        params.append(c_mining_sig)

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
            conditions.append(f"systems.{target_date_col} >= ?")
            params.append(from_ts)
        if date_to and date_to.strip():
            to_ts = date_to.strip() if "T" in date_to else f"{date_to.strip()}T23:59:59"
            conditions.append(f"systems.{target_date_col} <= ?")
            params.append(to_ts)

    # Star Types filtering (Stellar classification multi-search)
    # Supports "O", "N:2", "M:3", etc.
    active_star_types = {}
    if star_types:
        for st in star_types:
            for item in str(st).split(","):
                clean = item.strip()
                if not clean:
                    continue
                if ":" in clean:
                    k, v = clean.split(":", 1)
                    k = k.strip()
                    try:
                        c_val = max(1, int(v.strip()))
                    except (ValueError, TypeError):
                        c_val = 1
                else:
                    k = clean
                    c_val = 1
                if k and k not in active_star_types:
                    active_star_types[k] = c_val

    if active_star_types:
        star_type_sql_map = {
            "O": "(b.star_type = 'O')",
            "B": "(b.star_type = 'B' OR b.star_type LIKE 'B_%')",
            "A": "((b.star_type = 'A' OR b.star_type LIKE 'A_%') AND b.star_type NOT LIKE 'AeBe%')",
            "F": "(b.star_type = 'F' OR b.star_type LIKE 'F_%')",
            "G": "(b.star_type = 'G' OR b.star_type LIKE 'G_%')",
            "K": "(b.star_type = 'K' OR b.star_type LIKE 'K_%')",
            "M": "(b.star_type = 'M' OR b.star_type LIKE 'M_%')",
            "L": "(b.star_type = 'L')",
            "T": "(b.star_type = 'T')",
            "Y": "(b.star_type = 'Y')",
            "TTS": "(b.star_type = 'TTS' OR b.star_type LIKE 'TTS%')",
            "AeBe": "(b.star_type LIKE 'AeBe%')",
            "W": "(b.star_type LIKE 'W%')",
            "C": "(b.star_type LIKE 'C%' OR b.star_type = 'S' OR b.star_type = 'MS')",
            "D": "(b.star_type LIKE 'D%')",
            "N": "(b.star_type = 'N')",
            "H": "(b.star_type = 'H' OR b.star_type LIKE '%BlackHole%')",
        }

        if star_match_mode == "all":
            for st, min_cnt in active_star_types.items():
                if st in star_type_sql_map:
                    expr = star_type_sql_map[st]
                else:
                    clean_escaped = st.replace("'", "''")
                    expr = f"(b.star_type = '{clean_escaped}')"

                if min_cnt == 1:
                    conditions.append(f"EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND {expr})")
                else:
                    conditions.append(f"""(
                        SELECT COUNT(*) FROM bodies b 
                        WHERE b.system_address = systems.system_address 
                        AND {expr}
                    ) >= ?""")
                    params.append(min_cnt)
        else:
            type_or_clauses = []
            for st, min_cnt in active_star_types.items():
                if st in star_type_sql_map:
                    expr = star_type_sql_map[st]
                else:
                    clean_escaped = st.replace("'", "''")
                    expr = f"(b.star_type = '{clean_escaped}')"

                if min_cnt == 1:
                    type_or_clauses.append(f"EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND {expr})")
                else:
                    type_or_clauses.append(f"""(
                        SELECT COUNT(*) FROM bodies b 
                        WHERE b.system_address = systems.system_address 
                        AND {expr}
                    ) >= ?""")
                    params.append(min_cnt)
            if type_or_clauses:
                combined_or = " OR ".join(type_or_clauses)
                conditions.append(f"({combined_or})")

    # Luminosity / Evolutionary Stage Filtering (Independent from spectral type)
    # Supports "I", "V:2", etc.
    active_lum_classes = {}
    if luminosity_classes:
        for lc in luminosity_classes:
            for item in str(lc).split(","):
                clean = item.strip()
                if not clean:
                    continue
                if ":" in clean:
                    k, v = clean.split(":", 1)
                    k = k.strip()
                    try:
                        c_val = max(1, int(v.strip()))
                    except (ValueError, TypeError):
                        c_val = 1
                else:
                    k = clean
                    c_val = 1
                if k and k not in active_lum_classes:
                    active_lum_classes[k] = c_val

    if active_lum_classes:
        lum_sql_map = {
            # Supergiants (Ia0, Ia, Ib, Iab, I) - exclude II and IV
            "I": "(b.luminosity LIKE 'I%' AND b.luminosity NOT LIKE 'II%' AND b.luminosity NOT LIKE 'IV%')",
            # Bright Giants (II, IIa, IIb, IIab)
            "II": "(b.luminosity LIKE 'II%')",
            # Giants (III, IIIa, IIIb, IIIab)
            "III": "(b.luminosity LIKE 'III%')",
            # Subgiants (IV, IVa, IVb, IVab)
            "IV": "(b.luminosity LIKE 'IV%')",
            # Main Sequence Dwarfs (V, Va, Vb, Vab, Vz) - exclude VI
            "V": "(b.luminosity LIKE 'V%' AND b.luminosity NOT LIKE 'VI%')",
            # Subdwarfs (VI)
            "VI": "(b.luminosity = 'VI' OR b.luminosity LIKE 'VI%')",
            # Degenerate (VII, White Dwarfs, Neutron, Black Holes)
            "VII": "(b.luminosity = 'VII' OR b.star_type LIKE 'D%' OR b.star_type = 'N' OR b.star_type = 'H' OR b.star_type LIKE '%BlackHole%')",
        }

        if luminosity_match_mode == "all":
            for lc, min_cnt in active_lum_classes.items():
                if lc in lum_sql_map:
                    expr = lum_sql_map[lc]
                else:
                    clean_escaped = lc.replace("'", "''")
                    expr = f"(b.luminosity = '{clean_escaped}')"

                if min_cnt == 1:
                    conditions.append(f"EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND {expr})")
                else:
                    conditions.append(f"""(
                        SELECT COUNT(*) FROM bodies b 
                        WHERE b.system_address = systems.system_address 
                        AND {expr}
                    ) >= ?""")
                    params.append(min_cnt)
        else:
            lum_or_clauses = []
            for lc, min_cnt in active_lum_classes.items():
                if lc in lum_sql_map:
                    expr = lum_sql_map[lc]
                else:
                    clean_escaped = lc.replace("'", "''")
                    expr = f"(b.luminosity = '{clean_escaped}')"

                if min_cnt == 1:
                    lum_or_clauses.append(f"EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND {expr})")
                else:
                    lum_or_clauses.append(f"""(
                        SELECT COUNT(*) FROM bodies b 
                        WHERE b.system_address = systems.system_address 
                        AND {expr}
                    ) >= ?""")
                    params.append(min_cnt)
            if lum_or_clauses:
                combined_lum_or = " OR ".join(lum_or_clauses)
                conditions.append(f"({combined_lum_or})")

    # Celestial Bodies, Orbital & Anomaly Filters (Eccentric, Inclined, Fast, Binary, Rings, etc.)
    # Supports "eccentric", "ringed:2", etc.
    active_celestial_filters = {}
    if celestial_filters:
        for cf in celestial_filters:
            for item in str(cf).split(","):
                clean = item.strip()
                if not clean:
                    continue
                if ":" in clean:
                    k, v = clean.split(":", 1)
                    k = k.strip()
                    try:
                        c_val = max(1, int(v.strip()))
                    except (ValueError, TypeError):
                        c_val = 1
                else:
                    k = clean
                    c_val = 1
                if k and k not in active_celestial_filters:
                    active_celestial_filters[k] = c_val

    if active_celestial_filters:
        celestial_sql_map = {
            "eccentric": "(b.eccentricity >= 0.5)",
            "inclined": "(abs(b.orbital_inclination) >= 45.0 OR b.orbital_inclination > 90.0 OR b.orbital_inclination < -90.0)",
            "fast_orbit": "((b.orbital_period > 0 AND b.orbital_period <= 17280) OR (abs(b.rotation_period) > 0 AND abs(b.rotation_period) <= 7200))",
            "close_binary": "(b.star_type IS NOT NULL AND ((b.distance_from_arrival_ls > 0 AND b.distance_from_arrival_ls <= 50.0) OR (b.semi_major_axis > 0 AND (b.semi_major_axis / 299792458.0) <= 20.0)))",
            "hierarchical_binary": "(b.star_type IS NOT NULL AND b.parents LIKE '%Null%Null%')",
            "ringed": "(b.rings IS NOT NULL AND b.rings != '' AND b.rings != '[]' AND b.rings != '\"\"' AND b.rings LIKE '%Ring%')",
            "wide_ring": "(b.anomalies_json LIKE '%giant_ring%' OR (b.rings LIKE '%Ring%' AND EXISTS (SELECT 1 FROM json_each(b.rings) WHERE json_extract(value, '$.Name') NOT LIKE '%belt%' AND (json_extract(value, '$.OuterRad') >= 5000000000.0 OR (json_extract(value, '$.OuterRad') - json_extract(value, '$.InnerRad')) >= 1000000000.0))))",
            "ringed_star": "(b.star_type IS NOT NULL AND b.rings IS NOT NULL AND b.rings != '' AND b.rings != '[]' AND b.rings != '\"\"' AND b.rings LIKE '%Ring%')",
            "high_g": "(b.landable = 1 AND (b.surface_gravity_g >= 1.5 OR b.surface_gravity >= 14.71))",
            "volcanism": "(b.volcanism IS NOT NULL AND b.volcanism != '' AND LOWER(b.volcanism) != 'none')",
        }

        if celestial_match_mode == "all":
            for cf_key, min_cnt in active_celestial_filters.items():
                if cf_key in celestial_sql_map:
                    expr = celestial_sql_map[cf_key]
                    if min_cnt == 1:
                        conditions.append(f"EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND {expr})")
                    else:
                        conditions.append(f"""(
                            SELECT COUNT(*) FROM bodies b 
                            WHERE b.system_address = systems.system_address 
                            AND {expr}
                        ) >= ?""")
                        params.append(min_cnt)
        else:
            cf_or_clauses = []
            for cf_key, min_cnt in active_celestial_filters.items():
                if cf_key in celestial_sql_map:
                    expr = celestial_sql_map[cf_key]
                    if min_cnt == 1:
                        cf_or_clauses.append(f"EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND {expr})")
                    else:
                        cf_or_clauses.append(f"""(
                            SELECT COUNT(*) FROM bodies b 
                            WHERE b.system_address = systems.system_address 
                            AND {expr}
                        ) >= ?""")
                        params.append(min_cnt)
            if cf_or_clauses:
                combined_or = " OR ".join(cf_or_clauses)
                conditions.append(f"({combined_or})")

    if mining_scout:
        ms = str(mining_scout).strip().lower()
        if ms == "high":
            conditions.append("systems.mining_scout_grade = 'High'")
        elif ms == "medium":
            conditions.append("systems.mining_scout_grade = 'Medium'")
        elif ms in ["any", "all", "yes", "true", "1"]:
            conditions.append("(systems.mining_scout_grade = 'High' OR systems.mining_scout_grade = 'Medium')")

    if has_large_pad:
        conditions.append("EXISTS (SELECT 1 FROM stations st WHERE st.system_address = systems.system_address AND st.has_large_pad = 1)")

    if max_arrival_dist_ls is not None and max_arrival_dist_ls > 0:
        conditions.append("""(
            EXISTS (SELECT 1 FROM bodies b WHERE b.system_address = systems.system_address AND b.distance_from_arrival_ls > 0 AND b.distance_from_arrival_ls <= ?)
            OR EXISTS (SELECT 1 FROM stations st WHERE st.system_address = systems.system_address AND st.distance_to_arrival_ls > 0 AND st.distance_to_arrival_ls <= ?)
        )""")
        params.extend([float(max_arrival_dist_ls), float(max_arrival_dist_ls)])

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
        "visit_count": "visit_count",
        "avg_landable_radius": "avg_landable_radius",
        "main_star_type": "main_star_type",
        "rarity_score": "rarity_score"
    }

    # Gather active sort criteria
    valid_sorts = []
    for s_col, s_ord in [
        (sort_by, sort_order),
        (sort_by_2, sort_order_2),
        (sort_by_3, sort_order_3)
    ]:
        if s_col and s_col in allowed_sort and s_col != "none":
            if not any(v[0] == s_col for v in valid_sorts):
                valid_sorts.append((s_col, "asc" if s_ord and s_ord.lower() == "asc" else "desc"))

    if not valid_sorts:
        valid_sorts = [("total_potential_value", "desc")]

    # Count total matching systems
    c.execute(f"SELECT COUNT(*) as cnt FROM systems {where_clause}", params)
    total_count = c.fetchone()["cnt"]

    offset = (page - 1) * limit

    # CMDR Distance expression
    cmdr_dist_expr = "NULL"
    dist_params = []
    if cx is not None and cy is not None and cz is not None:
        cmdr_dist_expr = "CASE WHEN star_pos_x IS NOT NULL THEN ROUND(SQRT((star_pos_x - ?)*(star_pos_x - ?)+(star_pos_y - ?)*(star_pos_y - ?)+(star_pos_z - ?)*(star_pos_z - ?)), 1) ELSE NULL END"
        dist_params = [cx, cx, cy, cy, cz, cz]

    is_composite_mode = (sort_mode == "composite")

    if is_composite_mode and len(valid_sorts) > 1:
        # Weighted Composite Scoring (Method B)
        # Allocate weights based on number of active criteria
        if len(valid_sorts) == 2:
            weights = [0.65, 0.35]
        else:
            weights = [0.50, 0.35, 0.15]

        def get_score_subexpr(col_name: str, direction: str) -> str:
            if col_name == "total_potential_value":
                return "CASE WHEN stats.max_val > stats.min_val THEN (base.total_potential_value - stats.min_val) * 1.0 / (stats.max_val - stats.min_val) ELSE 1.0 END" if direction == "desc" else "CASE WHEN stats.max_val > stats.min_val THEN (stats.max_val - base.total_potential_value) * 1.0 / (stats.max_val - stats.min_val) ELSE 1.0 END"
            elif col_name == "total_fss_value":
                return "CASE WHEN stats.max_fss > stats.min_fss THEN (base.total_fss_value - stats.min_fss) * 1.0 / (stats.max_fss - stats.min_fss) ELSE 1.0 END" if direction == "desc" else "CASE WHEN stats.max_fss > stats.min_fss THEN (stats.max_fss - base.total_fss_value) * 1.0 / (stats.max_fss - stats.min_fss) ELSE 1.0 END"
            elif col_name == "total_bio_signals":
                return "CASE WHEN stats.max_bio > stats.min_bio THEN (base.total_bio_signals - stats.min_bio) * 1.0 / (stats.max_bio - stats.min_bio) ELSE (CASE WHEN base.total_bio_signals > 0 THEN 1.0 ELSE 0.0 END) END" if direction == "desc" else "CASE WHEN stats.max_bio > stats.min_bio THEN (stats.max_bio - base.total_bio_signals) * 1.0 / (stats.max_bio - stats.min_bio) ELSE 1.0 END"
            elif col_name == "first_discovered_bodies":
                return "CASE WHEN stats.max_fd > stats.min_fd THEN (base.first_discovered_bodies - stats.min_fd) * 1.0 / (stats.max_fd - stats.min_fd) ELSE (CASE WHEN base.first_discovered_bodies > 0 THEN 1.0 ELSE 0.0 END) END" if direction == "desc" else "CASE WHEN stats.max_fd > stats.min_fd THEN (stats.max_fd - base.first_discovered_bodies) * 1.0 / (stats.max_fd - stats.min_fd) ELSE 1.0 END"
            elif col_name == "cmdr_distance_ly":
                return "CASE WHEN base.cmdr_distance_ly IS NOT NULL AND stats.max_cmdr > stats.min_cmdr THEN (stats.max_cmdr - base.cmdr_distance_ly) * 1.0 / (stats.max_cmdr - stats.min_cmdr) WHEN base.cmdr_distance_ly IS NOT NULL THEN 1.0 ELSE 0.0 END" if direction == "asc" else "CASE WHEN base.cmdr_distance_ly IS NOT NULL AND stats.max_cmdr > stats.min_cmdr THEN (base.cmdr_distance_ly - stats.min_cmdr) * 1.0 / (stats.max_cmdr - stats.min_cmdr) WHEN base.cmdr_distance_ly IS NOT NULL THEN 1.0 ELSE 0.0 END"
            elif col_name == "sol_distance_ly":
                return "CASE WHEN stats.max_sol > stats.min_sol THEN (stats.max_sol - base.sol_distance_ly) * 1.0 / (stats.max_sol - stats.min_sol) ELSE 1.0 END" if direction == "asc" else "CASE WHEN stats.max_sol > stats.min_sol THEN (base.sol_distance_ly - stats.min_sol) * 1.0 / (stats.max_sol - stats.min_sol) ELSE 1.0 END"
            elif col_name == "avg_landable_radius":
                return "CASE WHEN base.avg_landable_radius > 0 AND stats.max_rad > stats.min_rad THEN (base.avg_landable_radius - stats.min_rad) * 1.0 / (stats.max_rad - stats.min_rad) WHEN base.avg_landable_radius > 0 THEN 1.0 ELSE 0.0 END" if direction == "desc" else "CASE WHEN base.avg_landable_radius > 0 AND stats.max_rad > stats.min_rad THEN (stats.max_rad - base.avg_landable_radius) * 1.0 / (stats.max_rad - stats.min_rad) WHEN base.avg_landable_radius > 0 THEN 1.0 ELSE 0.0 END"
            elif col_name == "scanned_bodies":
                return "CASE WHEN stats.max_sb > stats.min_sb THEN (base.scanned_bodies - stats.min_sb) * 1.0 / (stats.max_sb - stats.min_sb) ELSE 1.0 END" if direction == "desc" else "CASE WHEN stats.max_sb > stats.min_sb THEN (stats.max_sb - base.scanned_bodies) * 1.0 / (stats.max_sb - stats.min_sb) ELSE 1.0 END"
            elif col_name == "visit_count":
                return "CASE WHEN stats.max_vc > stats.min_vc THEN (base.visit_count - stats.min_vc) * 1.0 / (stats.max_vc - stats.min_vc) ELSE 1.0 END" if direction == "desc" else "CASE WHEN stats.max_vc > stats.min_vc THEN (stats.max_vc - base.visit_count) * 1.0 / (stats.max_vc - stats.min_vc) ELSE 1.0 END"
            elif col_name in ["last_visited", "first_visited"]:
                col = "last_visited" if col_name == "last_visited" else "first_visited"
                return f"CASE WHEN stats.max_{col} > stats.min_{col} THEN (julianday(base.{col}) - stats.min_{col}) * 1.0 / (stats.max_{col} - stats.min_{col}) ELSE 1.0 END" if direction == "desc" else f"CASE WHEN stats.max_{col} > stats.min_{col} THEN (stats.max_{col} - julianday(base.{col})) * 1.0 / (stats.max_{col} - stats.min_{col}) ELSE 1.0 END"
            elif col_name == "rarity_score":
                return "CASE WHEN stats.max_rarity > stats.min_rarity THEN (COALESCE(base.rarity_score, 10.0) - stats.min_rarity) * 1.0 / (stats.max_rarity - stats.min_rarity) ELSE 1.0 END" if direction == "desc" else "CASE WHEN stats.max_rarity > stats.min_rarity THEN (stats.max_rarity - COALESCE(base.rarity_score, 10.0)) * 1.0 / (stats.max_rarity - stats.min_rarity) ELSE 1.0 END"
            elif col_name == "main_star_type":
                spectral_score = """
                    CASE 
                        WHEN base.main_star_type = 'O' THEN 10.0
                        WHEN base.main_star_type LIKE 'B%' THEN 20.0
                        WHEN base.main_star_type LIKE 'A%' AND base.main_star_type NOT LIKE 'AeBe%' THEN 30.0
                        WHEN base.main_star_type LIKE 'F%' THEN 40.0
                        WHEN base.main_star_type LIKE 'G%' THEN 50.0
                        WHEN base.main_star_type LIKE 'K%' THEN 60.0
                        WHEN base.main_star_type LIKE 'M%' AND base.main_star_type != 'MS' THEN 70.0
                        WHEN base.main_star_type = 'L' THEN 80.0
                        WHEN base.main_star_type = 'T' THEN 90.0
                        WHEN base.main_star_type = 'Y' THEN 100.0
                        WHEN base.main_star_type LIKE 'TTS%' THEN 110.0
                        WHEN base.main_star_type LIKE 'AeBe%' THEN 120.0
                        WHEN base.main_star_type LIKE 'W%' THEN 130.0
                        WHEN base.main_star_type LIKE 'C%' OR base.main_star_type IN ('S', 'MS') THEN 140.0
                        WHEN base.main_star_type LIKE 'D%' THEN 150.0
                        WHEN base.main_star_type = 'N' THEN 160.0
                        WHEN base.main_star_type = 'H' OR base.main_star_type LIKE '%BlackHole%' THEN 170.0
                        ELSE 100.0
                    END
                """
                return f"((170.0 - ({spectral_score})) / 160.0)" if direction == "asc" else f"((({spectral_score}) - 10.0) / 160.0)"
            return "0.0"

        score_terms = []
        for i, (col, direction) in enumerate(valid_sorts):
            w = weights[i]
            sub = get_score_subexpr(col, direction)
            score_terms.append(f"({sub}) * {w}")

        score_formula = " + ".join(score_terms)

        select_sql = f"""
            WITH base AS (
                SELECT 
                    systems.*,
                    (SELECT b.luminosity FROM bodies b WHERE b.system_address = systems.system_address AND b.star_type IS NOT NULL ORDER BY b.distance_from_arrival_ls ASC, b.body_id ASC LIMIT 1) AS main_star_luminosity,
                    (SELECT b.absolute_magnitude FROM bodies b WHERE b.system_address = systems.system_address AND b.star_type IS NOT NULL ORDER BY b.distance_from_arrival_ls ASC, b.body_id ASC LIMIT 1) AS main_star_absolute_magnitude,
                    COALESCE(systems.system_age_my, (SELECT b.age_my FROM bodies b WHERE b.system_address = systems.system_address AND b.star_type IS NOT NULL AND b.age_my IS NOT NULL ORDER BY b.distance_from_arrival_ls ASC, b.body_id ASC LIMIT 1)) AS system_age_my,
                    pe.rarity_score,
                    {cmdr_dist_expr} AS cmdr_distance_ly,
                    EXISTS (
                        SELECT 1 FROM bodies b
                        WHERE b.system_address = systems.system_address
                        AND (
                            b.anomalies_json LIKE '%Confirmed GGG%'
                            {codex_ggg_check}
                        )
                    ) AS has_ggg
                FROM systems
                LEFT JOIN system_physics_evaluations pe ON systems.system_address = pe.system_address
                {where_clause}
            ),
            stats AS (
                SELECT 
                    COALESCE(MIN(total_potential_value), 0) AS min_val, COALESCE(MAX(total_potential_value), 0) AS max_val,
                    COALESCE(MIN(total_fss_value), 0) AS min_fss, COALESCE(MAX(total_fss_value), 0) AS max_fss,
                    COALESCE(MIN(total_bio_signals), 0) AS min_bio, COALESCE(MAX(total_bio_signals), 0) AS max_bio,
                    COALESCE(MIN(first_discovered_bodies), 0) AS min_fd, COALESCE(MAX(first_discovered_bodies), 0) AS max_fd,
                    COALESCE(MIN(cmdr_distance_ly), 0) AS min_cmdr, COALESCE(MAX(cmdr_distance_ly), 0) AS max_cmdr,
                    COALESCE(MIN(sol_distance_ly), 0) AS min_sol, COALESCE(MAX(sol_distance_ly), 0) AS max_sol,
                    COALESCE(MIN(CASE WHEN avg_landable_radius > 0 THEN avg_landable_radius ELSE NULL END), 0) AS min_rad,
                    COALESCE(MAX(CASE WHEN avg_landable_radius > 0 THEN avg_landable_radius ELSE NULL END), 0) AS max_rad,
                    COALESCE(MIN(scanned_bodies), 0) AS min_sb, COALESCE(MAX(scanned_bodies), 0) AS max_sb,
                    COALESCE(MIN(visit_count), 0) AS min_vc, COALESCE(MAX(visit_count), 0) AS max_vc,
                    COALESCE(MIN(COALESCE(rarity_score, 10.0)), 10.0) AS min_rarity, COALESCE(MAX(COALESCE(rarity_score, 10.0)), 10.0) AS max_rarity,
                    COALESCE(MIN(julianday(last_visited)), 0) AS min_last_visited, COALESCE(MAX(julianday(last_visited)), 0) AS max_last_visited,
                    COALESCE(MIN(julianday(first_visited)), 0) AS min_first_visited, COALESCE(MAX(julianday(first_visited)), 0) AS max_first_visited
                FROM base
            )
            SELECT 
                base.*,
                ROUND(({score_formula}) * 100.0, 1) AS composite_score
            FROM base, stats
            ORDER BY composite_score DESC, base.total_potential_value DESC, base.star_system ASC
            LIMIT ? OFFSET ?
        """
        c.execute(select_sql, dist_params + params + [limit, offset])
    else:
        # Strict hierarchical multi-column sorting (Method A / Standard)
        def build_order_clause(col_name, direction):
            if col_name == "cmdr_distance_ly":
                return f"cmdr_distance_ly IS NULL ASC, cmdr_distance_ly {direction.upper()}"
            if col_name == "avg_landable_radius":
                return f"(avg_landable_radius IS NULL OR avg_landable_radius = 0) ASC, avg_landable_radius {direction.upper()}"
            if col_name == "main_star_type":
                spectral_order = """
                    CASE 
                        WHEN main_star_type = 'O' THEN 10
                        WHEN main_star_type LIKE 'B%' THEN 20
                        WHEN main_star_type LIKE 'A%' AND main_star_type NOT LIKE 'AeBe%' THEN 30
                        WHEN main_star_type LIKE 'F%' THEN 40
                        WHEN main_star_type LIKE 'G%' THEN 50
                        WHEN main_star_type LIKE 'K%' THEN 60
                        WHEN main_star_type LIKE 'M%' AND main_star_type != 'MS' THEN 70
                        WHEN main_star_type = 'L' THEN 80
                        WHEN main_star_type = 'T' THEN 90
                        WHEN main_star_type = 'Y' THEN 100
                        WHEN main_star_type LIKE 'TTS%' THEN 110
                        WHEN main_star_type LIKE 'AeBe%' THEN 120
                        WHEN main_star_type LIKE 'W%' THEN 130
                        WHEN main_star_type LIKE 'C%' OR main_star_type IN ('S', 'MS') THEN 140
                        WHEN main_star_type LIKE 'D%' THEN 150
                        WHEN main_star_type = 'N' THEN 160
                        WHEN main_star_type = 'H' OR main_star_type LIKE '%BlackHole%' THEN 170
                        ELSE 999
                    END
                """
                return f"(main_star_type IS NULL OR main_star_type = '') ASC, {spectral_order} {direction.upper()}, main_star_type {direction.upper()}"
            if col_name == "rarity_score":
                return f"COALESCE(pe.rarity_score, 10.0) {direction.upper()}"
            return f"systems.{col_name} {direction.upper()}"

        order_clauses = [build_order_clause(col, direction) for col, direction in valid_sorts]

        # Fallback deterministic order
        if not any(v[0] == "star_system" for v in valid_sorts):
            order_clauses.append("systems.star_system ASC")

        order_sql = "ORDER BY " + ", ".join(order_clauses)

        select_sql = f"""
            SELECT 
                systems.*,
                (SELECT b.luminosity FROM bodies b WHERE b.system_address = systems.system_address AND b.star_type IS NOT NULL ORDER BY b.distance_from_arrival_ls ASC, b.body_id ASC LIMIT 1) AS main_star_luminosity,
                (SELECT b.absolute_magnitude FROM bodies b WHERE b.system_address = systems.system_address AND b.star_type IS NOT NULL ORDER BY b.distance_from_arrival_ls ASC, b.body_id ASC LIMIT 1) AS main_star_absolute_magnitude,
                COALESCE(systems.system_age_my, (SELECT b.age_my FROM bodies b WHERE b.system_address = systems.system_address AND b.star_type IS NOT NULL AND b.age_my IS NOT NULL ORDER BY b.distance_from_arrival_ls ASC, b.body_id ASC LIMIT 1)) AS system_age_my,
                pe.rarity_score,
                {cmdr_dist_expr} AS cmdr_distance_ly,
                NULL AS composite_score,
                EXISTS (
                    SELECT 1 FROM bodies b
                    WHERE b.system_address = systems.system_address
                    AND (
                        b.anomalies_json LIKE '%Confirmed GGG%'
                        {codex_ggg_check}
                    )
                ) AS has_ggg
            FROM systems
            LEFT JOIN system_physics_evaluations pe ON systems.system_address = pe.system_address
            {where_clause}
            {order_sql}
            LIMIT ? OFFSET ?
        """
        c.execute(select_sql, dist_params + params + [limit, offset])

    rows = [dict(r) for r in c.fetchall()]

    if rows:
        sys_addrs = [r["system_address"] for r in rows]
        placeholders = ",".join("?" * len(sys_addrs))
        c.execute(f"""
            SELECT system_address, body_id, body_name, planet_class, radius, surface_gravity_g, surface_temperature, rings, mining_signals
            FROM bodies
            WHERE system_address IN ({placeholders}) AND landable = 1
            ORDER BY radius DESC
        """, sys_addrs)
        summary_by_sys = {}
        for b in c.fetchall():
            s_addr = b["system_address"]
            if s_addr not in summary_by_sys:
                summary_by_sys[s_addr] = []
            p_class = b["planet_class"] or ""
            p_lower = p_class.lower()

            short_type = "Landable"
            if "high metal" in p_lower:
                short_type = "HMC"
            elif "metal rich" in p_lower:
                short_type = "Metal Rich"
            elif "rocky ice" in p_lower or "icy rocky" in p_lower:
                short_type = "Icy Rocky"
            elif "rocky" in p_lower:
                short_type = "Rocky"
            elif "icy" in p_lower:
                short_type = "Icy"

            is_ringed = bool(b["rings"] and b["rings"] != "[]" and b["rings"] != '""' and "Ring" in b["rings"])
            rad = b["radius"]
            rad_km = round(rad / 1000) if rad else None
            temp_k = round(b["surface_temperature"]) if b["surface_temperature"] is not None else None

            summary_by_sys[s_addr].append({
                "body_id": b["body_id"],
                "body_name": b["body_name"],
                "type": short_type,
                "planet_class": p_class,
                "radius": rad,
                "radius_km": rad_km,
                "gravity_g": b["surface_gravity_g"],
                "surface_temperature": b["surface_temperature"],
                "temp_k": temp_k,
                "is_ringed": is_ringed,
                "mining_signals": b["mining_signals"] or 0
            })
        for r in rows:
            r["landable_bodies"] = summary_by_sys.get(r["system_address"], [])

        # Fetch bookmarks for matching systems
        c.execute(f"""
            SELECT system_address, body_id, body_name, alias_name, note_markdown
            FROM body_bookmarks
            WHERE system_address IN ({placeholders})
            ORDER BY updated_at DESC
        """, sys_addrs)
        bms_by_sys = {}
        for bm in c.fetchall():
            s_addr = bm["system_address"]
            bms_by_sys.setdefault(s_addr, []).append({
                "body_id": bm["body_id"],
                "body_name": bm["body_name"],
                "alias_name": bm["alias_name"] or "",
                "has_note": bool(bm["note_markdown"] and bm["note_markdown"].strip()),
                "note_snippet": (bm["note_markdown"] or "").strip()[:60]
            })
        for r in rows:
            r["bookmarks"] = bms_by_sys.get(r["system_address"], [])

    for r in rows:
        if "landable_bodies" not in r:
            r["landable_bodies"] = []
        if "bookmarks" not in r:
            r["bookmarks"] = []
        lm_dists = calculate_landmark_distances(r.get("star_pos_x"), r.get("star_pos_y"), r.get("star_pos_z"))
        r.update(lm_dists)

    jump_stats = None
    try:
        jump_stats = get_cmdr_jump_stats(conn)
    except Exception:
        pass

    conn.close()

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "current_location": cur_loc,
        "jump_stats": jump_stats,
        "systems": rows
    }

## NOTE: extract_rhino_mining_sites moved to app/live/rhino/tracker.py
## (imported above) so both this file and addons/export_share/ can use it
## without a load-order dependency on this module's own definitions.

class MiningSiteCreateRequest(BaseModel):
    system_address: int
    star_system: Optional[str] = "Unknown"
    body_id: Optional[int] = None
    body_name: Optional[str] = None
    latitude: float
    longitude: float
    hotspot: Optional[str] = ""
    minerals: str
    note: Optional[str] = ""


class MiningSiteUpdateRequest(BaseModel):
    latitude: float
    longitude: float
    hotspot: Optional[str] = ""
    minerals: str
    note: Optional[str] = ""


@app.get("/api/mining_sites/{system_address}")
def api_get_mining_sites(system_address: int, body_id: Optional[int] = None):
    conn = get_db_connection()
    try:
        sites = get_mining_sites(conn, system_address, body_id)
        return {"system_address": system_address, "sites": sites}
    finally:
        conn.close()


@app.post("/api/mining_sites")
def api_create_mining_site(req: MiningSiteCreateRequest):
    conn = get_db_connection()
    try:
        site_id = add_manual_mining_site(
            conn=conn,
            system_address=req.system_address,
            star_system=req.star_system or "Unknown",
            body_id=req.body_id,
            body_name=req.body_name,
            latitude=req.latitude,
            longitude=req.longitude,
            minerals=req.minerals,
            hotspot=req.hotspot or "",
            note=req.note or ""
        )
        return {"status": "success", "site_id": site_id}
    finally:
        conn.close()


@app.put("/api/mining_sites/{site_id}")
def api_update_mining_site(site_id: int, req: MiningSiteUpdateRequest):
    conn = get_db_connection()
    try:
        ok = update_mining_site(
            conn=conn,
            site_id=site_id,
            latitude=req.latitude,
            longitude=req.longitude,
            minerals=req.minerals,
            hotspot=req.hotspot or "",
            note=req.note or ""
        )
        if not ok:
            return JSONResponse({"error": "Mining site not found"}, status_code=404)
        return {"status": "success", "site_id": site_id}
    finally:
        conn.close()


@app.delete("/api/mining_sites/{site_id}")
def api_delete_mining_site(site_id: int):
    conn = get_db_connection()
    try:
        ok = delete_mining_site(conn, site_id)
        if not ok:
            return JSONResponse({"error": "Mining site not found"}, status_code=404)
        return {"status": "success", "deleted_id": site_id}
    finally:
        conn.close()



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
    if system_data.get("edsm_factions_json"):
        try:
            system_data["edsm_factions"] = json.loads(system_data["edsm_factions_json"])
        except Exception:
            system_data["edsm_factions"] = []
    else:
        system_data["edsm_factions"] = []

    lm_dists = calculate_landmark_distances(system_data.get("star_pos_x"), system_data.get("star_pos_y"), system_data.get("star_pos_z"))
    system_data.update(lm_dists)

    # Queue EDSM verification with priority if not yet checked, or if registered on EDSM but missing bodies
    sys_name = system_data.get("star_system")
    if sys_name:
        if not system_data.get("edsm_checked"):
            edsm_service.queue_system_check(system_address, sys_name, priority=True)
        elif system_data.get("edsm_registered") == 1 and (system_data.get("edsm_body_count") or 0) > 0:
            # Check if bodies in DB are missing
            c.execute("SELECT COUNT(*) as cnt FROM bodies WHERE system_address = ?", (system_address,))
            b_cnt = c.fetchone()["cnt"]
            if b_cnt == 0:
                edsm_service.queue_system_check(system_address, sys_name, priority=True)

    # Fetch bodies
    c.execute("""
        SELECT * FROM bodies 
        WHERE system_address = ? 
        ORDER BY distance_from_arrival_ls ASC, body_id ASC
    """, (system_address,))
    main_star = system_data.get("main_star_type") or "F"
    bodies = []
    exobiology_predict_body = addon_manager.get_provider("exobiology_predict_body")
    for r in c.fetchall():
        b = dict(r)
        b["main_star_type"] = main_star
        b["system_main_star_type"] = main_star
        b["star_system"] = system_data.get("system_name", "") or system_data.get("star_system", "")
        if system_data.get("star_pos_x") is not None:
            b["star_pos_x"] = system_data.get("star_pos_x")
            b["star_pos_y"] = system_data.get("star_pos_y")
            b["star_pos_z"] = system_data.get("star_pos_z")
            b["star_pos"] = (system_data.get("star_pos_x"), system_data.get("star_pos_y"), system_data.get("star_pos_z"))

        if b.get("anomalies_json"):
            try:
                b["anomalies"] = json.loads(b["anomalies_json"])
            except Exception:
                b["anomalies"] = []
        else:
            b["anomalies"] = []

        # Always calculate latest exobiology predictions dynamically using full planet attributes & main star class
        try:
            b["exobiology"] = exobiology_predict_body(b) if exobiology_predict_body else []
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

    # Fetch surface mining activities
    c.execute("""
        SELECT * FROM surface_mining_activities 
        WHERE system_address = ? 
        ORDER BY timestamp DESC
    """, (system_address,))
    raw_mining = [dict(r) for r in c.fetchall()]

    # Fetch body bookmarks
    c.execute("SELECT * FROM body_bookmarks WHERE system_address = ?", (system_address,))
    bm_map = {b_row["body_id"]: dict(b_row) for b_row in c.fetchall()}
    for b in bodies:
        b_id = b.get("body_id")
        b["bookmark"] = bm_map.get(b_id)
    system_data["bookmarks"] = list(bm_map.values())
    system_data["bookmarks_count"] = len(bm_map)

    # Fetch physics evaluation (Stellar Physics Engine / ED_Analysys)
    c.execute("SELECT rarity_score, star_count, planet_count, anomalies_json, narrative_report, raw_features_json, evaluated_at FROM system_physics_evaluations WHERE system_address = ?", (system_address,))
    phys_row = c.fetchone()
    if not phys_row:
        try:
            storage = StellarDatabaseStorage(db_path=conn)
            storage.evaluate_and_store_from_ed_journal_db(system_address)
            c.execute("SELECT rarity_score, star_count, planet_count, anomalies_json, narrative_report, raw_features_json, evaluated_at FROM system_physics_evaluations WHERE system_address = ?", (system_address,))
            phys_row = c.fetchone()
        except Exception as p_err:
            print(f"Warning: on-demand physics evaluation failed for system {system_address}:", p_err)

    if phys_row:
        anoms_en = json.loads(phys_row["anomalies_json"])
        rep_en = phys_row["narrative_report"]
        system_data["rarity_score"] = phys_row["rarity_score"]
        system_data["physics_evaluation"] = {
            "rarity_score": phys_row["rarity_score"],
            "star_count": phys_row["star_count"],
            "planet_count": phys_row["planet_count"],
            "anomalies_en": anoms_en,
            "anomalies_ja": translate_anomalies_list_to_ja(anoms_en),
            "narrative_report_en": rep_en,
            "narrative_report_ja": translate_narrative_report_to_ja(rep_en),
            "raw_features": json.loads(phys_row["raw_features_json"]),
            "evaluated_at": phys_row["evaluated_at"]
        }
    else:
        system_data["rarity_score"] = None
        system_data["physics_evaluation"] = None

    # Fetch stations & settlements
    c.execute("""
        SELECT * FROM stations 
        WHERE system_address = ? 
        ORDER BY is_planetary ASC, distance_to_arrival_ls ASC, station_name ASC
    """, (system_address,))
    stations = [dict(r) for r in c.fetchall()]

    db_mining_sites = get_mining_sites(conn, system_address)
    conn.close()

    if db_mining_sites:
        final_mining_sites = db_mining_sites
    else:
        final_mining_sites = extract_rhino_mining_sites(raw_mining)

    # Group mining activities by body
    mining_by_body = {}
    for act in raw_mining:
        b_id = act.get("body_id")
        b_name = act.get("body_name")
        if b_id is not None:
            mining_by_body.setdefault(b_id, []).append(act)
        if b_name:
            mining_by_body.setdefault(b_name, []).append(act)

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
    exobiology_predict_system = addon_manager.get_provider("exobiology_predict_system")
    if exobiology_predict_system:
        exobiology_predict_system(bodies, system_data)

    # Attach Exobiology totals and potential predictions to each body
    for b in bodies:
        b_id = b.get("body_id")
        b_name = b.get("body_name")
        bio_sig = b.get("bio_signals") or 0
        b_scanned_list = b.get("scanned_organics", [])

        # Attach surface mining activities
        b_mining_list = (
            mining_by_body.get(b_id) or 
            mining_by_body.get(str(b_id)) or 
            mining_by_body.get(b_name) or 
            []
        )
        b["mining_activities"] = b_mining_list
        b["mining_activities_count"] = len(b_mining_list)
        b["rhino_mining_sites"] = [
            s for s in final_mining_sites
            if (b_id is not None and s.get("body_id") == b_id) or (b_name and s.get("body_name") == b_name)
        ]

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

        # Attach stations located on or orbiting this body
        b["stations"] = [st for st in stations if (st.get("body_name") and st.get("body_name") == b_name) or (st.get("body_id") is not None and st.get("body_id") == b_id)]

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

    # Collect all ring hotspots across bodies for top-level access
    system_ring_hotspots = []
    for b in bodies:
        for r in b.get("rings_list", []):
            hotspots = r.get("Hotspots")
            if not hotspots and r.get("signals"):
                hotspots = {s.get("name"): int(s.get("count", 1)) for s in r.get("signals", []) if s.get("name")}
            if hotspots:
                system_ring_hotspots.append({
                    "body_id": b.get("body_id"),
                    "body_name": b.get("body_name"),
                    "ring_name": r.get("Name") or "Ring",
                    "ring_class": r.get("RingClass"),
                    "reserve_level": b.get("reserve_level") or system_data.get("system_reserve") or "",
                    "hotspots": hotspots
                })

    # Build hierarchy tree
    hierarchy = build_system_hierarchy(bodies)

    return {
        "system": system_data,
        "bodies": bodies,
        "hierarchy": hierarchy,
        "visits": visits,
        "stations": stations,
        "organics": raw_organics,
        "mining_activities": raw_mining,
        "rhino_mining_sites": final_mining_sites,
        "ring_hotspots": system_ring_hotspots,
        "system_bio_summary": {
            "total_base_value": system_bio_total_base,
            "total_first_value": system_bio_total_first,
            "scanned_base_value": system_bio_scanned_base,
            "scanned_first_value": system_bio_scanned_first,
            "total_signals": system_bio_signals_count,
            "total_scanned": len(system_scanned_organics),
            "total_completed": system_bio_completed_count
        },
        "physics_evaluation": system_data.get("physics_evaluation")
    }

@app.get("/api/system/{system_address}/orrery")
def get_system_orrery(system_address: int, lang: str = "ja"):
    detail = get_system_detail(system_address)
    if isinstance(detail, JSONResponse):
        return detail
    sys_data = detail.get("system", {})
    bodies = detail.get("bodies", [])
    from app.services.export_service import build_interactive_orrery
    orrery_html = build_interactive_orrery(sys_data, bodies, lang=lang)
    return {"html": orrery_html}

## NOTE: POST /api/systems/{system_address}/edsm_sync and .../spansh_sync
## were moved out of this monolith into addons/edsm_sync/ and
## addons/spansh_sync/ (both enabled_by_default=true, so behavior is
## unchanged) -- see addons/README.md.

@app.get("/api/systems/{system_address}/physics")
def get_system_physics(system_address: int):
    """
    Returns astrophysical evaluation (Stellar Physics Engine / ED_Analysys)
    with dual-language (EN / JA) narrative reports, anomalies, and 2014 models.
    If not yet evaluated, runs evaluation on demand from systems/bodies.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT rarity_score, star_count, planet_count, anomalies_json, narrative_report, raw_features_json, evaluated_at FROM system_physics_evaluations WHERE system_address = ?",
        (system_address,)
    )
    phys_row = c.fetchone()
    
    if not phys_row:
        # Evaluate on-demand
        storage = StellarDatabaseStorage(db_path=conn)
        eval_result = storage.evaluate_and_store_from_ed_journal_db(system_address)
        if not eval_result:
            conn.close()
            return JSONResponse({"error": "System not found or has no scannable bodies for astrophysics evaluation"}, status_code=404)
        c.execute(
            "SELECT rarity_score, star_count, planet_count, anomalies_json, narrative_report, raw_features_json, evaluated_at FROM system_physics_evaluations WHERE system_address = ?",
            (system_address,)
        )
        phys_row = c.fetchone()

    c.execute("SELECT star_system, star_pos_x, star_pos_y, star_pos_z FROM systems WHERE system_address = ?", (system_address,))
    sys_row = c.fetchone()
    conn.close()

    if not phys_row:
        return JSONResponse({"error": "Evaluation could not be completed"}, status_code=500)

    anoms_en = json.loads(phys_row["anomalies_json"])
    rep_en = phys_row["narrative_report"]
    raw_feats = json.loads(phys_row["raw_features_json"])

    return {
        "system_address": system_address,
        "star_system": sys_row["star_system"] if sys_row else f"System {system_address}",
        "star_pos": [sys_row["star_pos_x"], sys_row["star_pos_y"], sys_row["star_pos_z"]] if sys_row and sys_row["star_pos_x"] is not None else None,
        "rarity_score": phys_row["rarity_score"],
        "star_count": phys_row["star_count"],
        "planet_count": phys_row["planet_count"],
        "anomalies_en": anoms_en,
        "anomalies_ja": translate_anomalies_list_to_ja(anoms_en),
        "narrative_report_en": rep_en,
        "narrative_report_ja": translate_narrative_report_to_ja(rep_en),
        "raw_features": raw_feats,
        "evaluated_at": phys_row["evaluated_at"]
    }

APP_SETTINGS_FILE = DATA_DIR / "app_settings.json"

def load_app_settings_data() -> dict:
    if APP_SETTINGS_FILE.exists():
        try:
            with open(APP_SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_app_settings_data(data: dict) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    current = load_app_settings_data()
    current.update(data)
    with open(APP_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
    return current

def get_saved_journal_dir() -> Path:
    cfg = load_app_settings_data()
    if cfg.get("journal_dir"):
        p = Path(cfg["journal_dir"])
        if p.exists() and p.is_dir():
            return p
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
        # Addon hooks fire for the historical batch re-parse too (but not the
        # live-update websocket broadcast, which is UI-only and would flood
        # connected clients with thousands of startup-scan events).
        addon_event_callback = lambda name, data: addon_manager.dispatch("journal_event", event_name=name, event_data=data)
        parser = JournalParser(event_callback=addon_event_callback)
        target_dir = get_saved_journal_dir()
        tot = parser.parse_all_journals(str(target_dir), progress_callback=cb)
        if not load_app_settings_data().get("star_age_backfill_done"):
            scan_state["message"] = "Backfilling star system ages..."
            parser.backfill_star_ages(str(target_dir), progress_callback=cb)
            save_app_settings_data({"star_age_backfill_done": True})
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
    cfg = load_app_settings_data()
    return {
        "journal_dir": str(current_dir),
        "default_journal_dir": str(DEFAULT_JOURNAL_DIR),
        "is_default": str(current_dir) == str(DEFAULT_JOURNAL_DIR),
        "language": cfg.get("language", "ja")
    }

@app.post("/api/app_settings")
def save_app_settings_endpoint(settings: dict):
    try:
        updated = save_app_settings_data(settings)
        if "journal_dir" in settings:
            start_watcher()
        return {"status": "saved", "settings": updated}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/addons")
def list_addons():
    """Lists every discovered addon (addons/<id>/addon.json) and its load state."""
    return {"status": "success", "data": addon_manager.list_status()}

class AddonToggleRequest(BaseModel):
    enabled: bool

@app.post("/api/addons/{addon_id}/toggle")
def toggle_addon(addon_id: str, body: AddonToggleRequest):
    if addon_id not in addon_manager.manifests:
        return JSONResponse({"error": "Addon not found"}, status_code=404)
    addon_manager.set_enabled(addon_id, body.enabled)
    return {"status": "success", "restart_required": True}

@app.post("/api/app/restart")
def restart_app():
    """Relaunches the app process (used after toggling addons, which only
    take effect on the next startup). Flushes the SQLite WAL first, then
    spawns a fresh, fully-detached process and exits this one -- pywebview's
    window runs on this same process's main thread, so exiting closes it and
    the new process opens its own window."""
    def _log_restart(msg: str):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(DATA_DIR / "run.log", "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [Restart] {msg}\n")
        except Exception:
            pass

    def _do_restart():
        time.sleep(0.5)
        try:
            checkpoint_wal()
        except Exception as e:
            _log_restart(f"WAL checkpoint failed: {e}")
        try:
            if getattr(sys, 'frozen', False):
                args = [sys.executable]
            else:
                args = [sys.executable, str(BASE_DIR / "run.py")] + sys.argv[1:]

            # PyInstaller's onefile bootloader tags this process's own
            # environment with internal bookkeeping vars (_MEIPASS2 and
            # friends) pointing at ITS extraction directory. subprocess.Popen
            # inherits the full environment by default, so the child would
            # inherit those vars, get confused about where its own bundled
            # DLLs (e.g. _sqlite3's) live, and fail to import them --
            # exactly the "DLL load failed while importing _sqlite3" crash
            # this was producing. Strip them so the child extracts and boots
            # as a genuinely fresh instance.
            child_env = os.environ.copy()
            for key in list(child_env.keys()):
                if key.startswith("_MEI") or key.startswith("_PYI"):
                    del child_env[key]

            popen_kwargs = {
                # A windowed (console=False) build has no valid OS-level
                # stdio handles; subprocess.Popen() would otherwise try to
                # inherit them and raise OSError: [WinError 6] The handle
                # is invalid. Redirect explicitly instead of inheriting.
                "stdin": subprocess.DEVNULL,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
                "close_fds": True,
                "env": child_env,
            }
            if os.name == "nt":
                # Let the child survive independently of our imminent
                # os._exit(0) without tying it to our (soon-gone) process
                # group.
                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            subprocess.Popen(args, **popen_kwargs)
            _log_restart(f"Relaunched: {args}")
        except Exception as e:
            _log_restart(f"Failed to relaunch: {e}")
            return
        os._exit(0)
    threading.Thread(target=_do_restart, daemon=True).start()
    return {"status": "restarting"}

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

@app.post("/api/scan_codex_history")
def scan_codex_history_endpoint():
    target_dir = get_saved_journal_dir()
    parser = JournalParser()
    res = parser.scan_historical_codex_entries(str(target_dir))
    return {"status": "ok", "result": res}

@app.get("/api/codex_ggg_entries")
def get_codex_ggg_entries():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT system_address, body_id, body_name, entry_id, name, name_localised,
               category, sub_category, region_name, ggg_variant, timestamp
        FROM codex_entries
        WHERE is_ggg = 1
        ORDER BY timestamp DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"total": len(rows), "entries": rows}

## NOTE: TTS settings persistence, /api/tts_settings, /api/tts/* endpoints,
## and the TTS worker start()/stop() lifecycle were moved out of this
## monolith into addons/tts/ (enabled_by_default=true, so behavior is
## unchanged) -- see addons/README.md.

MODULE_SETTINGS_FILE = DATA_DIR / "module_settings.json"

@app.get("/api/module_settings")
def get_module_settings_endpoint():
    default_settings = {
        "exobiology": True,
        "rhino": False,
        "faction": False
    }
    if MODULE_SETTINGS_FILE.exists():
        try:
            with open(MODULE_SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                default_settings.update(saved)
        except Exception:
            pass
    return default_settings

@app.post("/api/module_settings")
def save_module_settings_endpoint(settings: dict):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(MODULE_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return {"status": "saved", "settings": settings}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

# --- Safe System Export & Sharing Endpoints ---

## NOTE: Export (standalone HTML / snippet / summary PNG / .edsys package)
## and package-import endpoints were moved out of this monolith into
## addons/export_share/ (enabled_by_default=true, so behavior is unchanged)
## -- see addons/README.md. GET /api/system/{id}/orrery stays here (core UI
## view, not an export/share action).

@app.post("/api/external/import_edsm")
def import_edsm_external_system(system_name: str):
    """
    Imports and completes an unvisited system by name directly from EDSM.
    Enables viewing and analyzing star systems never visited by the player,
    while strictly restricting export/package operations.
    """
    clean_name = (system_name or "").strip()
    if not clean_name:
        return JSONResponse({"error": "星系名が指定されていません。"}, status_code=400)

    result = edsm_service.import_unvisited_system_by_name(clean_name)
    if not result.get("success"):
        return JSONResponse({"error": result.get("error", "EDSMからのインポートに失敗しました。")}, status_code=404)

    return JSONResponse(result)

## NOTE: /api/export/html, /api/export/snippet, /api/export/image,
## /api/export/open_location, /api/export/package(/save-local),
## /api/system/reveal-file, /api/import/png, /api/import/package/preview
## and /api/import/package/execute were moved out of this monolith into
## addons/export_share/ (enabled_by_default=true, so behavior is
## unchanged) -- see addons/README.md.


@app.post("/api/systems/{system_address}/toggle-shared")
def toggle_system_shared(system_address: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_shared FROM systems WHERE system_address = ?", (system_address,))
    row = c.fetchone()
    if not row:
        conn.close()
        return JSONResponse({"error": "System not found"}, status_code=404)

    new_val = 0 if row["is_shared"] == 1 else 1
    now_iso = datetime.now(timezone.utc).isoformat() if new_val == 1 else ""
    c.execute("UPDATE systems SET is_shared = ?, shared_at = ? WHERE system_address = ?", (new_val, now_iso, system_address))
    conn.commit()
    conn.close()
    return {"system_address": system_address, "is_shared": new_val}

@app.delete("/api/systems/{system_address}/shared")
def delete_shared_system(system_address: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT is_shared FROM systems WHERE system_address = ?", (system_address,))
    row = c.fetchone()
    if not row:
        conn.close()
        return JSONResponse({"error": "System not found"}, status_code=404)
    if row["is_shared"] != 1:
        conn.close()
        return JSONResponse({"error": "本人の探査データ（非共有星系）は削除できません。"}, status_code=400)

    c.execute("DELETE FROM systems WHERE system_address = ? AND is_shared = 1", (system_address,))
    c.execute("DELETE FROM bodies WHERE system_address = ?", (system_address,))
    c.execute("DELETE FROM surface_mining_activities WHERE system_address = ?", (system_address,))
    c.execute("DELETE FROM body_bookmarks WHERE system_address = ?", (system_address,))
    conn.commit()
    conn.close()
    return {"success": True, "system_address": system_address}

@app.get("/api/external_footprint")
def get_external_footprint(system_name: str = Query(..., min_length=1)):
    """
    Checks if a system has an external footprint on Inara, Spansh, or EDSM.
    Skips external queries if the system already exists in the local database.
    """
    result = footprint_service.check_system_footprint(system_name)
    return result

@app.get("/api/check_update")
def check_update(force: bool = False):
    """
    Checks GitHub Releases for a newer version of the application.
    """
    return version_service.check_update(force=force)

import jinja2

# Mount static files UI
ui_dir = BASE_DIR / "app" / "ui"
ui_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(ui_dir)), name="static")

_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(ui_dir)),
    autoescape=False
)

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

@app.get("/", response_class=HTMLResponse)
def index():
    index_file = ui_dir / "index.html"
    if index_file.exists():
        template = _jinja_env.get_template("index.html")
        return HTMLResponse(template.render(cache_bust=int(time.time())))
    return HTMLResponse("UI not initialized", status_code=404)


