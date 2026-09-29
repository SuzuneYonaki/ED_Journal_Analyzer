"""Lightweight addon (plugin) loader for ED_Journal_Analyzer.

Design goals:
- Zero cost when nothing is enabled: `discover()` only reads each addon's
  manifest JSON (cheap); the addon's Python module is imported by
  `load_enabled()` only for addons the user has actually turned on.
- Addons live as separate files under ADDONS_DIR/<addon_id>/ and never
  require editing core app/ modules to add a feature.
- A broken addon must never take down the host app: every load, hook
  dispatch and migration call is isolated with try/except and logged.

See /addons/README.md for the manifest schema and the register(ctx) contract.
"""
import importlib.util
import inspect
import json
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

MANIFEST_NAME = "addon.json"


@dataclass
class AddonManifest:
    id: str
    name: str
    version: str = "0.0.0"
    description: str = ""
    entry: str = "addon.py"
    enabled_by_default: bool = False
    ui_entry: Optional[str] = None
    path: Optional[Path] = None


@dataclass
class LoadedAddon:
    manifest: AddonManifest
    module: Any
    error: Optional[str] = None


class AddonContext:
    """Handed to each addon's register(ctx) call. This is the only surface
    an addon is allowed to use to reach into the host app."""

    def __init__(self, addon_id: str, data_dir: Path):
        self.addon_id = addon_id
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.router = None
        self.router_prefix: Optional[str] = None
        self.hooks: Dict[str, List[Callable]] = {}
        self.migrate_fn: Optional[Callable] = None
        self.startup_fn: Optional[Callable] = None
        self.shutdown_fn: Optional[Callable] = None
        self.provides: Dict[str, Callable] = {}

    def on(self, hook_name: str, callback: Callable):
        """Subscribe to a host event. Currently emitted: 'journal_event'
        (event_name: str, event_data: dict), fired for both live journal
        tailing and the historical batch re-parse."""
        self.hooks.setdefault(hook_name, []).append(callback)

    def add_api_router(self, router, prefix: Optional[str] = None):
        """A fastapi.APIRouter. By default mounted under /api/addons/<addon_id>/...
        Pass prefix="" (or any other path) to reclaim an existing route --
        e.g. an addon migrated out of core that must keep serving the same
        URL the frontend already calls (/api/systems/{id}/edsm_sync etc.)."""
        self.router = router
        self.router_prefix = prefix

    def provide(self, name: str, fn: Callable):
        """Registers this addon as the provider for a named computation slot
        that core code calls into synchronously and needs a return value
        from (e.g. "rarity_score", "exobiology_predict_body") -- unlike
        on(), which is a fire-and-forget fan-out to every subscriber, a
        provider slot is meant to have at most one addon behind it. Core
        code looks it up via AddonManager.get_provider(name) and falls back
        to a safe empty-equivalent default when nothing provides it, so
        disabling the addon turns the feature off cleanly instead of
        erroring or leaving stale data."""
        self.provides[name] = fn

    def on_migrate(self, fn: Callable):
        """fn(sqlite3.Connection) -> None. Run once at startup for every
        enabled addon. Must be additive-only (CREATE TABLE IF NOT EXISTS
        for addon-owned tables) -- never alter core tables. Join back to
        `systems` / `bodies` by system_address / body_id, the same pattern
        documented in INTEROPERABILITY_DESIGN.md."""
        self.migrate_fn = fn

    def on_startup(self, fn: Callable):
        """fn() -> None (may be async). Called once during the host's ASGI
        startup event, after core init_db() and every addon's on_migrate()
        have run. Use this for background workers / long-lived connections
        a service needs (e.g. starting a TTS playback worker)."""
        self.startup_fn = fn

    def on_shutdown(self, fn: Callable):
        """fn() -> None (may be async). Called once during the host's ASGI
        shutdown event, mirroring on_startup."""
        self.shutdown_fn = fn


class AddonManager:
    def __init__(self, addons_dir: Path, settings_path: Path):
        self.addons_dir = addons_dir
        self.settings_path = settings_path
        self.manifests: Dict[str, AddonManifest] = {}
        self.loaded: Dict[str, LoadedAddon] = {}
        self.contexts: Dict[str, AddonContext] = {}

    # -- settings: which addons the user has enabled -------------------------
    def _load_settings(self) -> dict:
        if self.settings_path.exists():
            try:
                return json.loads(self.settings_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_settings(self, data: dict):
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_enabled(self, addon_id: str) -> bool:
        settings = self._load_settings()
        if addon_id in settings:
            return bool(settings[addon_id])
        manifest = self.manifests.get(addon_id)
        return bool(manifest.enabled_by_default) if manifest else False

    def set_enabled(self, addon_id: str, enabled: bool):
        settings = self._load_settings()
        settings[addon_id] = bool(enabled)
        self._save_settings(settings)

    # -- discovery (cheap: manifest JSON only, no python import) -------------
    def discover(self) -> Dict[str, AddonManifest]:
        self.manifests = {}
        if not self.addons_dir.exists():
            return self.manifests
        for entry in sorted(self.addons_dir.iterdir()):
            if not entry.is_dir():
                continue
            manifest_file = entry / MANIFEST_NAME
            if not manifest_file.exists():
                continue
            try:
                raw = json.loads(manifest_file.read_text(encoding="utf-8"))
                manifest = AddonManifest(
                    id=raw.get("id", entry.name),
                    name=raw.get("name", entry.name),
                    version=raw.get("version", "0.0.0"),
                    description=raw.get("description", ""),
                    entry=raw.get("entry", "addon.py"),
                    enabled_by_default=bool(raw.get("enabled_by_default", False)),
                    ui_entry=raw.get("ui_entry"),
                    path=entry,
                )
                self.manifests[manifest.id] = manifest
            except Exception as e:
                print(f"[Addons] Failed to read manifest {manifest_file}: {e}")
        return self.manifests

    # -- loading (only for enabled addons) ------------------------------------
    def load_enabled(self, data_root: Path):
        for addon_id, manifest in self.manifests.items():
            if not self.is_enabled(addon_id):
                continue
            self._load_one(manifest, data_root)

    def _load_one(self, manifest: AddonManifest, data_root: Path):
        entry_path = manifest.path / manifest.entry
        if not entry_path.exists():
            print(f"[Addons] '{manifest.id}': entry file not found: {entry_path}")
            self.loaded[manifest.id] = LoadedAddon(manifest=manifest, module=None, error="entry file not found")
            return
        ctx = AddonContext(manifest.id, data_root / manifest.id)
        try:
            module_name = f"_addon_{manifest.id}"
            spec = importlib.util.spec_from_file_location(module_name, entry_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            register_fn = getattr(module, "register", None)
            if register_fn is None:
                raise AttributeError("addon module has no register(ctx) function")
            register_fn(ctx)
            self.loaded[manifest.id] = LoadedAddon(manifest=manifest, module=module)
            self.contexts[manifest.id] = ctx
            print(f"[Addons] Loaded '{manifest.id}' v{manifest.version}")
        except Exception as e:
            traceback.print_exc()
            self.loaded[manifest.id] = LoadedAddon(manifest=manifest, module=None, error=str(e))

    # -- host-side integration -------------------------------------------------
    def get_provider(self, name: str) -> Optional[Callable]:
        """Returns the callable registered via ctx.provide(name, fn) by
        whichever enabled addon provides it, or None if none does (core
        code must supply its own safe default in that case)."""
        for ctx in self.contexts.values():
            if name in ctx.provides:
                return ctx.provides[name]
        return None

    def dispatch(self, hook_name: str, **kwargs):
        """Fan a host event out to every loaded addon subscribed to it.
        A failing addon is logged and skipped; it never breaks the host."""
        for addon_id, ctx in self.contexts.items():
            for cb in ctx.hooks.get(hook_name, []):
                try:
                    cb(**kwargs)
                except Exception:
                    print(f"[Addons] '{addon_id}' hook '{hook_name}' raised:")
                    traceback.print_exc()

    async def run_startup_hooks(self):
        for addon_id, ctx in self.contexts.items():
            if ctx.startup_fn is None:
                continue
            try:
                result = ctx.startup_fn()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                print(f"[Addons] '{addon_id}' startup hook failed:")
                traceback.print_exc()

    async def run_shutdown_hooks(self):
        for addon_id, ctx in self.contexts.items():
            if ctx.shutdown_fn is None:
                continue
            try:
                result = ctx.shutdown_fn()
                if inspect.isawaitable(result):
                    await result
            except Exception:
                print(f"[Addons] '{addon_id}' shutdown hook failed:")
                traceback.print_exc()

    def run_migrations(self, conn):
        for addon_id, ctx in self.contexts.items():
            if ctx.migrate_fn is None:
                continue
            try:
                ctx.migrate_fn(conn)
            except Exception:
                print(f"[Addons] '{addon_id}' migration failed:")
                traceback.print_exc()
        try:
            conn.commit()
        except Exception:
            pass

    def mount(self, app):
        """Registers each addon's FastAPI router under /api/addons/<id>,
        and serves every addon folder's static files under /addons/<id>/..."""
        from fastapi.staticfiles import StaticFiles

        for addon_id, ctx in self.contexts.items():
            if ctx.router is not None:
                prefix = ctx.router_prefix if ctx.router_prefix is not None else f"/api/addons/{addon_id}"
                app.include_router(ctx.router, prefix=prefix, tags=[f"addon:{addon_id}"])
        if self.addons_dir.exists():
            app.mount("/addons", StaticFiles(directory=str(self.addons_dir)), name="addons_static")

    def list_status(self) -> List[dict]:
        out = []
        for addon_id, manifest in self.manifests.items():
            loaded = self.loaded.get(addon_id)
            is_loaded = loaded is not None and loaded.error is None
            out.append({
                "id": addon_id,
                "name": manifest.name,
                "version": manifest.version,
                "description": manifest.description,
                "enabled": self.is_enabled(addon_id),
                "loaded": is_loaded,
                "error": loaded.error if loaded else None,
                "ui_entry": f"/addons/{addon_id}/{manifest.ui_entry}" if (manifest.ui_entry and is_loaded) else None,
            })
        return out
