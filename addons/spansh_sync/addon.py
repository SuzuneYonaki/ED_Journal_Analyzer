"""Spansh Sync addon: moved out of app/server/api.py so the Spansh
integration is an independent, toggleable file instead of being baked into
the core API monolith. Behavior is unchanged -- same route, same response
shape. Enabled by default (enabled_by_default=true) since it was previously
an always-on core feature; disabling it only removes this one endpoint.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.database import get_db_connection
from app.services.spansh_service import spansh_service


def register(ctx):
    router = APIRouter()

    @router.post("/systems/{system_address}/spansh_sync")
    def sync_system_spansh(system_address: int):
        """Triggers a Spansh query for ring DSS hotspots and planetary mining
        locations, updating celestial bodies and markdown notes."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT star_system FROM systems WHERE system_address = ?", (system_address,))
        row = c.fetchone()
        if not row or not row["star_system"]:
            conn.close()
            return JSONResponse({"error": "System not found"}, status_code=404)

        sys_name = row["star_system"]
        result = spansh_service.sync_system_spansh(conn, system_address, sys_name)
        conn.close()
        return JSONResponse(result)

    # Reclaims the original /api/systems/{id}/spansh_sync path (no /api/addons/... prefix)
    # so the existing frontend call site keeps working unmodified.
    ctx.add_api_router(router, prefix="/api")
