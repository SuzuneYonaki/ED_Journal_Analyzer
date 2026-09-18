import json
import shutil
import subprocess
from pathlib import Path
import pytest


def test_sysmap_pan_drag_multidirectional():
    """Verify that system_map.js supports horizontal, vertical, and diagonal pan dragging."""
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    js_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_map.js").as_posix()
    utils_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js").as_posix()

    test_script = f"""
    // Mock minimal browser DOM environment
    global.window = global;
    global.document = {{
        createElement: function(tag) {{
            const listeners = {{}};
            return {{
                tagName: tag,
                className: '',
                classList: {{
                    add: function(cls) {{}},
                    remove: function(cls) {{}},
                    toggle: function(cls, val) {{}}
                }},
                style: {{}},
                dataset: {{}},
                children: [],
                parentElement: null,
                scrollLeft: 0,
                scrollTop: 0,
                appendChild: function(c) {{
                    c.parentElement = this;
                    this.children.push(c);
                    return c;
                }},
                addEventListener: function(evt, handler) {{
                    listeners[evt] = listeners[evt] || [];
                    listeners[evt].push(handler);
                }},
                removeEventListener: function(evt, handler) {{
                    if (listeners[evt]) {{
                        listeners[evt] = listeners[evt].filter(h => h !== handler);
                    }}
                }},
                dispatchEvent: function(evt) {{
                    if (listeners[evt.type]) {{
                        listeners[evt.type].forEach(h => h(evt));
                    }}
                }},
                closest: function(sel) {{ return this; }}
            }};
        }}
    }};
    global.window.addEventListener = function(evt, handler) {{
        global.window._listeners = global.window._listeners || {{}};
        global.window._listeners[evt] = global.window._listeners[evt] || [];
        global.window._listeners[evt].push(handler);
    }};
    global.window.removeEventListener = function(evt, handler) {{
        if (global.window._listeners && global.window._listeners[evt]) {{
            global.window._listeners[evt] = global.window._listeners[evt].filter(h => h !== handler);
        }}
    }};
    global.state = {{
        selectedSystem: {{ star_system: "Sol" }},
        selectedBody: null,
        targetBodyId: null
    }};
    global.t = function(k) {{ return k; }};

    // Load utils.js and system_map.js
    const fs = require('fs');
    eval(fs.readFileSync('{utils_path}', 'utf8'));
    eval(fs.readFileSync('{js_path}', 'utf8'));

    const container = document.createElement('div');
    container.scrollTop = 100;
    
    // Call renderSystemMapView
    const sampleBodies = [
        {{ body_id: 0, body_name: "Sol", body_type: "Star", distance_from_arrival_ls: 0, is_star: 1 }},
        {{ body_id: 1, body_name: "Sol 1", body_type: "Planet", distance_from_arrival_ls: 100, is_star: 0 }}
    ];
    renderSystemMapView(container, [], sampleBodies);

    const mapWrapper = container.children[0];
    mapWrapper.scrollLeft = 50;
    mapWrapper.scrollTop = 50;

    // Simulate mousedown
    mapWrapper.dispatchEvent({{
        type: 'mousedown',
        button: 0,
        pageX: 200,
        pageY: 300
    }});

    // Simulate diagonal mousemove (X moves +40, Y moves +60)
    // Walk = (240 - 200) = +40, (360 - 300) = +60
    // Expected scroll: scrollLeft = 50 - 40 = 10, scrollTop = 50 - 60 = -10
    const moveListeners = global.window._listeners['mousemove'] || [];
    moveListeners.forEach(h => h({{ pageX: 240, pageY: 360 }}));

    const result = {{
        scrollLeft: mapWrapper.scrollLeft,
        scrollTop: mapWrapper.scrollTop,
        parentScrollTop: container.scrollTop,
        hasDragged: mapWrapper._hasDragged()
    }};

    // Simulate mouseup
    const upListeners = global.window._listeners['mouseup'] || [];
    upListeners.forEach(h => h({{}}));

    result.listenersRemoved = (global.window._listeners['mousemove'].length === 0);

    console.log(JSON.stringify(result));
    """

    proc = subprocess.run([node_exe, "-e", test_script], capture_output=True, text=True, encoding="utf-8", check=True)
    res = json.loads(proc.stdout)

    assert res["scrollLeft"] == 10, f"Expected scrollLeft to be 10, got {res['scrollLeft']}"
    assert res["scrollTop"] == -10, f"Expected scrollTop to be -10, got {res['scrollTop']}"
    assert res["parentScrollTop"] == 40, f"Expected parentScrollTop to be 40 (100 - 60), got {res['parentScrollTop']}"
    assert res["hasDragged"] is True, "Expected hasDragged to be true after significant movement"
    assert res["listenersRemoved"] is True, "Expected window event listeners to be cleaned up on mouseup"


def test_css_system_map_pan_rules():
    """Verify that style.css contains necessary rules for multi-directional pan dragging in System Map."""
    css_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "css" / "style.css"
    content = css_path.read_text(encoding="utf-8")

    assert ".map-content-area.is-sysmap" in content, "Missing .map-content-area.is-sysmap in style.css"
    assert ".ed-system-map-container" in content, "Missing .ed-system-map-container in style.css"
    assert "cursor: grab" in content, "Missing cursor: grab in style.css"
    assert "cursor: grabbing" in content, "Missing cursor: grabbing in style.css"
