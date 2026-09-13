"""
EDSM Integration Package.
Provides rate-limited API access, background queue management, and modular importers for
systems, bodies, stations, and aggregated statistics.
"""

from app.services.edsm.constants import (
    EDSM_SYSTEM_API,
    EDSM_BODIES_API,
    EDSM_FACTIONS_API,
    EDSM_STATIONS_API,
    ENABLE_EDSM_BODY_COMPLETION,
    REQUEST_DELAY_SEC,
    UNREGISTERED_RECHECK_COOLDOWN_SEC,
    USER_AGENT
)
from app.services.edsm.client import EDSMClient
from app.services.edsm.body_importer import extract_star_type, import_and_complete_bodies
from app.services.edsm.station_importer import import_and_complete_stations
from app.services.edsm.stats_aggregator import update_system_aggregated_stats
from app.services.edsm.system_importer import (
    import_unvisited_system_by_name,
    fetch_and_update_system
)

__all__ = [
    "EDSM_SYSTEM_API",
    "EDSM_BODIES_API",
    "EDSM_FACTIONS_API",
    "EDSM_STATIONS_API",
    "ENABLE_EDSM_BODY_COMPLETION",
    "REQUEST_DELAY_SEC",
    "UNREGISTERED_RECHECK_COOLDOWN_SEC",
    "USER_AGENT",
    "EDSMClient",
    "extract_star_type",
    "import_and_complete_bodies",
    "import_and_complete_stations",
    "update_system_aggregated_stats",
    "import_unvisited_system_by_name",
    "fetch_and_update_system",
]
