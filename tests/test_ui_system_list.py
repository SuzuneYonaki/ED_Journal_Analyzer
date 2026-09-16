import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_system_list_test(script_body):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    system_list_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_list.js"

    runner_script = f"""
    const fs = require('fs');

    // DOM mock environment
    function createMockElement(tag = 'div') {{
      return {{
        tagName: tag.toUpperCase(),
        innerText: '',
        innerHTML: '',
        value: '',
        style: {{ display: '' }},
        children: [],
        dataset: {{}},
        classList: {{
          _classes: new Set(),
          add(c) {{ this._classes.add(c); }},
          remove(c) {{ this._classes.delete(c); }},
          toggle(c, force) {{
            if (force === undefined) {{
              if (this._classes.has(c)) this._classes.delete(c);
              else this._classes.add(c);
            }} else {{
              if (force) this._classes.add(c);
              else this._classes.delete(c);
            }}
          }},
          contains(c) {{ return this._classes.has(c); }}
        }},
        appendChild(child) {{ this.children.push(child); }},
        querySelectorAll() {{ return []; }},
        querySelector() {{ return null; }},
        addEventListener() {{}},
        scrollTo() {{}},
        scrollIntoView() {{}}
      }};
    }}

    const domStore = {{}};
    function getOrCreateEl(id) {{
      if (!domStore[id]) {{
        domStore[id] = createMockElement('div');
        domStore[id].id = id;
      }}
      return domStore[id];
    }}

    global.document = {{
      getElementById: (id) => getOrCreateEl(id),
      querySelectorAll: () => [],
      querySelector: () => null,
      createElement: (tag) => createMockElement(tag)
    }};
    global.window = global;
    global.localStorage = {{
      _data: {{}},
      getItem(k) {{ return this._data[k] || null; }},
      setItem(k, v) {{ this._data[k] = String(v); }}
    }};
    global.t = (k) => k;
    global.selectSystem = () => Promise.resolve();
    global.fetchSystems = () => Promise.resolve();
    global.state = {{
      systems: [],
      selectedSystem: null,
      currentLocation: {{ star_system: 'Sol' }},
      currentSystemData: null,
      page: 1,
      totalPages: 5,
      filters: {{}},
      celestialFilters: [],
      starTypes: [],
      luminosityClasses: [],
      collapsedGroups: {{}},
      uiLayoutMode: '1col',
      headerStatsCollapsed: false
    }};

    // Load utils.js then system_list.js
    const utilsCode = fs.readFileSync({json.dumps(str(utils_path))}, 'utf-8');
    eval(utilsCode);

    const sysListCode = fs.readFileSync({json.dumps(str(system_list_path))}, 'utf-8');
    eval(sysListCode);

    {script_body}
    """

    res = subprocess.run(
        [node_exe, "-e", runner_script],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if res.returncode != 0:
        raise RuntimeError(f"Node execution failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
    return res.stdout.strip()


def test_system_list_exports():
    out = run_js_system_list_test("""
    const exports = [
      typeof defaultLandmarkSettings === 'object',
      typeof getLandmarkSettings === 'function',
      typeof saveLandmarkSettings === 'function',
      typeof generateLandmarkDistanceBadges === 'function',
      typeof updateCurrentSystemDistances === 'function',
      typeof renderSystemList === 'function',
      typeof highlightSelectedSystemCard === 'function',
      typeof scrollToTopOfSystemCards === 'function',
      typeof renderPagination === 'function',
      typeof renderSystemHeader === 'function',
      typeof updateCollapsibleBadges === 'function',
      typeof initCollapsibleSections === 'function',
      typeof initStellarFilters === 'function',
      typeof initLayoutSwitcher === 'function',
      typeof initHeaderStatsCollapse === 'function',
      typeof clearSystemBioSummary === 'function'
    ];
    console.log(JSON.stringify(exports));
    """)
    res = json.loads(out)
    assert all(res), f"Expected all exports to be valid, got: {res}"


def test_generate_landmark_distance_badges():
    out = run_js_system_list_test("""
    const sys = {
      cmdr_distance_ly: 42.5,
      sol_distance_ly: 100.0,
      colonia_distance_ly: 22000.0,
      star_pos_x: 0,
      star_pos_y: 0,
      star_pos_z: 100
    };
    const badges = generateLandmarkDistanceBadges(sys);
    console.log(JSON.stringify(badges));
    """)
    badges = json.loads(out)
    joined = " ".join(badges)
    assert "CMDR: 43 Ly" in joined
    assert "Sol: 100 Ly" in joined
    assert "Colonia: 22,000 Ly" in joined


def test_render_system_list_empty():
    out = run_js_system_list_test("""
    state.systems = [];
    renderSystemList();
    const container = document.getElementById('system-list');
    console.log(JSON.stringify({ html: container.innerHTML }));
    """)
    res = json.loads(out)
    assert "no_systems" in res["html"]


def test_render_system_list_with_systems():
    out = run_js_system_list_test("""
    state.systems = [
      {
        system_address: 12345678,
        star_system: 'Sol',
        total_potential_value: 5000000,
        scanned_bodies: 10,
        total_bodies: 10,
        has_elw: true,
        has_first_discover: true,
        first_discovered_bodies: 2,
        main_star_type: 'G',
        star_pos_x: 0,
        star_pos_y: 0,
        star_pos_z: 0
      }
    ];
    renderSystemList();
    const container = document.getElementById('system-list');
    const child = container.children[0];
    console.log(JSON.stringify({
      cardCount: container.children.length,
      cardHtml: child ? child.innerHTML : ''
    }));
    """)
    res = json.loads(out)
    assert res["cardCount"] == 1
    assert "Sol" in res["cardHtml"]
    assert "ELW" in res["cardHtml"]
    assert "1st Disc" in res["cardHtml"]


def test_render_pagination():
    out = run_js_system_list_test("""
    state.page = 2;
    state.totalPages = 5;
    renderPagination(50);
    const info = document.getElementById('page-info').innerText;
    const prevDisabled = document.getElementById('btn-prev-page').disabled;
    const nextDisabled = document.getElementById('btn-next-page').disabled;
    console.log(JSON.stringify({ info, prevDisabled, nextDisabled }));
    """)
    res = json.loads(out)
    assert res["info"] == "2 / 5 (50)"
    assert res["prevDisabled"] is False
    assert res["nextDisabled"] is False


def test_update_collapsible_badges():
    out = run_js_system_list_test("""
    state.filters = {
      has_elw: true,
      has_bio: true,
      has_landable_hmc: true
    };
    state.miningScout = 'High';
    state.celestialFilters = ['black_hole', 'neutron_star'];
    state.starTypes = ['O', 'B'];
    state.luminosityClasses = ['Ia'];

    updateCollapsibleBadges();

    console.log(JSON.stringify({
      genText: document.getElementById('badge-general-filters').innerText,
      mineText: document.getElementById('badge-mining-filters').innerText,
      celText: document.getElementById('badge-celestial-filters').innerText,
      starText: document.getElementById('badge-stars-filters').innerText
    }));
    """)
    res = json.loads(out)
    # General has 2 active (has_elw, has_bio)
    assert res["genText"] == 2
    # Mining has has_landable_hmc (1) + miningScout (1) = 2
    assert res["mineText"] == 2
    # Celestial has 2
    assert res["celText"] == 2
    # Star has 2 types + 1 lum = 3
    assert res["starText"] == 3


def test_clear_system_bio_summary():
    out = run_js_system_list_test("""
    const bioBox = document.getElementById('system-bio-payout-box');
    bioBox.style.display = 'block';
    clearSystemBioSummary();
    console.log(JSON.stringify({
      display: bioBox.style.display,
      scannedBase: document.getElementById('current-system-bio-scanned-base').innerText
    }));
    """)
    res = json.loads(out)
    assert res["display"] == "none"
    assert res["scannedBase"] == "0 Cr"
