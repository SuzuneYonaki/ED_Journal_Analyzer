import sys
import os
import io
import time
import threading
import uvicorn
import webview

# Safe standard output for GUI (noconsole) mode
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

from app.config import HOST, PORT, BASE_DIR
from app.server.api import app

def run_server():
    # Run uvicorn without crashing when stdout/stderr are redirected
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="error",
        access_log=False
    )

def main():
    use_browser = "--browser" in sys.argv

    # Start FastAPI server in a background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to initialize
    time.sleep(1.0)
    url = f"http://{HOST}:{PORT}"

    if use_browser:
        import webbrowser
        print(f"Opening in browser: {url}")
        webbrowser.open(url)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
    else:
        # Create Desktop Window with pywebview
        icon_path = str(BASE_DIR / "app" / "ui" / "icon.png")
        window = webview.create_window(
            title="Elite Dangerous Journal Analyzer & Exploration Orrery",
            url=url,
            width=1400,
            height=900,
            min_size=(1024, 700),
            background_color="#0a0c10"
        )
        webview.start(debug=False)

if __name__ == "__main__":
    main()
