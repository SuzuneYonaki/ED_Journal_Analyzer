from pathlib import Path

def test_system_map_star_label_function_and_css():
    js_path = Path("app/ui/js/system_map.js")
    assert js_path.exists()
    js_content = js_path.read_text(encoding="utf-8")

    assert "function getStarLabelStyle" in js_content
    assert "star-len-1" in js_content
    assert "star-len-2" in js_content
    assert "star-len-3" in js_content
    assert "star-len-4" in js_content
    assert "star-len-long" in js_content

    # Check that createSysMapBodyElement uses getStarLabelStyle
    assert "getStarLabelStyle(iconLabel" in js_content

    css_path = Path("app/ui/css/style.css")
    assert css_path.exists()
    css_content = css_path.read_text(encoding="utf-8")

    assert ".sysmap-sphere.root-star .sysmap-icon-label" in css_content
    assert ".star-len-1" in css_content
    assert "2.2rem" in css_content
    assert "1.55rem" in css_content
    assert "-webkit-text-stroke: 1.5px #000;" in css_content
    assert "paint-order: stroke fill;" in css_content
