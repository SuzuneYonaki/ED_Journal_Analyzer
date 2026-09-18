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
                clientWidth: 800,
                clientHeight: 600,
                getBoundingClientRect: function() {{
                    return {{ left: 0, top: 0, width: 800, height: 600 }};
                }},
                appendChild: function(c) {{
                    c.parentElement = this;
                    this.children.push(c);
                    return c;
                }},
                setAttribute: function(k, v) {{ this[k] = v; }},
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
        targetBodyId: null,
        sysmapZoom: 1.0
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


def test_sysmap_wheel_zoom_and_controls():
    """Verify that system_map.js supports cursor-anchored wheel zooming, limits (0.4-2.0), and controls."""
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    js_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_map.js").as_posix()
    utils_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js").as_posix()

    test_script = f"""
    const fs = require('fs');
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
                clientWidth: 800,
                clientHeight: 600,
                getBoundingClientRect: function() {{
                    return {{ left: 0, top: 0, width: 800, height: 600 }};
                }},
                appendChild: function(c) {{
                    c.parentElement = this;
                    this.children.push(c);
                    return c;
                }},
                setAttribute: function(k, v) {{ this[k] = v; }},
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
                closest: function(sel) {{ return null; }}
            }};
        }}
    }};
    global.window.addEventListener = function(evt, handler) {{}};
    global.window.removeEventListener = function(evt, handler) {{}};
    global.state = {{
        selectedSystem: {{ star_system: "Sol" }},
        selectedBody: null,
        targetBodyId: null,
        sysmapZoom: 1.0
    }};
    global.t = function(k) {{ return k; }};

    eval(fs.readFileSync('{utils_path}', 'utf8'));
    eval(fs.readFileSync('{js_path}', 'utf8'));

    const container = document.createElement('div');
    const sampleBodies = [
        {{ body_id: 0, body_name: "Sol", body_type: "Star", distance_from_arrival_ls: 0, is_star: 1 }},
        {{ body_id: 1, body_name: "Sol 1", body_type: "Planet", distance_from_arrival_ls: 100, is_star: 0 }}
    ];
    renderSystemMapView(container, [], sampleBodies);

    const mapWrapper = container.children[0];
    const controls = container.children[1];
    const stage = mapWrapper.children[0];

    // Initial zoom
    const initialZoom = global.state.sysmapZoom;

    // Simulate wheel zoom in (deltaY: -100) at center (400, 300)
    mapWrapper.dispatchEvent({{
        type: 'wheel',
        deltaY: -100,
        clientX: 400,
        clientY: 300,
        preventDefault: function() {{}}
    }});
    const zoomedIn = global.state.sysmapZoom;

    // Simulate multiple zoom ins to test upper limit (2.0)
    for (let i = 0; i < 20; i++) {{
        mapWrapper.dispatchEvent({{
            type: 'wheel',
            deltaY: -100,
            clientX: 400,
            clientY: 300,
            preventDefault: function() {{}}
        }});
    }}
    const maxZoom = global.state.sysmapZoom;

    // Simulate multiple zoom outs to test lower limit (0.4)
    for (let i = 0; i < 40; i++) {{
        mapWrapper.dispatchEvent({{
            type: 'wheel',
            deltaY: 100,
            clientX: 400,
            clientY: 300,
            preventDefault: function() {{}}
        }});
    }}
    const minZoom = global.state.sysmapZoom;

    // Simulate middle click reset (button: 1)
    mapWrapper.dispatchEvent({{
        type: 'auxclick',
        button: 1,
        preventDefault: function() {{}}
    }});
    const resetZoom = global.state.sysmapZoom;

    console.log(JSON.stringify({{
        initialZoom,
        zoomedIn,
        maxZoom,
        minZoom,
        resetZoom,
        hasControls: Boolean(controls),
        hasStage: Boolean(stage && stage.className === 'sysmap-zoom-stage')
    }}));
    """

    proc = subprocess.run([node_exe, "-e", test_script], capture_output=True, text=True, encoding="utf-8", check=True)
    res = json.loads(proc.stdout)

    assert res["initialZoom"] == 1.0
    assert res["zoomedIn"] > 1.0, f"Expected zoom in to increase zoom, got {res['zoomedIn']}"
    assert res["maxZoom"] <= 2.0, f"Expected max zoom limit <= 2.0, got {res['maxZoom']}"
    assert res["minZoom"] >= 0.4, f"Expected min zoom limit >= 0.4, got {res['minZoom']}"
    assert res["resetZoom"] == 1.0, f"Expected reset zoom to be 1.0, got {res['resetZoom']}"
    assert res["hasControls"] is True
    assert res["hasStage"] is True


def test_css_system_map_pan_and_zoom_rules():
    """Verify that style.css contains necessary rules for multi-directional pan dragging and zoom in System Map."""
    css_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "css" / "style.css"
    content = css_path.read_text(encoding="utf-8")

    assert ".map-content-area.is-sysmap" in content, "Missing .map-content-area.is-sysmap in style.css"
    assert ".ed-system-map-container" in content, "Missing .ed-system-map-container in style.css"
    assert ".sysmap-zoom-stage" in content, "Missing .sysmap-zoom-stage in style.css"
    assert ".sysmap-zoom-controls" in content, "Missing .sysmap-zoom-controls in style.css"
    assert "cursor: grab" in content, "Missing cursor: grab in style.css"
    assert "cursor: grabbing" in content, "Missing cursor: grabbing in style.css"
