import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_system_list_test(script_body):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    i18n_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js"
    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    system_list_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_list.js"

    runner_script = f"""
    const fs = require('fs');

    // DOM mock environment
    function createMockElement(tag = 'div') {{
      return {{
        tagName: tag.toUpperCase(),
        innerText: '',
        _innerHTML: '',
        get innerHTML() {{ return this._innerHTML; }},
        set innerHTML(val) {{
          this._innerHTML = val;
          if (!val) this.children = [];
        }},
        value: '',
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
        _listeners: {{}},
        addEventListener(evt, cb) {{
          (this._listeners[evt] = this._listeners[evt] || []).push(cb);
        }},
        click() {{
          (this._listeners['click'] || []).forEach(cb => cb());
        }},
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
    global.selectSystem = () => Promise.resolve();
    global.fetchSystems = () => Promise.resolve();
    global.t = (k) => k;
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


def test_system_list_bilingual_switching():
    i18n_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js").as_posix()
    out = run_js_system_list_test(f"""
    const i18nMod = require('{i18n_path}');
    Object.assign(global, i18nMod);

    const testSys = {{
      system_address: 12345678,
      star_system: 'Test Sys',
      total_potential_value: 1000000,
      scanned_bodies: 5,
      total_bodies: 5,
      visit_count: 1,
      last_visited: '2026-09-16T12:00:00',
      system_state: 'Boom',
      controlling_faction: 'Pilots Federation',
      system_reserve: 'Pristine Reserves',
      system_economy: 'Refinery',
      edsm_checked: 1,
      edsm_registered: 1,
      edsm_first_discoverer: 'Commander Alpha',
      cmdr_distance_ly: 50.0,
      sol_distance_ly: 100.0,
      colonia_distance_ly: 22000.0,
      star_pos_x: 0,
      star_pos_y: 0,
      star_pos_z: 100
    }};

    // Enable faction module for testing state and economy info
    localStorage.setItem('ed_module_settings', JSON.stringify({{ faction: true }}));

    // Japanese mode
    setLanguage('ja');
    state.systems = [testSys];
    state.selectedSystem = testSys;
    state.currentSystemData = {{ system: testSys }};
    renderSystemList();
    renderSystemHeader();

    const ja_card = document.getElementById('system-list').children[0];
    const ja_card_html = ja_card ? ja_card.innerHTML : '';
    const ja_state_badge = document.getElementById('current-system-state-badge').innerHTML;
    const ja_econ_info = document.getElementById('current-system-economy-info').innerHTML;

    // English mode
    setLanguage('en');
    renderSystemList();
    renderSystemHeader();

    const en_card = document.getElementById('system-list').children[0];
    const en_card_html = en_card ? en_card.innerHTML : '';
    const en_state_badge = document.getElementById('current-system-state-badge').innerHTML;
    const en_econ_info = document.getElementById('current-system-economy-info').innerHTML;

    console.log(JSON.stringify({{
      ja_has_edsm_tip: ja_card_html.includes("EDSM登録済"),
      ja_has_boom_state: ja_state_badge.includes("好況") || ja_state_badge.includes("Boom"),
      ja_has_controlling_faction: ja_econ_info.includes("支配勢力"),
      ja_has_primary_economy: ja_econ_info.includes("主要経済"),
      en_has_edsm_tip: en_card_html.includes("Registered on EDSM"),
      en_has_boom_state: en_state_badge.includes("Boom") && !en_state_badge.includes("好況"),
      en_has_controlling_faction: en_econ_info.includes("Controlling Faction"),
      en_has_primary_economy: en_econ_info.includes("Primary Economy")
    }}));
    """)
    res = json.loads(out)
    assert res["ja_has_edsm_tip"] is True
    assert res["ja_has_boom_state"] is True
    assert res["ja_has_controlling_faction"] is True
    assert res["ja_has_primary_economy"] is True

    assert res["en_has_edsm_tip"] is True
    assert res["en_has_boom_state"] is True
    assert res["en_has_controlling_faction"] is True
    assert res["en_has_primary_economy"] is True


def test_header_update_notification_ui_state():
    out = run_js_system_list_test("""
    const headerGroup = document.getElementById('header-logged-group');
    const btnToggle = document.getElementById('btn-toggle-header-stats');
    const banner = document.getElementById('header-update-banner');
    const indicator = document.getElementById('header-update-indicator');
    const versionEl = document.getElementById('header-update-version');
    const summaryEl = document.getElementById('header-update-summary');
    const linkEl = document.getElementById('header-update-link');

    initHeaderStatsCollapse();

    // 1. Initial state without update
    state.updateInfo = { has_update: false };
    renderHeaderUpdateState();
    const initial_has_class = headerGroup.classList.contains('has-new-version');
    const initial_ind_disp = indicator.style.display;
    const initial_ban_disp = banner.style.display;

    // 2. Update exists and header is expanded
    state.updateInfo = {
      has_update: true,
      latest_version: 'v0.9.0',
      summary: 'New features and long descriptive summary line',
      release_url: 'https://github.com/test/release'
    };
    renderHeaderUpdateState();
    const exp_has_class = headerGroup.classList.contains('has-new-version');
    const exp_ind_disp = indicator.style.display;
    const exp_ban_disp = banner.style.display;

    // 3. Toggle to collapsed state
    btnToggle.click();
    const col_is_collapsed = headerGroup.classList.contains('collapsed');
    const col_ind_disp = indicator.style.display;
    const col_ban_disp = banner.style.display;
    const col_version = versionEl.textContent;
    const col_summary = summaryEl.textContent;
    const col_title = summaryEl.title;
    const col_link = linkEl.href;

    // 4. Toggle back to expanded
    btnToggle.click();
    const exp2_ind_disp = indicator.style.display;
    const exp2_ban_disp = banner.style.display;

    console.log(JSON.stringify({
      initial_has_class,
      initial_ind_disp,
      initial_ban_disp,
      exp_has_class,
      exp_ind_disp,
      exp_ban_disp,
      col_is_collapsed,
      col_ind_disp,
      col_ban_disp,
      col_version,
      col_summary,
      col_title,
      col_link,
      exp2_ind_disp,
      exp2_ban_disp
    }));
    """)
    res = json.loads(out)
    assert res["initial_has_class"] is False
    assert res["initial_ind_disp"] == "none"
    assert res["initial_ban_disp"] == "none"

    # Expanded with update: indicator visible, banner hidden
    assert res["exp_has_class"] is True
    assert res["exp_ind_disp"] == "inline-flex"
    assert res["exp_ban_disp"] == "none"

    # Collapsed with update: indicator hidden, banner visible with summary
    assert res["col_is_collapsed"] is True
    assert res["col_ind_disp"] == "none"
    assert res["col_ban_disp"] == "flex"
    assert res["col_version"] == "v0.9.0"
    assert "New features" in res["col_summary"]
    assert "New features" in res["col_title"]
    assert res["col_link"] == "https://github.com/test/release"

    # Toggled back: indicator visible, banner hidden
    assert res["exp2_ind_disp"] == "inline-flex"
    assert res["exp2_ban_disp"] == "none"


