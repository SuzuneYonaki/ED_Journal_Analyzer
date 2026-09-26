from pathlib import Path


def test_star_luminosity_and_magnitude_integration():
    """Verify that stellar luminosity and magnitude badges are rendered across all panels."""
    base_dir = Path(__file__).resolve().parent.parent

    # 1. API: get_systems returns main_star_luminosity and main_star_absolute_magnitude
    api_path = base_dir / "app" / "server" / "api.py"
    api_content = api_path.read_text(encoding="utf-8")
    assert "main_star_luminosity" in api_content
    assert "main_star_absolute_magnitude" in api_content

    # 2. Left pane system list card: main star badge displays luminosity & absolute magnitude
    sys_list_path = base_dir / "app" / "ui" / "js" / "system_list.js"
    sys_list_content = sys_list_path.read_text(encoding="utf-8")
    assert "main_star_luminosity" in sys_list_content
    assert "main_star_absolute_magnitude" in sys_list_content
    assert "Mag</span>" in sys_list_content

    # 3. System Map: star nodes display luminosity class and magnitude badges
    sys_map_path = base_dir / "app" / "ui" / "js" / "system_map.js"
    sys_map_content = sys_map_path.read_text(encoding="utf-8")
    assert "body.star_type" in sys_map_content
    assert "body.luminosity" in sys_map_content
    assert "body.absolute_magnitude" in sys_map_content
    assert "sysmap-mini-badge lum" in sys_map_content

    # 4. Celestial Flat View in app.js: star cards display luminosity and magnitude badges
    app_js_path = base_dir / "app" / "ui" / "js" / "app.js"
    app_js_content = app_js_path.read_text(encoding="utf-8")
    assert "body.star_type" in app_js_content
    assert "body.luminosity" in app_js_content
    assert "body.absolute_magnitude" in app_js_content

    # 5. Inspector in inspector.js: star subtitle reflects luminosity and magnitude
    inspector_path = base_dir / "app" / "ui" / "js" / "inspector.js"
    inspector_content = inspector_path.read_text(encoding="utf-8")
    assert "b.luminosity" in inspector_content
    assert "b.absolute_magnitude" in inspector_content
