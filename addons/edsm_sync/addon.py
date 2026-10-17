"""EDSM manual-sync addon: moved the single on-demand "sync this system now"
endpoint out of app/server/api.py. Note this addon only owns that one route --
edsm_service itself (auto-queueing on system view, unvisited-system import)
stays in core because it is still used directly by other core endpoints.
Behavior of this route is unchanged. Enabled by default since it was
previously an always-on core feature.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.database import get_db_connection
from app.services.edsm_service import edsm_service


def register(ctx):
    router = APIRouter()

    @router.post("/systems/{system_address}/edsm_sync")
    def sync_system_edsm(system_address: int):
        """Directly triggers a high-priority EDSM query and celestial body
        completion for this system."""
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT star_system FROM systems WHERE system_address = ?", (system_address,))
        row = c.fetchone()
        conn.close()
        if not row or not row["star_system"]:
            return JSONResponse({"error": "System not found"}, status_code=404)

        sys_name = row["star_system"]
        result = edsm_service.fetch_and_update_system_sync(system_address, sys_name)
        return JSONResponse(result)

    # Reclaims the original /api/systems/{id}/edsm_sync path (no /api/addons/... prefix)
    # so the existing frontend call site keeps working unmodified.
    ctx.add_api_router(router, prefix="/api")
