import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_mining_test(script_body):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    mining_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "mining_view.js"

    runner_script = f"""
    const fs = require('fs');

    // DOM mock environment
    function createMockElement(tag = 'div') {{
      return {{
        tagName: tag.toUpperCase(),
        innerText: '',
        innerHTML: '',
        value: '',
        style: {{}},
        children: [],
        dataset: {{}},
        classList: {{
          _classes: new Set(),
          add(c) {{ this._classes.add(c); }},
          remove(c) {{ this._classes.delete(c); }},
          contains(c) {{ return this._classes.has(c); }}
        }},
        appendChild(child) {{ this.children.push(child); }},
        querySelectorAll() {{ return []; }},
        querySelector() {{ return null; }},
        addEventListener() {{}}
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
    global.t = (k) => k;
    global.state = {{
      selectedBody: null,
      selectedSystem: null,
      currentSystemData: null,
      targetBodyId: null,
      miningSubFilter: 'all',
      showMiningGravity: true,
      showMiningTemp: true,
      filters: {{}}
    }};
    global.navigator = {{
      clipboard: {{
        writeText: () => Promise.resolve()
      }}
    }};

    // Load utils.js then mining_view.js
    const utilsCode = fs.readFileSync({json.dumps(str(utils_path))}, 'utf-8');
    eval(utilsCode);

    const miningCode = fs.readFileSync({json.dumps(str(mining_path))}, 'utf-8');
    eval(miningCode);

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


def test_mining_view_exports():
    out = run_js_mining_test("""
    const exports = [
      typeof renderBodyMiningBlock === 'function',
      typeof renderMiningView === 'function',
      typeof refreshMiningSitesForBody === 'function',
      typeof openMiningSiteModal === 'function',
      typeof closeMiningSiteModal === 'function',
      typeof initMiningSiteModal === 'function'
    ];
    console.log(JSON.stringify(exports));
    """)
    res = json.loads(out)
    assert all(res), f"Expected all exports to be functions, got: {res}"


def test_render_body_mining_block():
    out = run_js_mining_test("""
    const blockWithMining = renderBodyMiningBlock({ mining_signals: 3 });
    const blockZeroMining = renderBodyMiningBlock({ mining_signals: 0 });

    console.log(JSON.stringify({
      hasMining: blockWithMining,
      zeroMining: blockZeroMining
    }));
    """)
    res = json.loads(out)
    assert "MINING: 3" in res["hasMining"]
    assert "⛏️" in res["hasMining"]
    assert res["zeroMining"] == ""


def test_render_mining_view_empty():
    out = run_js_mining_test("""
    const container = document.createElement('div');
    renderMiningView(container, []);
    console.log(JSON.stringify({
      html: container.innerHTML
    }));
    """)
    res = json.loads(out)
    assert "no_landable_bodies" in res["html"]


def test_render_mining_view_ring_hotspots():
    out = run_js_mining_test("""
    const container = document.createElement('div');
    const bodies = [
      {
        body_id: 10,
        body_name: 'Sol 3 Ring',
        landable: 0,
        rings_list: [
          {
            Name: 'A Ring',
            RingClass: 'eRingClass_Metalic',
            Hotspots: { 'Platinum': 2, 'Painite': 1 }
          }
        ]
      }
    ];
    renderMiningView(container, bodies);
    console.log(JSON.stringify({
      hasChildren: container.children.length > 0,
      wrapperChildren: container.children[0] ? container.children[0].children.length : 0
    }));
    """)
    res = json.loads(out)
    assert res["hasChildren"] is True
    assert res["wrapperChildren"] >= 2


def test_render_mining_view_landable_body():
    out = run_js_mining_test("""
    const container = document.createElement('div');
    const bodies = [
      {
        body_id: 20,
        body_name: 'Sol 4 a',
        landable: 1,
        planet_class: 'High metal content body',
        surface_gravity_g: 0.38,
        surface_temperature: 250,
        radius: 3389000,
        mining_signals: 2,
        materials: JSON.stringify([{ Name: 'Iron', Percent: 22.5 }]),
        rhino_mining_sites: [
          { latitude: 12.34, longitude: -45.67, commodities: ['Bastnäsite'], hotspot: 'Hotspot 1' }
        ]
      }
    ];
    renderMiningView(container, bodies);
    const wrapper = container.children[0];
    console.log(JSON.stringify({
      wrapperExists: !!wrapper,
      childCount: wrapper ? wrapper.children.length : 0
    }));
    """)
    res = json.loads(out)
    assert res["wrapperExists"] is True
    # guideCard, subFilterBar, and body card
    assert res["childCount"] >= 3


def test_mining_view_bilingual_switching():
    i18n_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js").as_posix()
    out = run_js_mining_test(f"""
    const i18nMod = require('{i18n_path}');
    Object.assign(global, i18nMod);

    state.selectedSystem = {{
      system_name: "Test Mining System",
      system_state: "Boom",
      system_address: 123456
    }};

    const container = document.createElement('div');
    const bodies = [
      {{
        body_id: 20,
        body_name: 'Test Miner 1',
        landable: 1,
        planet_class: 'High metal content body',
        surface_gravity_g: 1.2,
        surface_temperature: 300,
        radius: 4000000,
        mining_signals: 3,
        rings_list: [
          {{
            Name: '1 A Ring',
            RingClass: 'eRingClass_Metalic',
            Hotspots: {{ 'Platinum': 2 }}
          }}
        ]
      }}
    ];

    // Japanese rendering
    setLanguage('ja');
    renderMiningView(container, bodies);
    const ja_wrapper = container.children[0];
    const ja_all_html = (ja_wrapper ? ja_wrapper.children.map(c => c.innerHTML || c.innerText || '').join(' ') : '') + (container.innerHTML || '');

    // English rendering
    const containerEn = document.createElement('div');
    setLanguage('en');
    renderMiningView(containerEn, bodies);
    const en_wrapper = containerEn.children[0];
    const en_all_html = (en_wrapper ? en_wrapper.children.map(c => c.innerHTML || c.innerText || '').join(' ') : '') + (containerEn.innerHTML || '');

    console.log(JSON.stringify({{
      ja_has_summary: ja_all_html.includes("星系採掘サマリー") || ja_all_html.includes("採掘・Landable天体サマリー"),
      ja_has_boom: ja_all_html.includes("好況"),
      ja_has_sites: ja_all_html.includes("採掘地点"),
      ja_has_spansh: ja_all_html.includes("Spansh照会"),
      en_has_summary: en_all_html.includes("System Mining Summary") || en_all_html.includes("Mining & Landable Bodies Summary") || en_all_html.includes("Field Guide"),
      en_has_boom: en_all_html.includes("Boom"),
      en_has_sites: en_all_html.includes("Mining Sites") || en_all_html.includes("locations"),
      en_has_spansh: en_all_html.includes("Query") || en_all_html.includes("Spansh")
    }}));
    """)
    res = json.loads(out)
    assert res["ja_has_summary"] is True
    assert res["ja_has_boom"] is True
    assert res["ja_has_sites"] is True
    assert res["ja_has_spansh"] is True

    assert res["en_has_summary"] is True
    assert res["en_has_boom"] is True
    assert res["en_has_sites"] is True
    assert res["en_has_spansh"] is True


