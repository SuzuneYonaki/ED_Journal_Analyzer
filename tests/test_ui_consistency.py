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


def test_ring_and_barycenter_i18n_keys():
    """Verify that ring, belt, and barycenter keys exist in both ja and en dictionaries."""
    i18n_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        content = f.read()

    ja_match = re.search(r"ja:\s*\{(.*?)\n\s*\},", content, re.DOTALL)
    en_match = re.search(r"en:\s*\{(.*?)\n\s*\}\n\};", content, re.DOTALL)
    assert ja_match and en_match

    keys = [
        "barycenter_multi",
        "barycenter_binary",
        "ring_belt_label",
        "ring_ring_label",
        "ring_or_belt_label",
        "ring_hotspot_title",
        "bookmark_alias_title",
        "no_bodies"
    ]
    for k in keys:
        assert f"{k}:" in ja_match.group(1), f"Key '{k}' must exist in ja"
        assert f"{k}:" in en_match.group(1), f"Key '{k}' must exist in en"

    # Verify that app.js does not hardcode Japanese nameJa in ring badge template
    app_js_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "js", "app.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        app_js = f.read()
    assert "${info.nameJa}ベルト" not in app_js, "app.js must not hardcode '${info.nameJa}ベルト'"
    assert "${info.nameJa}環" not in app_js, "app.js must not hardcode '${info.nameJa}環'"


def test_settings_modal_i18n_keys():
    """Verify that all i18n keys used in Settings modal exist in both ja and en dictionaries."""
    from bs4 import BeautifulSoup
    modals_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "components", "modals.html")
    with open(modals_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")
    modal = soup.find(id="settings-modal")
    assert modal is not None, "#settings-modal must exist in modals.html"

    found_keys = set()
    for el in modal.find_all(True):
        for attr in ["data-i18n", "data-i18n-html", "data-i18n-title", "data-i18n-placeholder"]:
            if el.has_attr(attr):
                found_keys.add(el[attr])

    assert len(found_keys) >= 25, f"Expected at least 25 i18n keys in settings modal, found {len(found_keys)}"

    i18n_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        i18n_content = f.read()

    ja_match = re.search(r"ja:\s*\{(.*?)\n\s*\},", i18n_content, re.DOTALL)
    en_match = re.search(r"en:\s*\{(.*?)\n\s*\}\n\};", i18n_content, re.DOTALL)
    assert ja_match and en_match

    ja_text = ja_match.group(1)
    en_text = en_match.group(1)

    for k in found_keys:
        assert f"{k}:" in ja_text, f"Key '{k}' used in settings modal must exist in ja dictionary"
        assert f"{k}:" in en_text, f"Key '{k}' used in settings modal must exist in en dictionary"


def test_all_components_unlocalized_audit():
    """Verify that no unlocalized Japanese text/title/placeholder remains in any HTML component."""
    import glob
    from bs4 import BeautifulSoup, NavigableString, Comment

    jp_regex = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
    components_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "ui", "components"))
    html_files = glob.glob(os.path.join(components_dir, "*.html"))
    assert len(html_files) >= 5, "Must find at least 5 component HTML files"

    unlocalized = []
    for file_path in html_files:
        with open(file_path, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        # 1. Check title attributes
        for tag in soup.find_all(lambda t: t.has_attr("title")):
            title_val = tag["title"]
            if jp_regex.search(title_val) and not tag.has_attr("data-i18n-title"):
                unlocalized.append((os.path.basename(file_path), "title", str(tag)[:60], title_val))

        # 2. Check placeholder attributes
        for tag in soup.find_all(lambda t: t.has_attr("placeholder")):
            ph_val = tag["placeholder"]
            if jp_regex.search(ph_val) and not tag.has_attr("data-i18n-placeholder"):
                unlocalized.append((os.path.basename(file_path), "placeholder", str(tag)[:60], ph_val))

        # 3. Check text nodes
        for text_node in soup.find_all(string=True):
            if not isinstance(text_node, NavigableString) or isinstance(text_node, Comment):
                continue
            text_str = text_node.strip()
            if not text_str or not jp_regex.search(text_str):
                continue

            curr = text_node.parent
            has_i18n = False
            while curr:
                if curr.has_attr and (curr.has_attr("data-i18n") or curr.has_attr("data-i18n-html")):
                    has_i18n = True
                    break
                curr = curr.parent

            if not has_i18n:
                parent_id = text_node.parent.get("id", "") if text_node.parent.has_attr("id") else ""
                if "btn-modal-lang-ja" in parent_id or "btn-modal-lang-en" in parent_id:
                    continue
                unlocalized.append((os.path.basename(file_path), "text", str(text_node.parent)[:60], text_str))

    assert unlocalized == [], f"Found unlocalized items: {unlocalized}"


def test_cmdr_location_integrated_in_header_logged_group():
    """Verify that stat-cmdr-container is nested inside header-logged-group and header-stats-content."""
    from bs4 import BeautifulSoup
    header_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "components", "header.html")
    with open(header_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    header_logged_group = soup.find(id="header-logged-group")
    assert header_logged_group is not None, "header-logged-group must exist"

    stats_content = header_logged_group.find(id="header-stats-content")
    assert stats_content is not None, "header-stats-content must exist inside header-logged-group"

    cmdr_container = stats_content.find(id="stat-cmdr-container")
    assert cmdr_container is not None, "stat-cmdr-container must be integrated inside header-stats-content"
    assert cmdr_container.find(id="stat-cmdr-loc") is not None, "stat-cmdr-loc must be inside stat-cmdr-container"


def test_tts_terms_and_disclaimer_ui():
    """Verify that tts-terms-container exists and contains the required unverified disclaimer."""
    from bs4 import BeautifulSoup
    modals_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "components", "modals.html")
    with open(modals_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    terms_container = soup.find(id="tts-terms-container")
    assert terms_container is not None, "tts-terms-container must exist in modals.html"

    policy_status = terms_container.find(id="tts-policy-status")
    assert policy_status is not None, "tts-policy-status element must exist inside tts-terms-container"
    assert policy_status.get("data-i18n") == "tts_terms_unverified_notice"

    # Verify i18n text content in i18n.js
    i18n_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        i18n_content = f.read()

    assert "確認できないものについては各TTSおよびキャラクター提供元の利用規約をご覧ください" in i18n_content
    assert "Please refer to the terms of use of each TTS and character provider for any unverified voices" in i18n_content

