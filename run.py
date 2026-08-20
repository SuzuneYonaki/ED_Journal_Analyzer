import sys
import time
import threading
import webbrowser
import uvicorn
from pathlib import Path

from app.config import HOST, PORT, DEFAULT_JOURNAL_DIR
from app.db.database import init_db
from app.parser.journal_parser import JournalParser

def start_server():
    from app.server.api import app
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")

def initial_quick_sync():
    """Perform quick sync of newest journals on startup if DB is fresh."""
    init_db()
    if DEFAULT_JOURNAL_DIR.exists():
        print(f"[Init] Found Elite Dangerous journal directory at: {DEFAULT_JOURNAL_DIR}")
        parser = JournalParser()
        # Parse initial logs in background or quick batch
        print("[Init] Syncing journal logs...")
        parser.parse_all_journals(str(DEFAULT_JOURNAL_DIR))
        print("[Init] Initial journal sync complete.")

def main():
    print("=" * 60)
    print("  Elite Dangerous Journal Analyzer & Exploration Orrery")
    print("=" * 60)

    # Run initial sync before launching UI
    initial_quick_sync()

    # Start FastAPI backend in a background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Wait for server to warm up
    time.sleep(1.0)
    url = f"http://{HOST}:{PORT}"
    print(f"[Server] Running at {url}")

    # Launch Desktop GUI via pywebview if available, else fallback to browser
    use_webview = True
    if "--browser" in sys.argv:
        use_webview = False

    if use_webview:
        try:
            import webview
            print("[GUI] Starting Desktop Window...")
            webview.create_window(
                "Elite Dangerous Journal Analyzer & Exploration Orrery",
                url,
                width=1400,
                height=900,
                min_size=(1024, 700)
            )
            webview.start()
            return
        except Exception as e:
            print(f"[GUI] Webview not available ({e}), falling back to default browser...")

    print(f"[Browser] Opening {url} in your default browser...")
    webbrowser.open(url)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()
