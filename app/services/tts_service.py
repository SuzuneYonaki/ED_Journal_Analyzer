"""
tts_service.py - Backend Text-To-Speech Service (VOICEVOX) with OBS Audio Capture Support
Elite Dangerous Journal Analyzer

Provides backend audio playback directly from the Python server process
to allow OBS Studio's "Application Audio Capture" to hook TTS output independently.
Features queued sequential playback to prevent audio overlap.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any, Dict, Optional, Tuple

import httpx

try:
    import winsound
except ImportError:
    winsound = None

logger = logging.getLogger("ed_analyzer.tts_service")


class TTSService:
    """
    Backend TTS Service managing VOICEVOX speech synthesis and direct OS audio output.
    Uses an internal asyncio queue for sequential, non-overlapping playback.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = {
            "enabled": True,
            "voicevox_url": "http://127.0.0.1:50021",
            "speaker_id": 1,
            "speed_scale": 1.0,
            "volume_scale": 1.0,
        }
        if config is not None:
            self.update_config(config)

        self._queue: asyncio.Queue[Optional[Tuple[str, bool]]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def start(self) -> None:
        """Starts the background sequential audio playback worker."""
        if self._running and self._worker_task and not self._worker_task.done():
            return
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("TTS backend service started.")

    async def stop(self) -> None:
        """Stops the worker cleanly."""
        if not self._running:
            return
        self._running = False
        await self._queue.put(None)
        if self._worker_task:
            try:
                await asyncio.wait_for(self._worker_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._worker_task.cancel()
            self._worker_task = None
        logger.info("TTS backend service stopped.")

    def enqueue_speak(self, text: str, priority: bool = False) -> bool:
        """
        Enqueues text for synthesis and playback.
        Returns True if enqueued, False if disabled or invalid text.
        """
        if not self.config.get("enabled", True):
            return False

        clean_text = (text or "").strip()
        if not clean_text:
            return False

        # Put into queue non-blocking
        self._queue.put_nowait((clean_text, priority))
        return True

    def test_speak(self) -> bool:
        """
        Triggers an immediate test utterance for OBS Application Audio Capture recognition.
        """
        return self.enqueue_speak("音声キャプチャの接続テストです", priority=True)

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Safely updates TTS configuration with strict None guards.
        """
        if not isinstance(new_config, dict):
            return

        enabled = new_config.get("enabled")
        if enabled is not None:
            self.config["enabled"] = bool(enabled)

        voicevox_url = new_config.get("voicevox_url")
        if voicevox_url is not None:
            self.config["voicevox_url"] = str(voicevox_url).rstrip("/")

        speaker_id = new_config.get("speaker_id")
        if speaker_id is not None:
            try:
                self.config["speaker_id"] = int(speaker_id)
            except (ValueError, TypeError):
                pass

        speed_scale = new_config.get("speed_scale")
        if speed_scale is not None:
            try:
                self.config["speed_scale"] = float(speed_scale)
            except (ValueError, TypeError):
                pass

        volume_scale = new_config.get("volume_scale")
        if volume_scale is not None:
            try:
                self.config["volume_scale"] = float(volume_scale)
            except (ValueError, TypeError):
                pass

    def get_config(self) -> Dict[str, Any]:
        """Returns a copy of the current configuration."""
        return self.config.copy()

    async def _worker(self) -> None:
        """Sequential queue processing worker."""
        while self._running:
            try:
                item = await self._queue.get()
                if item is None:
                    self._queue.task_done()
                    break

                text, priority = item
                if self.config.get("enabled", True):
                    await self._synthesize_and_play(text)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in TTS worker queue: {e}", exc_info=True)

    async def _synthesize_and_play(self, text: str) -> None:
        """Calls VOICEVOX API to synthesize audio and plays it via system sound."""
        try:
            url = self.config.get("voicevox_url", "http://127.0.0.1:50021")
            speaker = self.config.get("speaker_id", 1)
            speed = self.config.get("speed_scale", 1.0)
            volume = self.config.get("volume_scale", 1.0)

            async with httpx.AsyncClient(timeout=10.0) as client:
                # Step 1: Create audio query
                query_res = await client.post(
                    f"{url}/audio_query",
                    params={"text": text, "speaker": speaker}
                )
                query_res.raise_for_status()
                query_data = query_res.json()

                # Apply speed & volume scaling
                query_data["speedScale"] = speed
                query_data["volumeScale"] = volume

                # Step 2: Synthesize audio
                synth_res = await client.post(
                    f"{url}/synthesis",
                    params={"speaker": speaker},
                    json=query_data
                )
                synth_res.raise_for_status()
                wav_bytes = synth_res.content

            # Step 3: Play audio sequentially without blocking the event loop
            await self._play_audio(wav_bytes)

        except Exception as e:
            logger.warning(f"VOICEVOX synthesis/playback error for '{text}': {e}")

    async def _play_audio(self, wav_bytes: bytes) -> None:
        """Plays WAV bytes using the Windows audio subsystem (or mocks on other platforms)."""
        if not wav_bytes:
            return

        if winsound is not None:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                winsound.PlaySound,
                wav_bytes,
                winsound.SND_MEMORY
            )
        else:
            logger.debug(f"[Non-Windows/Mock] Simulated playback of {len(wav_bytes)} bytes.")


# Module-level singleton instance
tts_service = TTSService()
