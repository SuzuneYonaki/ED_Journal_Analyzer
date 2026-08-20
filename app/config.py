import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "elite_journal.db"

# Default Elite Dangerous Journal Directory on Windows
DEFAULT_JOURNAL_DIR = Path(os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous"))

# Server Config
HOST = "127.0.0.1"
PORT = 8686
