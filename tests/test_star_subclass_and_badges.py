import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
import pytest

from app.db.database import init_db
from app.parser.journal_parser import JournalParser


def test_format_star_spectral_class_and_names():
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    runner_script = f"""
    const fs = require('fs');
    global.window = global;
    const code = fs.readFileSync({json.dumps(str(utils_path))}, 'utf8');
    eval(code);

    console.log(JSON.stringify({{
        a6: formatStarSpectralClass("A", 6, ""),
        a7: formatStarSpectralClass("A", 7, null),
        b0_3b: formatStarSpectralClass("B", 0, "IIIB"),
        g2_v: formatStarSpectralClass("G", 2, "V"),
        m_v: formatStarSpectralClass("M", null, "V"),
        g_v_name: getStarTypeName("G", "V"),
        b_3b_name: getStarTypeName("B", "IIIB")
    }}));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, encoding="utf-8", check=True)
    res = json.loads(proc.stdout)

    assert res["a6"] == "A6"
    assert res["a7"] == "A7"
    assert res["b0_3b"] == "B0 IIIB"
    assert res["g2_v"] == "G2 V"
    assert res["m_v"] == "M V"
    assert "白黄色" in res["g_v_name"]
    assert "主系列星" in res["g_v_name"]


def test_subclass_db_storage_and_parsing():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn, force=True)

    parser = JournalParser(conn)
    sys_addr = 5544332211
    sys_name = "Subclass Test System"

    fsd_jump = {
        "event": "FSDJump",
        "timestamp": "2026-10-26T00:00:00Z",
        "StarSystem": sys_name,
        "SystemAddress": sys_addr,
        "StarPos": [10.0, 20.0, 30.0]
    }
    parser.process_journal_line(json.dumps(fsd_jump))

    # Star scan with Subclass: 6 (A6 V)
    star_scan = {
        "event": "Scan",
        "timestamp": "2026-10-26T00:01:00Z",
        "StarSystem": sys_name,
        "SystemAddress": sys_addr,
        "BodyName": f"{sys_name} A",
        "BodyID": 0,
        "DistanceFromArrivalLS": 0.0,
        "StarType": "A",
        "Subclass": 6,
        "Luminosity": "V",
        "AbsoluteMagnitude": 1.95,
        "Age_MY": 450
    }
    parser.process_journal_line(json.dumps(star_scan))
    parser.flush_dirty_systems()

    c = conn.cursor()
    # Check body subclass
    c.execute("SELECT star_type, subclass, luminosity FROM bodies WHERE system_address = ? AND body_id = 0", (sys_addr,))
    b_row = c.fetchone()
    assert b_row is not None
    assert b_row["star_type"] == "A"
    assert b_row["subclass"] == 6
    assert b_row["luminosity"] == "V"

    # Check system main_star_subclass
    c.execute("SELECT main_star_type, main_star_subclass FROM systems WHERE system_address = ?", (sys_addr,))
    s_row = c.fetchone()
    assert s_row is not None
    assert s_row["main_star_type"] == "A"
    assert s_row["main_star_subclass"] == 6

    conn.close()


def test_ui_system_card_spectral_badge_rendering():
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    i18n_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js"
    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    syslist_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_list.js"

    runner_script = f"""
    const fs = require('fs');
    global.window = global;

    eval(fs.readFileSync({json.dumps(str(i18n_path))}, 'utf8'));
    eval(fs.readFileSync({json.dumps(str(utils_path))}, 'utf8'));
    eval(fs.readFileSync({json.dumps(str(syslist_path))}, 'utf8'));

    // Mock DOM elements container
    const container = {{
      children: [],
      appendChild: function(c) {{ this.children.push(c); }}
    }};

    global.document = {{
      getElementById: (id) => {{
        if (id === 'system-list') return container;
        return {{ innerText: '', style: {{}}, classList: {{ add: () => {{}}, remove: () => {{}} }} }};
      }},
      createElement: (tag) => ({{
        tagName: tag.toUpperCase(),
        className: '',
        style: {{}},
        dataset: {{}},
        innerHTML: ''
      }}),
      querySelectorAll: () => []
    }};
    global.generateLandmarkDistanceBadges = () => [];

    const testSystems = [
      {{
        system_address: 101,
        star_system: "HIP 12345",
        main_star_type: "A",
        main_star_subclass: 6,
        main_star_luminosity: "V",
        main_star_absolute_magnitude: 1.95,
        scanned_bodies: 10,
        total_bodies: 10
      }},
      {{
        system_address: 102,
        star_system: "B-Giant System",
        main_star_type: "B",
        main_star_subclass: 0,
        main_star_luminosity: "IIIB",
        main_star_absolute_magnitude: -2.5,
        scanned_bodies: 3,
        total_bodies: 3
      }}
    ];

    global.state = {{
      selectedSystem: null,
      systems: testSystems,
      page: 1,
      totalPages: 1
    }};

    renderSystemList();

    console.log(JSON.stringify({{
      card1_html: container.children[0].innerHTML,
      card2_html: container.children[1].innerHTML
    }}));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, encoding="utf-8", check=True)
    res = json.loads(proc.stdout)

    # Card 1 should display 'A6 V', and tooltip should contain '絶対等級: 2.0 Mag'
    assert "A6 V" in res["card1_html"]
    assert "Mag</span>" not in res["card1_html"]  # Independent Mag badge is eliminated
    assert "絶対等級" in res["card1_html"]

    # Card 2 should display 'B0 IIIB'
    assert "B0 IIIB" in res["card2_html"]
    assert "Mag</span>" not in res["card2_html"]
