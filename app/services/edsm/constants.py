"""
Constants and API endpoints for EDSM service integration.
"""

EDSM_SYSTEM_API = "https://www.edsm.net/api-v1/system"
EDSM_BODIES_API = "https://www.edsm.net/api-system-v1/bodies"
EDSM_FACTIONS_API = "https://www.edsm.net/api-system-v1/factions"
EDSM_STATIONS_API = "https://www.edsm.net/api-system-v1/stations"

ENABLE_EDSM_BODY_COMPLETION = True
REQUEST_DELAY_SEC = 1.0
UNREGISTERED_RECHECK_COOLDOWN_SEC = 1800.0
USER_AGENT = "ED_Journal_Analyzer/v0.1.7 (External System Import)"
