import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_inspector_test(script_body):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    inspector_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "inspector.js"

    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as tf:
        out_file = tf.name.replace("\\", "/") + ".out.json"
        runner_script = f"""
    const fs = require('fs');

    // DOM mock environment
    const domStore = {{}};
    function getOrCreateEl(id) {{
      if (!domStore[id]) {{
        domStore[id] = {{
          id: id,
          tagName: 'DIV',
          innerText: '',
          innerHTML: '',
          value: '',
          style: {{ display: '' }},
          classList: {{
            _classes: new Set(),
            add(c) {{ this._classes.add(c); }},
            remove(c) {{ this._classes.delete(c); }},
            toggle(c, force) {{ if (force) this._classes.add(c); else this._classes.delete(c); }},
            contains(c) {{ return this._classes.has(c); }}
          }},
          children: [],
          appendChild(c) {{ this.children.push(c); }},
          querySelector() {{ return null; }}
        }};
      }}
      return domStore[id];
    }}

    global.document = {{
      getElementById: (id) => getOrCreateEl(id),
      querySelectorAll: () => [],
      createElement: (tag) => ({{
        tagName: tag,
        innerText: '',
        innerHTML: '',
        style: {{}},
        classList: {{ add() {{}}, remove() {{}} }}
      }})
    }};
    global.window = global;
    global.t = (k) => k;
    global.state = {{ selectedBody: null, selectedSystem: null, currentSystemData: null }};

    // Load utils.js then inspector.js
    const utilsCode = fs.readFileSync({json.dumps(str(utils_path))}, 'utf8');
    eval(utilsCode);
    const inspectorCode = fs.readFileSync({json.dumps(str(inspector_path))}, 'utf8');
    eval(inspectorCode);

    console.log = function(data) {{{{
      fs.writeFileSync("{out_file}", typeof data === 'string' ? data : JSON.stringify(data), 'utf8');
    }}}};

    {script_body}
    """
        tf.write(runner_script)
        tf_name = tf.name
    try:
        proc = subprocess.run([node_exe, tf_name], capture_output=True, text=True, encoding="utf-8", check=True)
        out_p = Path(out_file)
        if out_p.exists():
            return json.loads(out_p.read_text(encoding="utf-8"))
        return json.loads(proc.stdout)
    finally:
        Path(tf_name).unlink(missing_ok=True)
        Path(out_file).unlink(missing_ok=True)


def test_inspector_clears_gracefully():
    script = """
    clearBodyInspector();
    const result = {
      name: document.getElementById('inspect-body-name').innerText,
      fss: document.getElementById('val-fss').innerText
    };
    console.log(JSON.stringify(result));
    """
    res = run_js_inspector_test(script)
    assert res['name'] == '--'
    assert res['fss'] == '0 Cr'


def test_inspector_handles_null_selection():
    script = """
    state.selectedBody = null;
    renderBodyInspector();
    const result = {
      display: document.getElementById('inspector-content').style.display,
      title: document.getElementById('inspect-body-name').innerText
    };
    console.log(JSON.stringify(result));
    """
    res = run_js_inspector_test(script)
    assert res['display'] == 'none'
    assert res['title'] == 'inspector_title'


def test_inspector_renders_planet():
    script = """
    state.selectedBody = {
      body_id: 2,
      body_name: "Earth-like Test",
      planet_class: "Earthlike body",
      terraforming_state: "Terraformed",
      fss_value: 500000,
      dss_value: 1200000,
      first_discovered_fss: 2500000,
      first_mapped_dss: 6000000,
      max_potential_value: 9700000,
      surface_gravity: 9.81,
      surface_temperature: 288,
      surface_pressure: 101325,
      atmosphere: "Nitrogen",
      landable: false
    };
    renderBodyInspector();
    const result = {
      display: document.getElementById('inspector-content').style.display,
      name: document.getElementById('inspect-body-name').innerText,
      typeSubtitle: document.getElementById('inspect-body-type').innerText,
      maxPayout: document.getElementById('val-max-total').innerText,
      bmDisplay: document.getElementById('section-bookmark').style.display
    };
    console.log(JSON.stringify(result));
    """
    res = run_js_inspector_test(script)
    assert res['display'] == 'block'
    assert res['name'] == 'Earth-like Test'
    assert 'Earthlike body' in res['typeSubtitle']
    assert '9,700,000 Cr' in res['maxPayout']
    assert res['bmDisplay'] == 'block'


def test_inspector_handles_asteroid_belt_bookmark_guard():
    script = """
    state.selectedBody = {
      body_id: "belt-1-0",
      body_name: "Sol Asteroid Belt A",
      isAsteroidBelt: true,
      ring_class: "eRingClass_MetalRich",
      rings_list: [
        {
          Name: "Sol Asteroid Belt A",
          RingClass: "eRingClass_MetalRich",
          InnerRad: 3.14e11,
          OuterRad: 4.78e11,
          MassMT: 5.4e10
        }
      ]
    };
    renderBodyInspector();
    const result = {
      name: document.getElementById('inspect-body-name').innerText,
      typeSubtitle: document.getElementById('inspect-body-type').innerText,
      bmDisplay: document.getElementById('section-bookmark').style.display,
      bmToggleDisplay: document.getElementById('btn-inspect-bookmark-toggle').style.display,
      ringsDisplay: document.getElementById('section-rings').style.display
    };
    console.log(JSON.stringify(result));
    """
    res = run_js_inspector_test(script)
    assert res['name'] == 'Sol Asteroid Belt A'
    assert 'Asteroid Belt' in res['typeSubtitle']
    assert res['bmDisplay'] == 'none', "Bookmark section should be hidden for asteroid belts"
    assert res['bmToggleDisplay'] == 'none', "Bookmark toggle should be hidden for asteroid belts"
    assert res['ringsDisplay'] == 'block', "Rings/belt section should be visible"


def test_inspector_bilingual_switching():
    i18n_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js").as_posix()
    script = f"""
    const i18nMod = require('{i18n_path}');
    Object.assign(global, i18nMod);

    state.selectedBody = {{
      body_id: 10,
      body_name: "Tidal Test Body",
      planet_class: "Rocky body",
      scan_type: "EDSM_Known",
      edsm_discovered_by: "ExplorerOne",
      tidal_lock: true
    }};

    setLanguage('ja');
    renderBodyInspector();
    const ja_sub = document.getElementById('inspect-body-type').innerText;
    const ja_tidal = document.getElementById('prop-tidal-lock').innerText;

    setLanguage('en');
    renderBodyInspector();
    const en_sub = document.getElementById('inspect-body-type').innerText;
    const en_tidal = document.getElementById('prop-tidal-lock').innerText;

    const result = {{ ja_sub, ja_tidal, en_sub, en_tidal }};
    console.log(JSON.stringify(result));
    """
    res = run_js_inspector_test(script)
    assert "EDSM既知" in res['ja_sub']
    assert "発見者" in res['ja_sub']
    assert "あり (固定)" in res['ja_tidal']

    assert "Known in EDSM" in res['en_sub']
    assert "Discovered by" in res['en_sub']
    assert "Yes (Locked)" in res['en_tidal']


def test_inspector_anomaly_and_barycentre_localization():
    i18n_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js").as_posix()
    script = f"""
    const i18nMod = require('{i18n_path}');
    Object.assign(global, i18nMod);

    // 1. Barycentre body
    state.selectedBody = {{
      body_id: 101,
      body_name: "Test Barycentre AB",
      isBarycentre: true,
      barycentreStars: ["A", "B"],
      starGroup: "AB"
    }};

    setLanguage('ja');
    renderBodyInspector();
    const ja_barycentre_html = document.getElementById('inspect-anomaly-tags').innerHTML;

    setLanguage('en');
    renderBodyInspector();
    const en_barycentre_html = document.getElementById('inspect-anomaly-tags').innerHTML;

    // 2. Anomaly with desc_en and legacy anomaly without desc_en
    state.selectedBody = {{
      body_id: 102,
      body_name: "Extreme Planet",
      anomalies: [
        {{
          type: "extreme_orbit",
          tag: "Extreme Eccentricity",
          desc: "極端な高離心率軌道 (e = 0.850)",
          desc_en: "Extreme Orbital Eccentricity (e = 0.850)"
        }},
        {{
          type: "extreme_spin",
          tag: "Rapid Spinner",
          desc: "超高速自転 (1.2 時間)"
        }}
      ]
    }};

    setLanguage('ja');
    renderBodyInspector();
    const ja_anom_html = document.getElementById('inspect-anomaly-tags').innerHTML;

    setLanguage('en');
    renderBodyInspector();
    const en_anom_html = document.getElementById('inspect-anomaly-tags').innerHTML;

    const result = {{
      ja_barycentre_html,
      en_barycentre_html,
      ja_anom_html,
      en_anom_html
    }};
    console.log(JSON.stringify(result));
    """
    res = run_js_inspector_test(script)
    assert "共通重心" in res['ja_barycentre_html']
    assert "Barycentre" in res['en_barycentre_html']

    assert "極端な高離心率軌道" in res['ja_anom_html']
    assert "超高速自転" in res['ja_anom_html']

    assert "Extreme Orbital Eccentricity (e = 0.850)" in res['en_anom_html']
    assert "Rapid Rotational Period (1.2 hrs)" in res['en_anom_html']

