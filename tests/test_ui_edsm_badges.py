"""
Tests verifying system map UI logic separates EDSM_Known bodies from CMDR first discovery badges.
"""

from pathlib import Path


def test_system_map_edsm_badge_logic_in_source():
    """Verify that system_map.js prevents ⭐ 1st on EDSM_Known and adds 🌐 EDSM badge."""
    js_path = Path("app/ui/js/system_map.js")
    assert js_path.exists()
    content = js_path.read_text(encoding="utf-8")

    # Verify isCmdrFirstDisc excludes EDSM_Known
    assert "body.scan_type !== 'EDSM_Known'" in content

    # Verify EDSM badge is applied for EDSM_Known
    assert "span class=\"sysmap-mini-badge edsm-known\"" in content
    assert "🌐 EDSM" in content

    # Verify personal price badge is suppressed for EDSM_Known
    assert "body.scan_type === 'EDSM_Known'" in content


def test_inspector_edsm_label_in_source():
    """Verify that inspector.js uses 🌐 instead of ⭐ for unscanned EDSM bodies."""
    js_path = Path("app/ui/js/inspector.js")
    assert js_path.exists()
    content = js_path.read_text(encoding="utf-8")

    assert "🌐 ${t('edsm_known_unscanned')}" in content
    # Ensure misleading ⭐ is not in the EDSM unscanned label
    assert "⭐ ${t('edsm_known_unscanned')}" not in content
