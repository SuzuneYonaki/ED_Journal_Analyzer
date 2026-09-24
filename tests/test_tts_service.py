"""
test_tts_service.py - Unit tests for Backend TTS Service (VOICEVOX)
Elite Dangerous Journal Analyzer
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.tts_service import TTSService


@pytest.fixture
def tts():
    """Provides a fresh instance of TTSService for each test."""
    return TTSService({
        "enabled": True,
        "voicevox_url": "http://127.0.0.1:50021",
        "speaker_id": 1,
        "speed_scale": 1.0,
        "volume_scale": 1.0,
    })


def test_config_management(tts):
    """Test safe config retrieval and update with strict type casting and None guards."""
    cfg = tts.get_config()
    assert cfg["enabled"] is True
    assert cfg["speaker_id"] == 1

    # Update with valid and dirty values
    tts.update_config({
        "enabled": False,
        "voicevox_url": "http://localhost:50021/",
        "speaker_id": "3",
        "speed_scale": "1.25",
        "volume_scale": 0.8,
    })
    updated = tts.get_config()
    assert updated["enabled"] is False
    assert updated["voicevox_url"] == "http://localhost:50021"  # trailing slash removed
    assert updated["speaker_id"] == 3
    assert updated["speed_scale"] == 1.25
    assert updated["volume_scale"] == 0.8

    # Update with None values should NOT overwrite existing settings
    tts.update_config({
        "enabled": None,
        "speaker_id": None,
    })
    assert tts.get_config()["enabled"] is False
    assert tts.get_config()["speaker_id"] == 3


def test_enqueue_speak_validation(tts):
    """Test enqueue validation on text and enabled state."""
    # Valid text
    assert tts.enqueue_speak("テスト発声") is True

    # Empty and whitespace-only text
    assert tts.enqueue_speak("") is False
    assert tts.enqueue_speak("   ") is False
    assert tts.enqueue_speak(None) is False  # type: ignore

    # Disabled state
    tts.update_config({"enabled": False})
    assert tts.enqueue_speak("こんにちは") is False


def test_test_speak(tts):
    """Test OBS identification trigger."""
    assert tts.test_speak() is True


def test_worker_lifecycle_and_playback():
    """Test background worker sequential processing and mock synthesis."""
    async def _run_test():
        service = TTSService({"enabled": True})

        fake_query = {"speedScale": 1.0, "volumeScale": 1.0, "kana": "テスト"}
        fake_wav = b"RIFF....WAVEfmt...."

        mock_resp_query = MagicMock()
        mock_resp_query.json.return_value = fake_query
        mock_resp_query.raise_for_status.return_value = None

        mock_resp_synth = MagicMock()
        mock_resp_synth.content = fake_wav
        mock_resp_synth.raise_for_status.return_value = None

        async def mock_post(url, **kwargs):
            if "audio_query" in url:
                return mock_resp_query
            return mock_resp_synth

        with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=mock_post)):
            with patch.object(service, "_play_audio", new=AsyncMock()) as mock_play:
                await service.start()
                service.enqueue_speak("第1天体")
                service.enqueue_speak("第2天体")

                # Allow queue processing
                await asyncio.sleep(0.1)

                await service.stop()
                assert mock_play.call_count == 2
                mock_play.assert_called_with(fake_wav)

    asyncio.run(_run_test())


def test_worker_resilience_on_connection_error():
    """Test that VOICEVOX connection failure does not crash the worker loop."""
    async def _run_test():
        service = TTSService({"enabled": True})

        with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=Exception("Connection refused"))):
            with patch.object(service, "_play_audio", new=AsyncMock()) as mock_play:
                await service.start()
                service.enqueue_speak("エラーテスト発声")

                await asyncio.sleep(0.1)
                await service.stop()

                # Play should not have been called due to synthesis error
                assert mock_play.call_count == 0

    asyncio.run(_run_test())


def test_tts_api_endpoints():
    """Test FastAPI TTS endpoints (/api/tts/speak, /api/tts/test, /api/tts/config)."""
    from fastapi.testclient import TestClient
    from app.server.api import app

    client = TestClient(app)

    # 1. GET /api/tts/config
    res_get = client.get("/api/tts/config")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["status"] == "success"
    assert "enabled" in data_get["data"]

    # 2. POST /api/tts/config
    res_post_cfg = client.post("/api/tts/config", json={"speaker_id": 7, "speed_scale": 1.1})
    assert res_post_cfg.status_code == 200
    assert res_post_cfg.json()["data"]["speaker_id"] == 7
    assert res_post_cfg.json()["data"]["speed_scale"] == 1.1

    # 3. POST /api/tts/test
    res_test = client.post("/api/tts/test")
    assert res_test.status_code == 200
    assert res_test.json()["status"] == "success"
    assert res_test.json()["data"]["enqueued"] is True

    # 4. POST /api/tts/speak
    res_speak = client.post("/api/tts/speak", json={"text": "システムに到達しました"})
    assert res_speak.status_code == 200
    assert res_speak.json()["data"]["enqueued"] is True
