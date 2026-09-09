import sys
import os
import io
import time
import threading
import socket
import urllib.request
import uvicorn
import webview

# Safe standard output for GUI (noconsole) mode
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

from app.config import HOST, BASE_DIR, DATA_DIR
from app.server.api import app

def find_free_port(start_port=8686):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                return port
            except OSError:
                continue
    return start_port

def wait_for_server(url, timeout=10.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/api/scan_status", timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False

def main():
    port = find_free_port(8686)
    use_browser = "--browser" in sys.argv

    # Start FastAPI server in a background thread
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(
            app,
            host=HOST,
            port=port,
            log_level="error",
            access_log=False
        ),
        daemon=True
    )
    server_thread.start()

    url = f"http://{HOST}:{port}"

    # Wait until server is fully responsive
    wait_for_server(url, timeout=8.0)

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
            title="Elite Dangerous Journal Analyzer & Exploration Orrery (v0.0.5)",
            url=url,
            width=1400,
            height=900,
            min_size=(1024, 700),
            background_color="#0a0c10"
        )
        storage_dir = DATA_DIR / "webview"
        storage_dir.mkdir(parents=True, exist_ok=True)
        webview.start(debug=False, private_mode=False, storage_path=str(storage_dir))

if __name__ == "__main__":
    main()
