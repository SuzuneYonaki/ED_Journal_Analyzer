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

    {script_body}
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(proc.stdout)


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
