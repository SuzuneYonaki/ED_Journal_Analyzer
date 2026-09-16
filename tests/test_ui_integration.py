import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_integration_test(script_body):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    ui_js_dir = Path(__file__).resolve().parent.parent / "app" / "ui" / "js"
    utils_path = ui_js_dir / "utils.js"
    inspector_path = ui_js_dir / "inspector.js"
    mining_path = ui_js_dir / "mining_view.js"
    system_list_path = ui_js_dir / "system_list.js"
    app_path = ui_js_dir / "app.js"

    runner_script = f"""
    const fs = require('fs');

    // Full DOM mock environment
    function createMockElement(tag = 'div') {{
      return {{
        tagName: tag.toUpperCase(),
        innerText: '',
        innerHTML: '',
        value: '',
        placeholder: '',
        disabled: false,
        title: '',
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
      querySelectorAll: (sel) => [],
      querySelector: (sel) => null,
      createElement: (tag) => createMockElement(tag),
      addEventListener: () => {{}}
    }};
    global.window = global;
    global.localStorage = {{
      _data: {{}},
      getItem(k) {{ return this._data[k] || null; }},
      setItem(k, v) {{ this._data[k] = String(v); }}
    }};
    global.navigator = {{
      clipboard: {{
        writeText: () => Promise.resolve()
      }}
    }};
    global.t = (k) => k;

    // Load in exact browser order: utils -> inspector -> mining_view -> system_list -> app
    const scripts = [
      {json.dumps(str(utils_path))},
      {json.dumps(str(inspector_path))},
      {json.dumps(str(mining_path))},
      {json.dumps(str(system_list_path))},
      {json.dumps(str(app_path))}
    ];

    for (const s of scripts) {{
      const code = fs.readFileSync(s, 'utf-8');
      eval(code);
    }}

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


def test_full_frontend_integration_and_state():
    out = run_js_integration_test("""
    console.log(JSON.stringify({
      hasState: typeof state === 'object' && state !== null,
      windowStateIdentical: window.state === state,
      hasSelectSystem: typeof selectSystem === 'function',
      hasRenderSystemList: typeof renderSystemList === 'function',
      hasRenderMiningView: typeof renderMiningView === 'function',
      hasRenderBodyInspector: typeof renderBodyInspector === 'function',
      hasEscapeHtml: typeof escapeHtml === 'function',
      hasFormatCredits: typeof formatCredits === 'function'
    }));
    """)
    res = json.loads(out)
    assert res["hasState"] is True
    assert res["windowStateIdentical"] is True
    assert res["hasSelectSystem"] is True
    assert res["hasRenderSystemList"] is True
    assert res["hasRenderMiningView"] is True
    assert res["hasRenderBodyInspector"] is True
    assert res["hasEscapeHtml"] is True
    assert res["hasFormatCredits"] is True


def test_cross_module_sorting_and_rendering():
    out = run_js_integration_test("""
    const bodies = [
      { body_id: 1, body_name: 'Earth', max_potential_value: 1000000, distance_from_arrival_ls: 500 },
      { body_id: 2, body_name: 'Mars', max_potential_value: 200000, distance_from_arrival_ls: 700 }
    ];

    state.bodySortBy = 'value';
    state.bodySortOrder = 'desc';
    const sorted = getSortedBodies(bodies);

    console.log(JSON.stringify({
      topBody: sorted[0].body_name,
      secondBody: sorted[1].body_name
    }));
    """)
    res = json.loads(out)
    assert res["topBody"] == "Earth"
    assert res["secondBody"] == "Mars"


def test_cross_module_view_switching():
    out = run_js_integration_test("""
    state.currentView = 'tree';
    const view1 = state.currentView;
    state.currentView = 'flat';
    const view2 = state.currentView;
    state.currentView = 'bio';
    const view3 = state.currentView;
    state.currentView = 'mining';
    const view4 = state.currentView;

    console.log(JSON.stringify({ view1, view2, view3, view4 }));
    """)
    res = json.loads(out)
    assert res["view1"] == "tree"
    assert res["view2"] == "flat"
    assert res["view3"] == "bio"
    assert res["view4"] == "mining"
