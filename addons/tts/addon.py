"""TTS Alerts addon: moved the VOICEVOX/Web-Speech backend wiring out of
app/server/api.py -- settings persistence, the /api/tts* REST endpoints, and
the worker start()/stop() lifecycle (previously called directly inside
api.py's on_startup/on_shutdown).

Left in core (unchanged) on purpose:
- app/services/tts_service.py -- the TTSService class/singleton itself.
- app/parser/journal_parser.py -- it calls tts_service.enqueue_speak(...)
  directly for GGG / high-value-bio alerts, and reads tts_settings.json
  itself (get_ggg_tts_config / get_high_bio_tts_config) via its own
  DATA_DIR-derived path, independent of whichever module manages the file.
  enqueue_speak() is safe to call even if this addon's start() was never
  run (it just queues; nothing crashes -- it is simply never spoken).

Enabled by default since this was previously an always-on core feature;
disabling it removes the settings/REST endpoints and stops the playback
worker, but does not touch the GGG/exobiology detection logic itself.
"""
import json
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import DATA_DIR
from app.services.tts_service import tts_service

TTS_SETTINGS_FILE = DATA_DIR / "tts_settings.json"


def sync_tts_settings_to_service(settings: dict):
    """Synchronizes dict settings (camelCase or snake_case) to backend tts_service."""
    update_data = {}
    if "enabled" in settings:
        update_data["enabled"] = bool(settings["enabled"])

    url = settings.get("voicevoxUrl") or settings.get("voicevox_url")
    if url is not None:
        update_data["voicevox_url"] = str(url).rstrip("/")

    sp_id = settings.get("voicevoxSpeakerId") or settings.get("speaker_id")
    if sp_id is not None:
        try:
            update_data["speaker_id"] = int(sp_id)
        except (ValueError, TypeError):
            pass

    speed = settings.get("rate") or settings.get("speed_scale")
    if speed is not None:
        try:
            update_data["speed_scale"] = float(speed)
        except (ValueError, TypeError):
            pass

    vol = settings.get("volume") or settings.get("volume_scale")
    if vol is not None:
        try:
            update_data["volume_scale"] = float(vol)
        except (ValueError, TypeError):
            pass

    if update_data:
        tts_service.update_config(update_data)


class TTSSpeakRequest(BaseModel):
    text: str
    priority: Optional[bool] = False


class TTSConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    voicevox_url: Optional[str] = None
    speaker_id: Optional[int] = None
    speed_scale: Optional[float] = None
    volume_scale: Optional[float] = None


async def _on_startup():
    await tts_service.start()
    if TTS_SETTINGS_FILE.exists():
        try:
            with open(TTS_SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved_tts = json.load(f)
                sync_tts_settings_to_service(saved_tts)
        except Exception:
            pass


async def _on_shutdown():
    await tts_service.stop()


def register(ctx):
    ctx.on_startup(_on_startup)
    ctx.on_shutdown(_on_shutdown)

    router = APIRouter()

    @router.get("/tts_settings")
    def get_tts_settings():
        default_settings = {
            "enabled": False,
            "highBioEnabled": False,
            "highBioMode": "both",
            "highBioThreshold": 40000000,
            "highBioThresholdType": "bonus",
            "highBioText": "{body}、高額生物反応です。見込額{value}クレジット。",
            "gggEnabled": True,
            "gggConfirmedEnabled": True,
            "gggMode": "both",
            "gggConfirmedText": "{body}はグリーンガスジャイアント、目視確認を推奨。種別は、{variant}です。",
            "engine": "web_speech",
            "webVoiceURI": "",
            "voicevoxSpeakerId": "3",
            "voicevoxUrl": "http://127.0.0.1:50021",
            "customText": "First discover.",
            "volume": 1.0,
            "rate": 1.0
        }
        if TTS_SETTINGS_FILE.exists():
            try:
                with open(TTS_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    default_settings.update(saved)
            except Exception:
                pass
        return default_settings

    @router.post("/tts_settings")
    def save_tts_settings_endpoint(settings: dict):
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            saved_settings = {}
            if TTS_SETTINGS_FILE.exists():
                try:
                    with open(TTS_SETTINGS_FILE, "r", encoding="utf-8") as f:
                        saved_settings = json.load(f)
                except Exception:
                    pass
            saved_settings.update(settings)
            with open(TTS_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(saved_settings, f, ensure_ascii=False, indent=2)

            sync_tts_settings_to_service(saved_settings)
            return {"status": "saved", "settings": saved_settings}
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

    @router.post("/tts/speak")
    def tts_speak_endpoint(req: TTSSpeakRequest):
        enqueued = tts_service.enqueue_speak(req.text, priority=bool(req.priority))
        return {
            "status": "success",
            "data": {
                "enqueued": enqueued,
                "text": req.text
            }
        }

    @router.post("/tts/test")
    def tts_test_endpoint():
        enqueued = tts_service.test_speak()
        return {
            "status": "success",
            "data": {
                "enqueued": enqueued,
                "text": "音声キャプチャの接続テストです"
            }
        }

    @router.get("/tts/config")
    def tts_get_config_endpoint():
        return {
            "status": "success",
            "data": tts_service.get_config()
        }

    @router.post("/tts/config")
    def tts_update_config_endpoint(req: TTSConfigRequest):
        dump_fn = getattr(req, "model_dump", getattr(req, "dict", None))
        raw_data = dump_fn() if dump_fn else req.__dict__
        update_data = {k: v for k, v in raw_data.items() if v is not None}
        tts_service.update_config(update_data)
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            saved_settings = {}
            if TTS_SETTINGS_FILE.exists():
                try:
                    with open(TTS_SETTINGS_FILE, "r", encoding="utf-8") as f:
                        saved_settings = json.load(f)
                except Exception:
                    pass
            if "voicevox_url" in update_data:
                saved_settings["voicevoxUrl"] = update_data["voicevox_url"]
                saved_settings["voicevox_url"] = update_data["voicevox_url"]
            if "speaker_id" in update_data:
                saved_settings["voicevoxSpeakerId"] = str(update_data["speaker_id"])
                saved_settings["speaker_id"] = update_data["speaker_id"]
            if "speed_scale" in update_data:
                saved_settings["rate"] = update_data["speed_scale"]
                saved_settings["speed_scale"] = update_data["speed_scale"]
            if "volume_scale" in update_data:
                saved_settings["volume"] = update_data["volume_scale"]
                saved_settings["volume_scale"] = update_data["volume_scale"]
            if "enabled" in update_data:
                saved_settings["enabled"] = update_data["enabled"]

            with open(TTS_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(saved_settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return {
            "status": "success",
            "data": tts_service.get_config()
        }

    # Reclaims the original /api/tts_settings, /api/tts/* paths (no
    # /api/addons/... prefix) so existing frontend call sites keep working.
    ctx.add_api_router(router, prefix="/api")
