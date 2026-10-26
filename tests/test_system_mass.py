import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
import pytest
from starlette.testclient import TestClient

from app.db.database import init_db
from app.parser.journal_parser import JournalParser
from app.server.api import app


def test_format_solar_mass():
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
        m1: formatSolarMass(125.46),
        m2: formatSolarMass(1.054),
        m3: formatSolarMass(0.4567),
        m4: formatSolarMass(0.00523),
        m_null: formatSolarMass(null),
        m_zero: formatSolarMass(0)
    }}));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, encoding="utf-8", check=True)
    res = json.loads(proc.stdout)

    assert res["m1"] == "125.5"
    assert res["m2"] == "1.05"
    assert res["m3"] == "0.457"
    assert res["m4"] == "0.0052"
    assert res["m_null"] is None
    assert res["m_zero"] == "0"


def test_system_mass_db_backfill_and_calculation():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn, force=True)

    c = conn.cursor()
    sys_addr = 123456789
    c.execute("INSERT INTO systems (system_address, star_system) VALUES (?, ?)", (sys_addr, "Test Mass System"))

    # Main star: 1.5 Solar masses
    c.execute("""
    INSERT INTO bodies (system_address, body_id, body_name, distance_from_arrival_ls, star_type, stellar_mass)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (sys_addr, 0, "Test Mass System A", 0.0, "G", 1.5))

    # Secondary star: 0.5 Solar masses
    c.execute("""
    INSERT INTO bodies (system_address, body_id, body_name, distance_from_arrival_ls, star_type, stellar_mass)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (sys_addr, 1, "Test Mass System B", 1500.0, "M", 0.5))

    # Planet: 33294.6 Earth masses (~0.1 Solar masses)
    c.execute("""
    INSERT INTO bodies (system_address, body_id, body_name, distance_from_arrival_ls, planet_class, mass_em)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (sys_addr, 2, "Test Mass System A 1", 200.0, "Sudarsky class I gas giant", 33294.60487))

    conn.commit()

    # Re-run init_db to test backfill execution on existing data with NULL mass columns
    init_db(conn=conn, force=True)

    c.execute("SELECT main_star_mass, total_system_mass FROM systems WHERE system_address = ?", (sys_addr,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row["main_star_mass"] == pytest.approx(1.5, rel=1e-3)
    # Total mass = 1.5 (Main star) + 0.5 (Secondary star) + 0.1 (Planet) = 2.1 M☉
    assert row["total_system_mass"] == pytest.approx(2.1, rel=1e-3)


def test_journal_parser_mass_summary():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn, force=True)

    parser = JournalParser(conn)
    sys_addr = 987654321
    sys_name = "Parser Mass System"

    # FSDJump event
    fsd_jump = {
        "event": "FSDJump",
        "timestamp": "2026-10-26T00:00:00Z",
        "StarSystem": sys_name,
        "SystemAddress": sys_addr,
        "StarPos": [10.0, 20.0, 30.0]
    }
    parser.process_journal_line(json.dumps(fsd_jump))

    # Scan main star
    star_scan = {
        "event": "Scan",
        "timestamp": "2026-10-26T00:01:00Z",
        "StarSystem": sys_name,
        "SystemAddress": sys_addr,
        "BodyName": f"{sys_name} A",
        "BodyID": 0,
        "DistanceFromArrivalLS": 0.0,
        "StarType": "F",
        "StellarMass": 1.25,
        "Age_MY": 3500
    }
    parser.process_journal_line(json.dumps(star_scan))

    # Scan planet
    planet_scan = {
        "event": "Scan",
        "timestamp": "2026-10-26T00:02:00Z",
        "StarSystem": sys_name,
        "SystemAddress": sys_addr,
        "BodyName": f"{sys_name} 1",
        "BodyID": 1,
        "DistanceFromArrivalLS": 120.0,
        "PlanetClass": "High metal content body",
        "MassEM": 3329.460487  # 0.01 Solar masses
    }
    parser.process_journal_line(json.dumps(planet_scan))
    parser.flush_dirty_systems()

    # Verify systems table values
    c = conn.cursor()
    c.execute("SELECT main_star_mass, total_system_mass FROM systems WHERE system_address = ?", (sys_addr,))
    row = c.fetchone()
    conn.close()

    assert row is not None
    assert row["main_star_mass"] == pytest.approx(1.25, rel=1e-3)
    # Total mass = 1.25 + 0.01 = 1.26 M☉
    assert row["total_system_mass"] == pytest.approx(1.26, rel=1e-3)


def test_ui_system_mass_header_rendering():
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    i18n_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js"
    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    syslist_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_list.js"

    runner_script = f"""
    const fs = require('fs');
    global.window = global;

    // Minimal DOM Mock
    const elements = {{
      'current-system-name': {{ innerText: '' }},
      'current-system-coords': {{ innerText: '' }},
      'current-system-fss-value': {{ innerText: '' }},
      'current-system-value': {{ innerText: '' }},
      'current-system-mass-badge': {{ className: '', style: {{}}, innerText: '', title: '' }},
      'body-count-badge': {{ innerText: '' }}
    }};

    global.document = {{
      getElementById: (id) => elements[id] || {{ innerText: '', style: {{}}, classList: {{ add: () => {{}}, remove: () => {{}} }} }},
      querySelectorAll: () => []
    }};
    global.updateCurrentSystemDistances = () => {{}};

    eval(fs.readFileSync({json.dumps(str(i18n_path))}, 'utf8'));
    eval(fs.readFileSync({json.dumps(str(utils_path))}, 'utf8'));
    eval(fs.readFileSync({json.dumps(str(syslist_path))}, 'utf8'));

    global.state = {{
      selectedSystem: {{
        system_address: 112233,
        star_system: 'Eol Prou Mass-1',
        star_pos_x: 100.0,
        star_pos_y: -20.0,
        star_pos_z: 350.0,
        main_star_mass: 1.05,
        total_system_mass: 1.42,
        scanned_bodies: 5,
        total_bodies: 5
      }}
    }};

    renderSystemHeader();

    console.log(JSON.stringify({{
      badgeText: elements['current-system-mass-badge'].innerText,
      badgeTitle: elements['current-system-mass-badge'].title
    }}));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, encoding="utf-8", check=True)
    res = json.loads(proc.stdout)

    assert "1.05" in res["badgeText"]
    assert "1.42" in res["badgeText"]
    assert "M☉" in res["badgeText"]
    assert "1.05" in res["badgeTitle"]
    assert "1.42" in res["badgeTitle"]
