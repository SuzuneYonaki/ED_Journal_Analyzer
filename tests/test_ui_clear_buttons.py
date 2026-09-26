from pathlib import Path


def test_clear_buttons_markup_and_handlers():
    """Verify that clear buttons for filters, sort, date, and live settings exist and are wired."""
    base_dir = Path(__file__).resolve().parent.parent

    # 1. left_pane.html markup
    left_pane_path = base_dir / "app" / "ui" / "components" / "left_pane.html"
    left_html = left_pane_path.read_text(encoding="utf-8")

    assert 'id="btn-clear-all-filters"' in left_html, "btn-clear-all-filters must exist next to live toggle"
    assert 'id="btn-clear-sort-filters"' in left_html, "btn-clear-sort-filters must exist in sort collapsible header"
    assert 'id="badge-sort-filters"' in left_html, "badge-sort-filters must exist in sort collapsible header"
    assert 'id="btn-clear-date-top"' in left_html, "btn-clear-date-top must exist next to date preset select"
    assert 'id="btn-clear-sort-only"' in left_html, "btn-clear-sort-only must exist in sort controls section"

    # 2. app.js logic
    app_js_path = base_dir / "app" / "ui" / "js" / "app.js"
    app_js = app_js_path.read_text(encoding="utf-8")

    assert "function resetAllSearchAndFilters()" in app_js
    assert "function resetSortSettings()" in app_js
    assert "function resetDateFilter()" in app_js
    assert "btnClearAllFilters.addEventListener" in app_js
    assert "btnClearSortFilters.addEventListener" in app_js
    assert "btnClearDateTop.addEventListener" in app_js
    assert "btnClearSortOnly.addEventListener" in app_js

    # 3. system_list.js badge update
    sys_list_path = base_dir / "app" / "ui" / "js" / "system_list.js"
    sys_list = sys_list_path.read_text(encoding="utf-8")
    assert "badge-sort-filters" in sys_list

    # 4. i18n keys
    i18n_path = base_dir / "app" / "ui" / "js" / "i18n.js"
    i18n_content = i18n_path.read_text(encoding="utf-8")
    assert 'btn_clear_all: "全クリア"' in i18n_content
    assert 'btn_clear_all: "Clear All"' in i18n_content
