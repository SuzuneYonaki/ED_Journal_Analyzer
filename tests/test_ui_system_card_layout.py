import os
from pathlib import Path

def test_system_card_markup_and_css_structure():
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    js_path = ui_dir / "js" / "system_list.js"
    css_path = ui_dir / "css" / "style.css"

    assert js_path.exists()
    assert css_path.exists()

    js_code = js_path.read_text(encoding="utf-8")
    css_code = css_path.read_text(encoding="utf-8")

    # 1. Verify system-card-sub-header and system-card-visited exist in system_list.js
    assert "system-card-sub-header" in js_code
    assert "system-card-visited" in js_code

    # 2. Verify visited_meta is in system-card-visited, not squeezed inside system-card-meta
    assert "class=\"system-card-visited\">${t('visited_meta')}" in js_code

    # 3. Verify CSS rules for sub-header and visited
    assert ".system-card-sub-header" in css_code
    assert ".system-card-visited" in css_code

    # 4. Verify tag-badge overflow protection to prevent clipping
    assert "max-width: 100%" in css_code
    assert "text-overflow: ellipsis" in css_code
    assert "overflow: hidden" in css_code
