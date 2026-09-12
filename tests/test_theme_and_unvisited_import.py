import pytest
from app.services.edsm_service import edsm_service
from pathlib import Path

def test_theme_definitions_in_style_css():
    css_path = Path("app/ui/css/style.css")
    assert css_path.exists()
    content = css_path.read_text(encoding="utf-8")
    assert '[data-theme="elite-amber"]' in content
    assert '--ed-orange: #ff7100;' in content
    assert '--ed-cyan: #ffaa33;' in content
    assert '--bg-primary: #0a0502;' in content
    assert '[data-theme="cyan-explorer"]' in content
    assert '--ed-orange: #00d2ff;' in content
    assert '--bg-primary: #040c14;' in content
    assert '.theme-selector-grid' in content
    assert '.theme-card-btn' in content

def test_theme_elements_in_index_html():
    html_path = Path("app/ui/index.html")
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert 'data-theme="default"' in content
    assert 'data-theme="elite-amber"' in content
    assert 'data-theme="cyan-explorer"' in content
    assert 'class="version-badge">v0.1.5</span>' in content
    assert "localStorage.getItem('ed_theme')" in content

def test_edsm_service_url_has_show_id():
    import inspect
    src = inspect.getsource(edsm_service.import_unvisited_system_by_name)
    assert "showId=1" in src
    src2 = inspect.getsource(edsm_service._fetch_and_update_system)
    assert "showId=1" in src2
