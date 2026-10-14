import logging
from typing import Any, Dict, Optional

from app.addons import addon_manager
from app.db.database import get_db_connection
from app.services.spansh_service import spansh_service

logger = logging.getLogger(__name__)

_NO_RINGS = ("", "[]", '""', "null")


def fetch_ring_hotspots_if_rings(system_address: int, system_name: str) -> Optional[Dict[str, Any]]:
    """After an EDSM load/sync, ask Spansh for ring hotspots if the system has rings.

    Returns None when nothing was requested (Spansh addon off, or no rings), so an
    EDSM load never triggers a network call the user has not enabled. Failures are
    reported in the returned dict and never raise.
    """
    loaded = addon_manager.loaded.get("spansh_sync")
    if not (loaded and loaded.module and addon_manager.is_enabled("spansh_sync")):
        return None

    conn = get_db_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM bodies WHERE system_address = ? AND rings IS NOT NULL "
            f"AND rings NOT IN ({','.join('?' * len(_NO_RINGS))}) LIMIT 1",
            (system_address, *_NO_RINGS),
        ).fetchone()
        if not row:
            return None
        return spansh_service.sync_system_spansh(conn, system_address, system_name)
    except Exception as e:
        logger.warning("Spansh ring hotspot follow-up failed for %s: %s", system_name, e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
