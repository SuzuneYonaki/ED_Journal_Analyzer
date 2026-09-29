"""Sample addon: proves the addon loader, hook dispatch, DB migration and
API-router mounting all work end to end. Disabled by default -- enable via
POST /api/addons/sample_hello/toggle {"enabled": true} and restart.
"""
from fastapi import APIRouter

_state = {"scan_events_seen": 0}


def _on_journal_event(event_name: str, event_data: dict):
    if event_name == "Scan":
        _state["scan_events_seen"] += 1


def _migrate(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS addon_sample_hello_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)


def register(ctx):
    ctx.on_migrate(_migrate)
    ctx.on("journal_event", _on_journal_event)

    router = APIRouter()

    @router.get("/ping")
    def ping():
        return {"status": "ok", "addon": ctx.addon_id}

    @router.get("/status")
    def status():
        return {"scan_events_seen": _state["scan_events_seen"]}

    ctx.add_api_router(router)
