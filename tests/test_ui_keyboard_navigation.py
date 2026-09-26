"""
test_ui_keyboard_navigation.py - Unit tests for left pane system card keyboard navigation
Elite Dangerous Journal Analyzer
"""
import json
import shutil
import subprocess
from pathlib import Path
import pytest


def test_system_card_keyboard_css_and_markup():
    """Verifies that .system-card has focus styles in style.css and tabindex in system_list.js."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    js_path = ui_dir / "js" / "system_list.js"
    css_path = ui_dir / "css" / "style.css"

    assert js_path.exists()
    assert css_path.exists()

    js_code = js_path.read_text(encoding="utf-8")
    css_code = css_path.read_text(encoding="utf-8")

    # 1. Verify tabindex="0" set on system-card
    assert "card.setAttribute('tabindex', '0')" in js_code

    # 2. Verify keyboard navigation functions exist in system_list.js
    assert "function initSystemCardKeyboardNavigation()" in js_code
    assert "async function navigateSystemCard(direction)" in js_code
    assert "function focusCardByIndex(index)" in js_code
    assert "function isInputOrModalActive(e)" in js_code

    # 3. Verify CSS rules for focus and focus-visible
    assert ".system-card:focus" in css_code
    assert ".system-card:focus-visible" in css_code


def test_system_card_keyboard_navigation_logic():
    """Runs a Node.js simulation to verify navigateSystemCard 'down' and 'up' with pagination wrapping."""
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    system_list_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_list.js"
    test_script = f"""
    const systemList = require({json.dumps(str(system_list_path))});

    // Mock DOM and global state
    const mockSelected = [];
    const mockFocused = [];
    let fetchSystemsCalled = [];

    global.state = {{
      page: 1,
      totalPages: 3,
      selectedSystem: {{ system_address: 101 }},
      systems: [
        {{ system_address: 101, star_system: 'Alpha' }},
        {{ system_address: 102, star_system: 'Beta' }},
        {{ system_address: 103, star_system: 'Gamma' }}
      ]
    }};

    global.selectSystem = async function(addr) {{
      mockSelected.push(addr);
      const found = global.state.systems.find(s => s.system_address === addr);
      if (found) global.state.selectedSystem = found;
    }};

    global.fetchSystems = async function(opts) {{
      fetchSystemsCalled.push({{ page: global.state.page, opts }});
      if (global.state.page === 2) {{
        global.state.systems = [
          {{ system_address: 201, star_system: 'Delta' }},
          {{ system_address: 202, star_system: 'Epsilon' }}
        ];
      }} else if (global.state.page === 1) {{
        global.state.systems = [
          {{ system_address: 101, star_system: 'Alpha' }},
          {{ system_address: 102, star_system: 'Beta' }},
          {{ system_address: 103, star_system: 'Gamma' }}
        ];
      }}
    }};

    global.scrollToTopOfSystemCards = function() {{}};

    // Mock document
    const mockCards = [
      {{ focus() {{ mockFocused.push('card_0'); }}, scrollIntoView() {{}} }},
      {{ focus() {{ mockFocused.push('card_1'); }}, scrollIntoView() {{}} }},
      {{ focus() {{ mockFocused.push('card_2'); }}, scrollIntoView() {{}} }}
    ];

    global.document = {{
      activeElement: null,
      getElementById(id) {{
        if (id === 'system-list') {{
          return {{
            querySelectorAll(sel) {{ return mockCards; }}
          }};
        }}
        return null;
      }},
      querySelectorAll(sel) {{ return []; }}
    }};

    async function runTests() {{
      const results = {{}};

      // 1. ArrowRight (down) from index 0 -> selects index 1 (102)
      await systemList.navigateSystemCard('down');
      results.step1_selected = global.state.selectedSystem.system_address; // 102

      // 2. ArrowRight (down) from index 1 -> selects index 2 (103)
      await systemList.navigateSystemCard('down');
      results.step2_selected = global.state.selectedSystem.system_address; // 103

      // 3. ArrowRight (down) from index 2 (bottom of page 1) -> triggers page 2, selects top card (201)
      await systemList.navigateSystemCard('down');
      results.step3_page = global.state.page; // 2
      results.step3_selected = global.state.selectedSystem.system_address; // 201

      // 4. ArrowLeft (up) from index 0 of page 2 -> triggers page 1, selects bottom card (103)
      await systemList.navigateSystemCard('up');
      results.step4_page = global.state.page; // 1
      results.step4_selected = global.state.selectedSystem.system_address; // 103

      // 5. ArrowLeft (up) from index 2 -> selects index 1 (102)
      await systemList.navigateSystemCard('up');
      results.step5_selected = global.state.selectedSystem.system_address; // 102

      // 6. ArrowLeft (up) from index 1 -> selects index 0 (101)
      await systemList.navigateSystemCard('up');
      results.step6_selected = global.state.selectedSystem.system_address; // 101

      // 7. ArrowLeft (up) from index 0 of page 1 -> stays at page 1, index 0 (101)
      await systemList.navigateSystemCard('up');
      results.step7_page = global.state.page; // 1
      results.step7_selected = global.state.selectedSystem.system_address; // 101

      // 8. Test isInputOrModalActive
      const inputEl = {{ tagName: 'INPUT' }};
      results.input_active = systemList.isInputOrModalActive({{ target: inputEl }});

      const divEl = {{ tagName: 'DIV' }};
      results.div_active = systemList.isInputOrModalActive({{ target: divEl }});

      console.log(JSON.stringify(results));
    }}

    runTests();
    """

    res = subprocess.run(
        [node_exe, "-e", test_script],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(res.stdout)

    # 1. Downward stepping in same page
    assert data["step1_selected"] == 102
    assert data["step2_selected"] == 103

    # 2. Next page transition focuses top card (201)
    assert data["step3_page"] == 2
    assert data["step3_selected"] == 201

    # 3. Previous page transition focuses bottom card (103)
    assert data["step4_page"] == 1
    assert data["step4_selected"] == 103

    # 4. Upward stepping in same page
    assert data["step5_selected"] == 102
    assert data["step6_selected"] == 101

    # 5. Bound at page 1 top (latest system)
    assert data["step7_page"] == 1
    assert data["step7_selected"] == 101

    # 6. Input guard
    assert data["input_active"] is True
    assert data["div_active"] is False
