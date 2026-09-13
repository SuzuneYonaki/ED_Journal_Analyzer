"""
EDSM (Elite Dangerous Star Map) API Integration Service Facade.
Provides asynchronous rate-limited queries to query system registration, discovery status,
and celestial body discoveries.
Results are persisted into the local SQLite database as a permanent cache.
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
    import_unvisited_system_by_name as _import_unvisited_system_by_name,
    fetch_and_update_system as _fetch_and_update_system_func
)

# Backward-compatibility aliases
_extract_star_type = extract_star_type


class EDSMService:
    def __init__(self):
        self.client = EDSMClient(processor_callback=self._fetch_and_update_system)

    @property
    def high_priority_queue(self):
        return self.client.high_priority_queue

    @property
    def low_priority_queue(self):
        return self.client.low_priority_queue

    @property
    def queued_systems(self):
        return self.client.queued_systems

    @property
    def priority_systems(self):
        return self.client.priority_systems

    @property
    def recent_unregistered_cache(self):
        return self.client.recent_unregistered_cache

    @property
    def last_request_time(self):
        return self.client.last_request_time

    @last_request_time.setter
    def last_request_time(self, val):
        self.client.last_request_time = val

    @property
    def is_running(self):
        return self.client.is_running

    def queue_system_check(self, system_address: int, system_name: str, force_recheck: bool = False, priority: bool = False):
        return self.client.queue_system_check(system_address, system_name, force_recheck=force_recheck, priority=priority)

    def _throttle_delay(self):
        return self.client.throttle_delay()

    def _mark_checked_unregistered(self, system_address: int):
        return self.client.mark_checked_unregistered(system_address)

    def fetch_and_update_system_sync(self, system_address: int, system_name: str) -> dict:
        self.client.throttle_delay()
        return self._fetch_and_update_system(system_address, system_name)

    def import_unvisited_system_by_name(self, system_name: str) -> dict:
        # Queries EDSM_SYSTEM_API with showId=1 and imports celestial bodies
        return _import_unvisited_system_by_name(
            self.client,
            system_name,
            body_importer_func=self._import_and_complete_bodies,
            station_importer_func=self._import_and_complete_stations,
            stats_aggregator_func=self._update_system_aggregated_stats
        )

    def _fetch_and_update_system(self, system_address: int, system_name: str) -> dict:
        # Queries EDSM_SYSTEM_API with showId=1 and updates system discoveries in SQLite
        return _fetch_and_update_system_func(
            self.client,
            system_address,
            system_name,
            body_importer_func=self._import_and_complete_bodies,
            station_importer_func=self._import_and_complete_stations,
            stats_aggregator_func=self._update_system_aggregated_stats
        )

    def _import_and_complete_stations(self, conn, system_address: int, system_name: str, is_uninhabited: bool = False) -> int:
        return import_and_complete_stations(self.client, conn, system_address, system_name, is_uninhabited=is_uninhabited)

    def _import_and_complete_bodies(self, conn, system_address: int, star_system: str, bodies_list: list) -> int:
        return import_and_complete_bodies(conn, system_address, star_system, bodies_list)

    def _update_system_aggregated_stats(self, conn, system_address: int):
        return update_system_aggregated_stats(conn, system_address)


# Global singleton instance
edsm_service = EDSMService()
