"""
test_ui_keyboard_navigation.py - Fast unit tests for UI keyboard navigation & shortcuts
Elite Dangerous Journal Analyzer

Pure Python static analysis tests without external subprocess overhead.
"""
import re
from pathlib import Path


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
    """Verifies left pane arrow key navigation logic, page transitions, and input guards in system_list.js."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    js_path = ui_dir / "js" / "system_list.js"
    assert js_path.exists()

    js_code = js_path.read_text(encoding="utf-8")

    # 1. Keydown event listener handles ArrowRight and ArrowLeft
    assert "e.key === 'ArrowRight'" in js_code
    assert "e.key === 'ArrowLeft'" in js_code
    assert "navigateSystemCard('down')" in js_code
    assert "navigateSystemCard('up')" in js_code

    # 2. Input/modal guard
    assert "if (isInputOrModalActive(e)) return;" in js_code
    assert "tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT'" in js_code
    assert "target.isContentEditable" in js_code

    # 3. Down navigation logic (next card or next page top card)
    assert "if (direction === 'down')" in js_code
    assert "state.page < state.totalPages" in js_code
    assert "focusCardByIndex(0)" in js_code

    # 4. Up navigation logic (prev card or prev page bottom card, bounded at page 1 top)
    assert "if (direction === 'up')" in js_code
    assert "state.page > 1" in js_code
    assert "focusCardByIndex(lastIdx)" in js_code

    # 5. Exported for modular use
    assert "navigateSystemCard" in js_code
    assert "initSystemCardKeyboardNavigation" in js_code


def test_center_pane_number_shortcuts_logic():
    """Verifies that number keys 1-6 switch center pane views in order."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    app_js_path = ui_dir / "js" / "app.js"
    assert app_js_path.exists()

    app_js = app_js_path.read_text(encoding="utf-8")

    # 1. Verify switchCenterPaneView function & module checks
    assert "function switchCenterPaneView(viewName)" in app_js
    assert "state.currentView = viewName;" in app_js
    assert "updateViewButtons();" in app_js
    assert "renderCurrentView();" in app_js

    # 2. Key mapping verification: 1-6, Numpad, and Full-width numbers
    expected_mappings = {
        '1': 'sysmap',
        'Digit1': 'sysmap',
        'Numpad1': 'sysmap',
        '１': 'sysmap',
        '2': 'flat',
        'Digit2': 'flat',
        'Numpad2': 'flat',
        '２': 'flat',
        '3': 'orrery',
        'Digit3': 'orrery',
        'Numpad3': 'orrery',
        '３': 'orrery',
        '4': 'bio',
        'Digit4': 'bio',
        'Numpad4': 'bio',
        '４': 'bio',
        '5': 'visits',
        'Digit5': 'visits',
        'Numpad5': 'visits',
        '５': 'visits',
        '6': 'physics',
        'Digit6': 'physics',
        'Numpad6': 'physics',
        '６': 'physics',
    }
    assert "const CENTER_PANE_TAB_KEY_MAP =" in app_js
    for key, view in expected_mappings.items():
        assert f"'{key}': '{view}'" in app_js

    # 3. Guard conditions in initCenterPaneTabShortcuts
    assert "function initCenterPaneTabShortcuts()" in app_js
    assert "if (e.ctrlKey || e.altKey || e.metaKey) return;" in app_js
    assert "e.preventDefault();" in app_js
    assert "switchCenterPaneView(targetView);" in app_js

    # 4. Exports in window & module.exports
    assert "window.switchCenterPaneView = switchCenterPaneView;" in app_js
    assert "window.initCenterPaneTabShortcuts = initCenterPaneTabShortcuts;" in app_js
    assert "switchCenterPaneView," in app_js
    assert "initCenterPaneTabShortcuts," in app_js


def test_fsdjump_auto_switch_to_sysmap():
    """Verifies that FSDJump automatically resets center pane view to sysmap (System)."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    app_js_path = ui_dir / "js" / "app.js"
    assert app_js_path.exists()

    app_js = app_js_path.read_text(encoding="utf-8")

    # 1. Verify handleLiveJournalEvent exists
    assert "function handleLiveJournalEvent(eventName, eventData)" in app_js

    # 2. Extract the FSDJump / Location / CarrierJump block
    jump_match = re.search(
        r"else if\s*\(\s*eventName\s*===\s*'FSDJump'\s*\|\|\s*eventName\s*===\s*'Location'\s*\|\|\s*eventName\s*===\s*'CarrierJump'\s*\)\s*\{([^}]+)\}",
        app_js
    )
    assert jump_match is not None, "FSDJump handler block not found"
    jump_body = jump_match.group(1)

    # 3. Verify switchCenterPaneView('sysmap') is called inside jump block
    assert "switchCenterPaneView('sysmap');" in jump_body

    # 4. Verify regular scan events do NOT call switchCenterPaneView
    scan_match = re.search(
        r"else if\s*\(\s*eventName\s*===\s*'Scan'\s*\|\|\s*eventName\s*===\s*'SAAScanComplete'.*?\)\s*\{([^}]+)\}",
        app_js
    )
    assert scan_match is not None, "Scan handler block not found"
    scan_body = scan_match.group(1)
    assert "switchCenterPaneView" not in scan_body
