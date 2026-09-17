import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_utils_eval(expression):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    runner_script = f"""
    const fs = require('fs');
    global.window = global;
    global.t = (k) => k;
    const code = fs.readFileSync({json.dumps(str(js_path))}, 'utf8');
    eval(code);
    const result = ({expression});
    console.log(JSON.stringify(result));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(proc.stdout)


def test_format_credits():
    assert run_js_utils_eval('formatCredits(0)') == '0 Cr'
    assert run_js_utils_eval('formatCredits(null)') == '0 Cr'
    assert run_js_utils_eval('formatCredits(1234567)') == '1,234,567 Cr'


def test_format_distance():
    assert run_js_utils_eval('formatDistance(null)') == '--'
    assert 'km' in run_js_utils_eval('formatDistance(0.5)')
    assert 'M ls' in run_js_utils_eval('formatDistance(2500000)')
    assert 'ls' in run_js_utils_eval('formatDistance(500.5)')


def test_parse_ring_class():
    icy = run_js_utils_eval('parseRingClass("eRingClass_Icy")')
    assert icy['key'] == 'icy'
    assert icy['icon'] == '❄️'

    metallic = run_js_utils_eval('parseRingClass("eRingClass_Metallic")')
    assert metallic['key'] == 'metallic'
    assert metallic['icon'] == '🪙'

    metal_rich = run_js_utils_eval('parseRingClass("eRingClass_MetalRich")')
    assert metal_rich['key'] == 'metal_rich'

    rocky = run_js_utils_eval('parseRingClass("eRingClass_Rocky")')
    assert rocky['key'] == 'rocky'


def test_parse_reserve_level():
    assert run_js_utils_eval('parseReserveLevel(null)') is None
    res = run_js_utils_eval('parseReserveLevel("PristineResources")')
    assert res['en'] == 'Pristine'
    assert res['icon'] == '💎'


def test_body_icons():
    star = run_js_utils_eval('getBodyIconClass({ star_type: "G" })')
    assert star == 'icon-star'

    bh = run_js_utils_eval('getBodyIconClass({ star_type: "H" })')
    assert bh == 'icon-black-hole'

    elw = run_js_utils_eval('getBodyIconClass({ planet_class: "Earthlike body" })')
    assert elw == 'icon-elw'

    ww_label = run_js_utils_eval('getBodyIconLabel({ planet_class: "Water world" })')
    assert ww_label == 'WW'


def test_module_settings_defaults():
    settings = run_js_utils_eval('getModuleSettings()')
    assert settings['exobiology'] is False
    assert settings['rhino'] is False


def test_app_state_live_sync_default():
    """Verify that state.liveSyncEnabled in app.js defaults to false."""
    app_js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "app.js"
    content = app_js_path.read_text(encoding="utf-8")
    # Verify state definition defaults liveSyncEnabled to false
    import re
    m = re.search(r'liveSyncEnabled:\s*(true|false)', content)
    assert m is not None, "liveSyncEnabled property not found in app.js"
    assert m.group(1) == "false", f"Expected liveSyncEnabled to be false, got {m.group(1)}"


def test_export_html_url_includes_lang():
    """Verify that export html fetch in app.js includes ?lang= parameter."""
    app_js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "app.js"
    content = app_js_path.read_text(encoding="utf-8")
    assert "/api/export/html/${sysAddr}?lang=" in content, "app.js must pass ?lang= query param to /api/export/html"

