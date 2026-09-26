"""
test_ui_update_link.py - Tests for GitHub release URL embedding and top-left update notification button
Elite Dangerous Journal Analyzer
"""
from pathlib import Path


def test_header_update_notification_markup_links():
    """Verifies that update notification text strings in header.html are wrapped in clickable anchor links and top-left button exists."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    header_html_path = ui_dir / "components" / "header.html"
    assert header_html_path.exists()

    content = header_html_path.read_text(encoding="utf-8")

    # 1. Top-left dedicated update notification button exists before header-logged-group
    btn_pos = content.find('id="header-left-update-btn"')
    group_pos = content.find('id="header-logged-group"')
    assert btn_pos != -1, "header-left-update-btn not found"
    assert group_pos != -1, "header-logged-group not found"
    assert btn_pos < group_pos, "header-left-update-btn must be placed at the far left before header-logged-group"

    assert 'class="header-left-update-btn"' in content
    assert 'id="header-left-update-version"' in content

    # 2. Indicator is an anchor link with target="_blank"
    assert '<a id="header-update-indicator"' in content
    assert 'class="header-update-indicator"' in content
    assert 'target="_blank"' in content
    assert 'rel="noopener noreferrer"' in content

    # 3. Banner text (badge + version + summary) is wrapped inside header-update-banner-link
    assert '<a id="header-update-banner-link"' in content
    assert 'class="header-update-banner-link"' in content

    banner_section = content[content.find('id="header-update-banner"'):content.find('<!-- Manual Log Rescan Button')]
    assert 'header-update-banner-link' in banner_section
    assert 'header-update-version' in banner_section
    assert 'header-update-summary' in banner_section
    assert 'header-update-link' in banner_section


def test_header_update_notification_script_logic():
    """Verifies that system_list.js assigns release_url to left update button, banner link, and indicator."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    js_path = ui_dir / "js" / "system_list.js"
    assert js_path.exists()

    js_code = js_path.read_text(encoding="utf-8")

    # 1. Elements retrieved
    assert "const leftUpdateBtn = document.getElementById('header-left-update-btn');" in js_code
    assert "const leftUpdateVersion = document.getElementById('header-left-update-version');" in js_code
    assert "const bannerLink = document.getElementById('header-update-banner-link');" in js_code
    assert "const indicator = document.getElementById('header-update-indicator');" in js_code

    # 2. Top-left button displayed and configured on update
    assert "leftUpdateBtn.style.display = 'inline-flex';" in js_code
    assert "leftUpdateBtn.href = updateInfo.release_url;" in js_code
    assert "leftUpdateBtn.style.display = 'none';" in js_code

    # 3. release_url assigned to indicator.href & bannerLink.href
    assert "indicator.href = updateInfo.release_url;" in js_code
    assert "bannerLink.href = updateInfo.release_url;" in js_code

    # 4. stopPropagation on indicator to prevent triggering header collapse toggle
    assert "indicatorEl.addEventListener('click', (e) => {" in js_code
    assert "e.stopPropagation();" in js_code


def test_header_update_notification_css_styles():
    """Verifies that style.css provides styles for top-left update button and banner link."""
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"
    css_path = ui_dir / "css" / "style.css"
    assert css_path.exists()

    css_code = css_path.read_text(encoding="utf-8")

    # 1. Top-left update button styling
    assert ".header-left-update-btn" in css_code
    assert ".header-left-update-btn:hover" in css_code
    assert ".header-left-update-btn .left-update-version" in css_code

    # 2. Banner link styling
    assert ".header-update-banner-link" in css_code
    assert ".header-update-banner-link:hover .update-summary" in css_code
    assert ".header-update-banner-link:hover .update-badge" in css_code
    assert ".header-update-indicator:hover" in css_code
