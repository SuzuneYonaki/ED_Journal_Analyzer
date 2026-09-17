"""
UI & i18n Consistency Automated Verification Tests.
Asserts that all i18n keys referenced in HTML exist in both Japanese and English dictionaries,
and that critical DOM IDs for live controls, tabs, and filters match between HTML and JS.
"""
import re
import os
import pytest

def test_i18n_keys_completeness():
    """Verify that required new i18n keys exist in both ja and en."""
    i18n_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        content = f.read()

    ja_match = re.search(r"ja:\s*\{(.*?)\n\s*\},", content, re.DOTALL)
    en_match = re.search(r"en:\s*\{(.*?)\n\s*\}\n\};", content, re.DOTALL)
    assert ja_match is not None, "ja dictionary must be found in i18n.js"
    assert en_match is not None, "en dictionary must be found in i18n.js"

    ja_text = ja_match.group(1)
    en_text = en_match.group(1)

    required_keys = [
        "concept_tab_explorer_short",
        "concept_tab_physics_short",
        "search_mode_label",
        "filter_first_discover",
        "filter_bookmarks",
        "filter_shared",
        "sort_live_hint",
        "sort_live_unlock_btn",
        "sort_live_resume_btn",
        "settings_landmarks_label",
        "settings_landmarks_desc",
        "lm_cmdr",
        "lm_sol",
        "lm_colonia",
        "lm_rainbow",
        "lm_eanch",
    ]

    for key in required_keys:
        assert f"{key}:" in ja_text, f"Key '{key}' must exist in ja dictionary"
        assert f"{key}:" in en_text, f"Key '{key}' must exist in en dictionary"

def test_html_ui_ids_match_js():
    """Verify that critical DOM element IDs match between index.html and app.js."""
    import jinja2
    ui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "ui"))
    js_dir = os.path.join(ui_dir, "js")

    # Verify component modularization
    components_dir = os.path.join(ui_dir, "components")
    assert os.path.isdir(components_dir), "components directory must exist"
    expected_components = ["banner.html", "header.html", "left_pane.html", "center_pane.html", "right_pane.html", "modals.html"]
    for comp in expected_components:
        assert os.path.isfile(os.path.join(components_dir, comp)), f"Component {comp} must exist"

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(ui_dir))
    html_content = env.get_template("index.html").render()

    js_modules = ["app.js", "system_list.js", "mining_view.js", "inspector.js", "utils.js"]
    js_content = ""
    for jm in js_modules:
        p = os.path.join(js_dir, jm)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                js_content += "\n" + f.read()

    critical_ids = [
        "btn-pane-tab-explorer",
        "btn-pane-tab-physics",
        "btn-live-toggle",
        "btn-accordion-live-toggle",
        "accordion-live-sync-row",
        "body-sort-wrapper",
    ]

    for elem_id in critical_ids:
        assert f'id="{elem_id}"' in html_content or f"id='{elem_id}'" in html_content, f"Element ID '{elem_id}' must exist in index.html"
        assert elem_id in js_content, f"Element ID '{elem_id}' must be referenced in app.js"

    # Landmark checkboxes verification
    landmarks = ["cmdr", "sol", "colonia", "rainbow", "eanch"]
    for lm in landmarks:
        assert f'data-landmark="{lm}"' in html_content, f"Landmark '{lm}' checkbox must exist in index.html"
        assert f"defaultLandmarkSettings" in js_content and lm in js_content, f"Landmark '{lm}' must be supported in app.js"

def test_all_components_included_in_root_index():
    """Verify that every HTML component in app/ui/components is included in root index.html."""
    ui_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "ui"))
    root_index_path = os.path.join(ui_dir, "index.html")
    with open(root_index_path, "r", encoding="utf-8") as f:
        root_content = f.read()

    components_dir = os.path.join(ui_dir, "components")
    for comp_file in os.listdir(components_dir):
        if comp_file.endswith(".html"):
            include_tag = f'include "components/{comp_file}"'
            assert include_tag in root_content, f"Component {comp_file} must be included in index.html via {include_tag}"


def test_luminosity_english_and_left_pane_tooltips():
    """Verify that luminosity labels in left_pane.html are in English, and all data-i18n-title exist in i18n."""
    left_pane_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "components", "left_pane.html")
    with open(left_pane_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Luminosity labels must be English
    expected_labels = [
        "I Supergiants",
        "II Bright Giants",
        "III Giants",
        "IV Subgiants",
        "V Main Sequence",
        "VI Subdwarfs",
        "VII Degenerate Stars"
    ]
    for label in expected_labels:
        assert label in content, f"Luminosity label '{label}' must exist in left_pane.html"

    # All data-i18n-title must exist in i18n dictionaries
    i18n_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        i18n_content = f.read()

    title_keys = re.findall(r'data-i18n-title="([^"]+)"', content)
    assert len(title_keys) > 0, "There should be data-i18n-title keys in left_pane.html"
    for tk in set(title_keys):
        assert f"{tk}:" in i18n_content, f"Tooltip key '{tk}' must exist in i18n.js"



