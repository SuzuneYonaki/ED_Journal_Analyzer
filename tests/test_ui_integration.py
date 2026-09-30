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
      const listeners = {{}};
      const elem = {{
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
              if (this._classes.has(c)) {{ this._classes.delete(c); return false; }}
              else {{ this._classes.add(c); return true; }}
            }} else {{
              if (force) this._classes.add(c);
              else this._classes.delete(c);
              return force;
            }}
          }},
          contains(c) {{ return this._classes.has(c); }}
        }},
        appendChild(child) {{ this.children.push(child); }},
        querySelectorAll(sel) {{
          const res = [];
          for (const c of this.children) {{
            if (c.matches && c.matches(sel)) res.push(c);
            if (c.querySelectorAll) res.push(...c.querySelectorAll(sel));
          }}
          return res;
        }},
        querySelector(sel) {{
          const all = this.querySelectorAll(sel);
          return all.length > 0 ? all[0] : null;
        }},
        setAttribute(k, v) {{ this[k] = v; }},
        getAttribute(k) {{ return this[k] || ''; }},
        addEventListener(event, cb) {{
          if (!listeners[event]) listeners[event] = [];
          listeners[event].push(cb);
        }},
        click() {{
          if (this.onclick) this.onclick({{ stopPropagation: () => {{}} }});
          if (listeners['click']) listeners['click'].forEach(cb => cb({{ stopPropagation: () => {{}} }}));
        }},
        scrollTo() {{}},
        scrollIntoView() {{}}
      }};

      let _className = '';
      Object.defineProperty(elem, 'className', {{
        get() {{ return Array.from(elem.classList._classes).join(' ') || _className; }},
        set(v) {{
          _className = v;
          (v || '').split(/\\s+/).filter(Boolean).forEach(c => elem.classList.add(c));
        }}
      }});
      return elem;
    }}

    const registeredElements = [];
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
      querySelectorAll: (sel) => {{
        return registeredElements.filter(el => el._selectorMatches && el._selectorMatches(sel));
      }},
      querySelector: (sel) => {{
        const all = global.document.querySelectorAll(sel);
        return all.length > 0 ? all[0] : null;
      }},
      createElement: (tag) => {{
        const el = createMockElement(tag);
        el._selectorMatches = (s) => {{
          const classes = (el.className || '').split(/\\s+/);
          if (s.includes('.star-chip') && (el.classList.contains('star-chip') || classes.includes('star-chip'))) return true;
          if (s.includes('.lum-chip') && (el.classList.contains('lum-chip') || classes.includes('lum-chip'))) return true;
          if (s.startsWith('.') && (el.classList.contains(s.slice(1)) || classes.includes(s.slice(1)))) return true;
          return false;
        }};
        registeredElements.push(el);
        return el;
      }},
      addEventListener: () => {{}}
    }};
    global.window = global;
    global.window.addEventListener = () => {{}};
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
    global.fetch = () => Promise.resolve({{
      ok: true,
      json: () => Promise.resolve({{ systems: [], total: 0 }})
    }});
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


def test_rhino_module_hides_mining_filters_and_resets_state():
    out = run_js_integration_test("""
    const groupMining = document.getElementById('group-mining-filters');

    // Case 1: Default (rhino is false)
    state.filters.has_landable_hmc = true;
    state.miningScout = 'high';
    state.hasLargePad = true;
    state.maxArrivalDistLs = 2000;
    
    // Save settings with rhino: false
    saveModuleSettings({ exobiology: true, rhino: false });
    updateModuleVisibilityUI();

    const hiddenDisplay = groupMining.style.display;
    const filterReset1 = state.filters.has_landable_hmc;
    const scoutReset1 = state.miningScout;
    const padReset1 = state.hasLargePad;
    const distReset1 = state.maxArrivalDistLs;

    // Case 2: Turn rhino: true
    saveModuleSettings({ exobiology: true, rhino: true });
    updateModuleVisibilityUI();
    const visibleDisplay = groupMining.style.display;

    console.log(JSON.stringify({
      hiddenDisplay,
      filterReset1,
      scoutReset1,
      padReset1,
      distReset1,
      visibleDisplay
    }));
    """)
    res = json.loads(out)
    assert res["hiddenDisplay"] == "none"
    assert res["filterReset1"] is False
    assert res["scoutReset1"] == ""
    assert res["padReset1"] is False
    assert res["distReset1"] is None
    assert res["visibleDisplay"] == ""


def test_body_card_click_does_not_overwrite_target_body_id():
    """Verify clicking body cards (tree, bio view, flat list) selects body without hijacking targetBodyId."""
    out = run_js_integration_test("""
    const body1 = { body_id: 100, body_name: 'Targeted Body 100', planet_class: 'High metal content world' };
    const body2 = { body_id: 200, body_name: 'Clicked Body 200', planet_class: 'Icy body', bio_signals: 2 };

    state.currentSystemData = {
      system: { system_address: 99999, last_targeted_body_id: 100 },
      bodies: [body1, body2]
    };
    state.targetBodyId = 100;
    state.selectedBody = body1;

    // 1. Test flat list card click
    const flatContainer = document.createElement('div');
    renderFlatBodiesList(flatContainer, [body1, body2]);
    const listWrapper = flatContainer.children[0];
    const card200Flat = listWrapper.children.find(c => c.dataset && c.dataset.bodyId == 200);
    if (card200Flat && card200Flat.onclick) {
      card200Flat.onclick();
    }

    const selectedAfterFlatClick = state.selectedBody ? state.selectedBody.body_id : null;
    const targetAfterFlatClick = state.targetBodyId;

    // 2. Test bio only view card click
    const bioContainer = document.createElement('div');
    renderBioOnlyView(bioContainer, [body1, body2]);
    const bioCards = bioContainer.children;
    const card200Bio = bioCards.find(c => c.dataset && c.dataset.bodyId == 200);
    const card200HasTargetClassBefore = card200Bio ? card200Bio.classList.contains('is-current-target') : false;
    
    if (card200Bio && card200Bio.onclick) {
      card200Bio.onclick();
    }

    const selectedAfterBioClick = state.selectedBody ? state.selectedBody.body_id : null;
    const targetAfterBioClick = state.targetBodyId;

    console.log(JSON.stringify({
      selectedAfterFlatClick,
      targetAfterFlatClick,
      selectedAfterBioClick,
      targetAfterBioClick,
      card200HasTargetClassBefore
    }));
    """)
    res = json.loads(out)
    assert res["selectedAfterFlatClick"] == 200
    assert res["targetAfterFlatClick"] == 100
    assert res["selectedAfterBioClick"] == 200
    assert res["targetAfterBioClick"] == 100
    assert res["card200HasTargetClassBefore"] is False


def test_badge_style_star_and_lum_chips_trigger_events():
    """Verify star-chip and lum-chip toggle active state and update filter arrays on click."""
    out = run_js_integration_test("""
    // Create mock star and lum chips
    const chipO = document.createElement('button');
    chipO.className = 'chip star-chip';
    chipO.dataset.star = 'O';

    const chipM = document.createElement('button');
    chipM.className = 'chip star-chip';
    chipM.dataset.star = 'M';

    const chipI = document.createElement('button');
    chipI.className = 'chip lum-chip';
    chipI.dataset.lum = 'I';

    const chipV = document.createElement('button');
    chipV.className = 'chip lum-chip';
    chipV.dataset.lum = 'V';

    // Mock fetchSystems to verify it gets triggered
    let fetchCount = 0;
    fetchSystems = (opts) => { fetchCount++; return Promise.resolve(); };

    // Initialize listeners
    initStellarFilters();

    // 1. Click star-chip 'O'
    chipO.click();
    const starTypesAfter1 = [...state.starTypes];
    const isChipOActive1 = chipO.classList.contains('active');
    const fetchAfter1 = fetchCount;

    // 2. Click lum-chip 'I'
    chipI.click();
    const lumClassesAfter2 = [...state.luminosityClasses];
    const isChipIActive2 = chipI.classList.contains('active');
    const fetchAfter2 = fetchCount;

    // 3. Click star-chip 'O' again (toggle off)
    chipO.click();
    const starTypesAfter3 = [...state.starTypes];
    const isChipOActive3 = chipO.classList.contains('active');
    const fetchAfter3 = fetchCount;

    console.log(JSON.stringify({
      starTypesAfter1,
      isChipOActive1,
      fetchAfter1,
      lumClassesAfter2,
      isChipIActive2,
      fetchAfter2,
      starTypesAfter3,
      isChipOActive3,
      fetchAfter3
    }));
    """)
    res = json.loads(out)
    assert res["starTypesAfter1"] == ["O"]
    assert res["isChipOActive1"] is True
    assert res["fetchAfter1"] == 1

    assert res["lumClassesAfter2"] == ["I"]
    assert res["isChipIActive2"] is True
    assert res["fetchAfter2"] == 2

    assert res["starTypesAfter3"] == []
    assert res["isChipOActive3"] is False
    assert res["fetchAfter3"] == 3

