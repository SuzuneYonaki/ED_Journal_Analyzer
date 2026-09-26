import sys
import os
import io
import time
import threading
import socket
import urllib.request
import psutil
import uvicorn
import webview

# Safe standard output for GUI (noconsole) mode
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

from app.config import HOST, BASE_DIR, DATA_DIR, WEBVIEW_CACHE_DIR, APP_VERSION
from app.db.database import checkpoint_wal, init_db
from app.server.api import app

def log_msg(msg: str):
    """Outputs to stdout and app/data/run.log for diagnostics."""
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}\n"
        if sys.stdout:
            sys.stdout.write(line)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "run.log", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

def get_own_process_family():
    """Returns set of PIDs in current process hierarchy (ancestors and descendants)."""
    pids = set()
    try:
        cur = psutil.Process()
        pids.add(cur.pid)
        # Ancestors
        p = cur.parent()
        while p:
            pids.add(p.pid)
            try:
                p = p.parent()
            except Exception:
                break
        # Children
        for c in cur.children(recursive=True):
            pids.add(c.pid)
    except Exception:
        pids.add(os.getpid())
    return pids

def cleanup_stale_instances():
    """Terminates any orphan background processes of ED_Journal_Analyzer.exe and associated msedgewebview2 from previous runs."""
    family = get_own_process_family()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            pid = proc.info['pid']
            if pid not in family:
                pname = (proc.info['name'] or '').lower()
                cmdline = proc.info.get('cmdline') or []
                cmdline_str = " ".join(cmdline).lower()
                
                is_stale_app = pname == 'ed_journal_analyzer.exe'
                is_stale_webview = (pname == 'msedgewebview2.exe' and 'ed_journal_analyzer.exe' in cmdline_str)
                
                if is_stale_app or is_stale_webview:
                    log_msg(f"[Cleanup] Terminating stale instance PID {pid} ({pname})")
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.5)
                    except Exception:
                        proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass

def free_port_if_stale(port=8686):
    """Frees the specified port if it is held by an orphan ED_Journal_Analyzer process."""
    family = get_own_process_family()
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr and conn.laddr.port == port and conn.status == 'LISTEN':
                if conn.pid and conn.pid not in family:
                    try:
                        proc = psutil.Process(conn.pid)
                        pname = proc.name().lower()
                        if 'ed_journal_analyzer' in pname:
                            log_msg(f"[Port] Freeing port {port} held by stale process (PID {conn.pid})")
                            proc.terminate()
                            try:
                                proc.wait(timeout=1.5)
                            except Exception:
                                proc.kill()
                    except Exception:
                        pass
    except Exception:
        pass

class ResilientServerRunner:
    """Runs FastAPI via uvicorn with automatic port migration on conflict (8686 -> 8687...)."""
    def __init__(self, host="127.0.0.1", start_port=8686, max_tries=30):
        self.host = host
        self.start_port = start_port
        self.max_tries = max_tries
        self.active_port = None
        self.server = None
        self.ready_event = threading.Event()
        self.error = None

    def start_in_background(self):
        t = threading.Thread(target=self._run_loop, daemon=True)
        t.start()
        return t

    def _run_loop(self):
        for port in range(self.start_port, self.start_port + self.max_tries):
            # 1. Quick check: Is another server already listening?
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.settimeout(0.15)
                    s.connect((self.host, port))
                    # Already listening: port is occupied
                    log_msg(f"[Server] Port {port} is already listening, trying next port...")
                    continue
                except (ConnectionRefusedError, OSError, socket.timeout):
                    pass

            # 2. Test bind with exclusive addr use
            try:
                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
                    test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                else:
                    test_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_sock.bind((self.host, port))
                test_sock.close()
            except OSError as e:
                log_msg(f"[Server] Port {port} cannot be bound ({e}), trying next port...")
                continue

            # 3. Start uvicorn on this port
            try:
                config = uvicorn.Config(
                    app,
                    host=self.host,
                    port=port,
                    log_level="error",
                    access_log=False
                )
                self.server = uvicorn.Server(config)
                self.active_port = port
                self.ready_event.set()
                log_msg(f"[Server] Running on http://{self.host}:{port}")
                self.server.run()
                break
            except OSError as e:
                log_msg(f"[Server] Uvicorn failed to bind on port {port}: {e}")
                self.ready_event.clear()
                self.active_port = None
                continue
            except Exception as e:
                log_msg(f"[Server] Unexpected startup error: {e}")
                self.error = e
                break

def wait_for_server(url, timeout=12.0):
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
    log_msg(f"=== Starting ED Journal Analyzer (PID {os.getpid()}) ===")
    
    # 0. Ensure database tables and schema migrations are applied
    try:
        init_db()
        log_msg("[Startup] Database schema verified and initialized.")
    except Exception as e:
        log_msg(f"[Startup Error] Failed to initialize DB: {e}")

    # 1. Startup safety: Terminate stale instances
    cleanup_stale_instances()
    free_port_if_stale(8686)

    # 2. Start server with automatic port migration
    runner = ResilientServerRunner(host=HOST, start_port=8686, max_tries=30)
    runner.start_in_background()

    # Wait for runner to find a port and start
    if not runner.ready_event.wait(timeout=10.0) or runner.active_port is None:
        log_msg("[Error] Failed to initialize server port.")
        url = None
    else:
        url = f"http://{HOST}:{runner.active_port}"

    # 5. Wait until server is fully responsive via HTTP
    is_ready = False
    if url:
        is_ready = wait_for_server(url, timeout=12.0)

    use_browser = "--browser" in sys.argv

    if use_browser:
        if is_ready:
            import webbrowser
            log_msg(f"Opening in browser: {url}")
            webbrowser.open(url)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        checkpoint_wal()
        os._exit(0)
    else:
        # Create Desktop Window with pywebview using dedicated cache directory
        if is_ready:
            window = webview.create_window(
                title=f"Elite Dangerous Journal Analyzer & Exploration Orrery (v{APP_VERSION})",
                url=url,
                width=1380,
                height=840,
                min_size=(1024, 660),
                background_color="#0a0c10"
            )
        else:
            # Fallback error screen if server failed to start
            error_html = """
            <!DOCTYPE html>
            <html style="background: #0a0c10; color: #f1f5f9; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh;">
            <body style="text-align: center; max-width: 600px; padding: 20px;">
                <h1 style="color: #ef4444; font-size: 1.5rem;">⚠️ ローカルサーバーの起動に失敗しました</h1>
                <p style="color: #94a3b8; line-height: 1.6; margin-top: 12px;">
                    ポートの競合または前回のプロセスが残存している可能性があります。<br>
                    タスクマネージャーから「ED_Journal_Analyzer.exe」を終了してから再度起動してください。
                </p>
                <div style="margin-top: 24px;">
                    <button onclick="window.close()" style="background: #ff7100; color: #000; font-weight: bold; border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer;">
                        閉じる
                    </button>
                </div>
            </body>
            </html>
            """
            window = webview.create_window(
                title="Elite Dangerous Journal Analyzer - Startup Error",
                html=error_html,
                width=700,
                height=450,
                background_color="#0a0c10"
            )

        def on_window_closed():
            log_msg("[Shutdown] Window closed. Checkpointing SQLite WAL...")
            try:
                checkpoint_wal()
            except Exception:
                pass
            log_msg("[Shutdown] Complete. Exiting process.")
            os._exit(0)

        window.events.closed += on_window_closed
        try:
            webview.start(debug=False, private_mode=False, storage_path=str(WEBVIEW_CACHE_DIR))
        finally:
            try:
                checkpoint_wal()
            except Exception:
                pass
            os._exit(0)

if __name__ == "__main__":
    main()

