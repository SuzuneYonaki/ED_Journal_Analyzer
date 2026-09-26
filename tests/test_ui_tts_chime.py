from pathlib import Path
import re


def test_tts_chime_and_announcement_logic():
    """Verify that TTS chime and announcement functions are properly implemented in app.js."""
    app_js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "app.js"
    content = app_js_path.read_text(encoding="utf-8")

    # 1. Verify getSharedAudioContext exists and handles suspended state
    assert "function getSharedAudioContext()" in content, "getSharedAudioContext function must be defined"
    assert "sharedAudioCtx.state === 'suspended'" in content, "Must check for suspended AudioContext state"
    assert "sharedAudioCtx.resume()" in content, "Must call resume on AudioContext"

    # 2. Verify checkAndAnnounceHighBioBody does NOT erroneously require !ttsState.enabled
    m_high_bio = re.search(r"function checkAndAnnounceHighBioBody\([^)]*\)\s*\{([^}]+)\}", content)
    assert m_high_bio is not None, "checkAndAnnounceHighBioBody must be defined"
    high_bio_body = m_high_bio.group(1)
    assert "!ttsState.enabled" not in high_bio_body, "checkAndAnnounceHighBioBody must not depend on ttsState.enabled"
    assert "ttsState.highBioEnabled" in high_bio_body, "checkAndAnnounceHighBioBody must check highBioEnabled"

    # 3. Verify checkAndAnnounceGggBody is defined and called in selectSystem
    assert "function checkAndAnnounceGggBody(" in content, "checkAndAnnounceGggBody function must be defined"
    assert "checkAndAnnounceGggBody(data.system, b)" in content, "selectSystem must call checkAndAnnounceGggBody for each body"
    assert "playGggChime()" in content, "playGggChime must be called"
    assert "playHighBioBuzzer()" in content, "playHighBioBuzzer must be called"
