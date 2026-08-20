import os
import sys
from pathlib import Path

# PyInstaller one-file extraction support
if getattr(sys, 'frozen', False):
    EXE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', EXE_DIR))
    DATA_DIR = EXE_DIR / "data"
else:
    RESOURCE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = RESOURCE_DIR / "data"

BASE_DIR = RESOURCE_DIR
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "elite_journal.db"

# Default Elite Dangerous Journal Directory on Windows
DEFAULT_JOURNAL_DIR = Path(os.path.expanduser("~/Saved Games/Frontier Developments/Elite Dangerous"))

# Server Config
HOST = "127.0.0.1"
PORT = 8686
