import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_share_warning_test(script_body):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    i18n_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js"
    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    sys_list_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_list.js"
    app_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "app.js"

    runner_script = f"""
    const fs = require('fs');

    function createMockElement(tag = 'div') {{
      return {{
        tagName: tag.toUpperCase(),
        innerText: '',
        value: '',
        title: '',
        checked: false,
        style: {{ display: 'none' }},
        children: [],
        dataset: {{}},
        classList: {{
          _classes: new Set(),
          add(c) {{ this._classes.add(c); }},
          remove(c) {{ this._classes.delete(c); }},
          toggle(c) {{ if (this._classes.has(c)) this._classes.delete(c); else this._classes.add(c); }},
          contains(c) {{ return this._classes.has(c); }}
        }},
        appendChild(child) {{ this.children.push(child); }},
        querySelectorAll() {{ return []; }},
        querySelector() {{ return null; }},
        setAttribute() {{}},
        removeAttribute() {{}},
        getAttribute() {{ return null; }},
        _listeners: {{}},
        addEventListener(evt, cb) {{
          (this._listeners[evt] = this._listeners[evt] || []).push(cb);
        }},
        click() {{
          (this._listeners['click'] || []).forEach(cb => cb({{ stopPropagation: () => {{}}, target: this }}));
        }}
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

    const docListeners = {{}};
    global.document = {{
      documentElement: createMockElement('html'),
      getElementById: (id) => getOrCreateEl(id),
      querySelectorAll: () => [],
      querySelector: () => null,
      createElement: (tag) => createMockElement(tag),
      addEventListener: (evt, cb) => {{
        (docListeners[evt] = docListeners[evt] || []).push(cb);
      }}
    }};
    global.window = global;
    global.window.location = {{ protocol: 'http:', host: 'localhost:8686' }};
    global.window.addEventListener = () => {{}};
    global.window.removeEventListener = () => {{}};
    global.localStorage = {{
      _data: {{}},
      getItem(k) {{ return this._data[k] || null; }},
      setItem(k, v) {{ this._data[k] = String(v); }},
      removeItem(k) {{ delete this._data[k]; }}
    }};
    global.state = {{ selectedSystem: {{ system_address: 12345, star_system: 'Sol' }}, systems: [] }};

    // Load prerequisites
    const i18nCode = fs.readFileSync({json.dumps(str(i18n_path))}, 'utf-8');
    eval(i18nCode);
    const utilsCode = fs.readFileSync({json.dumps(str(utils_path))}, 'utf-8');
    eval(utilsCode);
    const sysListCode = fs.readFileSync({json.dumps(str(sys_list_path))}, 'utf-8');
    eval(sysListCode);

    // Mock fetch and stubs
    global.fetch = () => Promise.resolve({{ ok: true, json: () => Promise.resolve({{}}) }});
    global.renderSystemList = () => {{}};
    global.renderSystemHeader = () => {{}};
    global.renderBodyInspector = () => {{}};
    global.renderStellarBodyInspector = () => {{}};
    global.updateModuleVisibilityUI = () => {{}};
    global.initSettingsModal = () => {{}};
    global.initExportImportModals = () => {{}};
    global.initMiningSiteModal = () => {{}};
    global.fetchGlobalStats = () => Promise.resolve();
    global.fetchSystems = () => Promise.resolve();
    global.checkScanOnStartup = () => Promise.resolve();

    // Load and execute app.js
    const appCode = fs.readFileSync({json.dumps(str(app_path))}, 'utf-8');
    eval(appCode);

    // Fire DOMContentLoaded
    (docListeners['DOMContentLoaded'] || []).forEach(cb => cb());

    {script_body}
    """

    res = subprocess.run(
        [node_exe, "-e", runner_script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10
    )
    if res.returncode != 0:
        raise RuntimeError(f"Node execution failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
    return res.stdout


def test_cmdr_data_share_warning_lifecycle():
    out = run_js_share_warning_test("""
    const btnShareToggle = document.getElementById('btn-share-dropdown-toggle');
    const shareMenu = document.getElementById('share-dropdown-menu');
    const modalShareWarning = document.getElementById('modal-share-warning');
    const btnCancel = document.getElementById('btn-cancel-share-warning');
    const btnConfirm = document.getElementById('btn-confirm-share-warning');
    const cbDismiss = document.getElementById('cb-share-warning-dismiss');
    const btnReset = document.getElementById('btn-reset-share-warning');

    // 1. Initial 1st click without dismissal
    btnShareToggle.click();
    const step1_modal_disp = modalShareWarning.style.display;
    const step1_menu_disp = shareMenu.style.display;
    const step1_dismissed = localStorage.getItem('ed_share_warning_dismissed');

    // 2. Cancel without checking dismiss
    btnCancel.click();
    const step2_modal_disp = modalShareWarning.style.display;
    const step2_dismissed = localStorage.getItem('ed_share_warning_dismissed');

    // 2b. 2nd click without dismissal still pops up modal
    btnShareToggle.click();
    const step2b_modal_disp = modalShareWarning.style.display;

    // 3. Confirm WITH checkbox checked
    cbDismiss.checked = true;
    btnConfirm.click();
    const step3_modal_disp = modalShareWarning.style.display;
    const step3_menu_disp = shareMenu.style.display;
    const step3_dismissed = localStorage.getItem('ed_share_warning_dismissed');

    // 4. 3rd click (after dismissal) toggles menu directly without warning modal
    shareMenu.style.display = 'none'; // reset menu state
    btnShareToggle.click();
    const step4_modal_disp = modalShareWarning.style.display;
    const step4_menu_disp = shareMenu.style.display;

    // 5. Reset warning in settings
    btnReset.click();
    const step5_dismissed = localStorage.getItem('ed_share_warning_dismissed');

    // 6. Click after reset pops up modal again
    shareMenu.style.display = 'none';
    btnShareToggle.click();
    const step6_modal_disp = modalShareWarning.style.display;
    const step6_menu_disp = shareMenu.style.display;

    console.log(JSON.stringify({
      step1_modal_disp,
      step1_menu_disp,
      step1_dismissed,
      step2_modal_disp,
      step2_dismissed,
      step2b_modal_disp,
      step3_modal_disp,
      step3_menu_disp,
      step3_dismissed,
      step4_modal_disp,
      step4_menu_disp,
      step5_dismissed,
      step6_modal_disp,
      step6_menu_disp
    }));
    process.exit(0);
    """)
    res = json.loads(out)

    # Step 1: First click shows modal and keeps menu hidden
    assert res["step1_modal_disp"] == "flex"
    assert res["step1_menu_disp"] == "none"
    assert res["step1_dismissed"] is None

    # Step 2: Cancel closes modal and does not set localStorage
    assert res["step2_modal_disp"] == "none"
    assert res["step2_dismissed"] is None
    assert res["step2b_modal_disp"] == "flex"

    # Step 3: Confirm with checkbox dismisses warning and opens menu
    assert res["step3_modal_disp"] == "none"
    assert res["step3_menu_disp"] == "flex"
    assert res["step3_dismissed"] == "true"

    # Step 4: After dismissal, clicking opens menu directly without modal
    assert res["step4_modal_disp"] == "none"
    assert res["step4_menu_disp"] == "flex"

    # Step 5 & 6: Resetting warning re-enables modal
    assert res["step5_dismissed"] is None
    assert res["step6_modal_disp"] == "flex"
    assert res["step6_menu_disp"] == "none"
