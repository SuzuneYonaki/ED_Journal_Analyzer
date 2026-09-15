import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_build_system_map_tree(flat_bodies, system_name):
    """Executes app/ui/js/system_map.js via Node.js for true end-to-end verification."""
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_map.js"
    runner_script = f"""
    const fs = require('fs');
    global.state = {{ selectedSystem: {{ star_system: {json.dumps(system_name)} }} }};
    const code = fs.readFileSync({json.dumps(str(js_path))}, 'utf8');
    eval(code);
    const bodies = {json.dumps(flat_bodies)};
    const tree = buildSystemMapTree(bodies, {json.dumps(system_name)});
    console.log(JSON.stringify(tree));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def test_asteroid_belts_extracted_to_rail():
    """Verify that asteroid belts on a star are extracted into the planets rail as independent nodes."""
    bodies = [
        {
            "body_id": 1,
            "body_name": "Sol",
            "star_type": "G",
            "parents": "[]",
            "distance_from_arrival_ls": 0.0,
            "rings": json.dumps([
                {
                    "Name": "Sol Asteroid Belt A",
                    "RingClass": "eRingClass_MetalRich",
                    "MassMT": 5.4e10,
                    "InnerRad": 3.14e11,
                    "OuterRad": 4.78e11
                },
                {
                    "Name": "Sol Asteroid Belt B",
                    "RingClass": "eRingClass_Icy",
                    "MassMT": 1.2e11,
                    "InnerRad": 7.5e11,
                    "OuterRad": 9.2e11
                }
            ]),
            "reserve_level": "PristineResources"
        },
        {
            "body_id": 2,
            "body_name": "Sol 1",
            "planet_class": "High metal content body",
            "semi_major_axis": 1.5e11,
            "parents": '[{"Star": 1}]',
            "distance_from_arrival_ls": 500.0
        }
    ]

    tree = run_js_build_system_map_tree(bodies, "Sol")
    assert len(tree) == 1
    sec = tree[0]
    planets = sec["planets"]

    # Sol 1, Sol Asteroid Belt A, Sol Asteroid Belt B
    assert len(planets) == 3

    # Check Belt A node properties
    belt_a = next(p for p in planets if "Belt A" in p["shortName"])
    assert belt_a["isAsteroidBelt"] is True
    assert belt_a["isStar"] is False
    assert belt_a["ring_class"] == "eRingClass_MetalRich"
    assert belt_a["reserve_level"] == "PristineResources"
    assert belt_a["inner_radius"] == 3.14e11
    assert belt_a["outer_radius"] == 4.78e11
    assert belt_a["semi_major_axis"] == (3.14e11 + 4.78e11) / 2
    assert belt_a["shortName"] == "Belt A"

    # Check Belt B node properties
    belt_b = next(p for p in planets if "Belt B" in p["shortName"])
    assert belt_b["isAsteroidBelt"] is True
    assert belt_b["ring_class"] == "eRingClass_Icy"
    assert belt_b["shortName"] == "Belt B"


def test_asteroid_belt_sorting_with_planets():
    """Verify that asteroid belts are naturally sorted into their proper orbital position between planets."""
    bodies = [
        {
            "body_id": 1,
            "body_name": "Sol",
            "star_type": "G",
            "parents": "[]",
            "distance_from_arrival_ls": 0.0,
            "rings": json.dumps([
                {
                    "Name": "Sol Asteroid Belt A",
                    "RingClass": "eRingClass_MetalRich",
                    "InnerRad": 3.0e11,
                    "OuterRad": 4.0e11  # avg = 3.5e11
                }
            ])
        },
        {
            "body_id": 2,
            "body_name": "Sol 1",
            "planet_class": "High metal content body",
            "semi_major_axis": 1.5e11,  # Before belt
            "parents": '[{"Star": 1}]',
            "distance_from_arrival_ls": 500.0
        },
        {
            "body_id": 3,
            "body_name": "Sol 2",
            "planet_class": "Gas giant with water based life",
            "semi_major_axis": 7.5e11,  # After belt
            "parents": '[{"Star": 1}]',
            "distance_from_arrival_ls": 2500.0
        }
    ]

    tree = run_js_build_system_map_tree(bodies, "Sol")
    sec = tree[0]
    names = [p["shortName"] for p in sec["planets"]]

    # Sol 1 (1.5e11) -> Belt A (3.5e11) -> Sol 2 (7.5e11)
    assert names == ["1", "Belt A", "2"]


def test_genuine_star_rings_preserved():
    """Verify that genuine circumstellar rings on stars (e.g. Y dwarf, T Tauri, or ringed star) remain on the star."""
    bodies = [
        {
            "body_id": 1,
            "body_name": "Col 285 Sector A",
            "star_type": "M",
            "parents": "[]",
            "distance_from_arrival_ls": 0.0
        },
        {
            "body_id": 2,
            "body_name": "Col 285 Sector B",
            "star_type": "Y",
            "parents": '[{"Star": 1}]',
            "distance_from_arrival_ls": 15000.0,
            "rings": json.dumps([
                {
                    "Name": "Col 285 Sector B Ring A",
                    "RingClass": "eRingClass_Icy",
                    "MassMT": 8.5e11,
                    "InnerRad": 1.2e8,
                    "OuterRad": 3.4e8
                }
            ])
        }
    ]

    tree = run_js_build_system_map_tree(bodies, "Col 285 Sector")
    assert len(tree) == 2

    # Star B section
    sec_b = next(s for s in tree if s["starKey"] == "B")

    # Star B's planets rail should NOT have an extracted belt
    assert len(sec_b["planets"]) == 0

    # Star B rootStar must preserve the ring in rings_list / rings
    star_b = sec_b["rootStar"]
    raw_rings = star_b.get("rings_list") or (json.loads(star_b["rings"]) if isinstance(star_b.get("rings"), str) else star_b.get("rings"))
    assert len(raw_rings) == 1
    assert raw_rings[0]["Name"] == "Col 285 Sector B Ring A"
    assert raw_rings[0]["RingClass"] == "eRingClass_Icy"


def test_mixed_star_belts_and_rings():
    """Verify that when a star has BOTH a genuine circumstellar ring and an Asteroid Belt:
    the belt is placed in the planetary rail while the ring remains on the star."""
    bodies = [
        {
            "body_id": 1,
            "body_name": "TestStar A",
            "star_type": "TTS",
            "parents": "[]",
            "distance_from_arrival_ls": 0.0,
            "rings": json.dumps([
                {
                    "Name": "TestStar A Ring A",
                    "RingClass": "eRingClass_Rocky",
                    "InnerRad": 1.0e8,
                    "OuterRad": 2.5e8
                },
                {
                    "Name": "TestStar A Asteroid Belt A",
                    "RingClass": "eRingClass_MetalRich",
                    "InnerRad": 5.0e11,
                    "OuterRad": 8.0e11
                }
            ])
        }
    ]

    tree = run_js_build_system_map_tree(bodies, "TestStar")
    assert len(tree) == 1
    sec = tree[0]

    # Planetary rail should only have the Asteroid Belt
    assert len(sec["planets"]) == 1
    belt_node = sec["planets"][0]
    assert belt_node["isAsteroidBelt"] is True
    assert belt_node["shortName"] == "Belt A"
    assert belt_node["ring_class"] == "eRingClass_MetalRich"

    # Root star still has access to the circumstellar ring
    star_node = sec["rootStar"]
    rings = json.loads(star_node["rings"]) if isinstance(star_node.get("rings"), str) else star_node.get("rings", [])
    non_belt_rings = [r for r in rings if "belt" not in (r.get("Name", "").lower())]
    assert len(non_belt_rings) == 1
    assert non_belt_rings[0]["Name"] == "TestStar A Ring A"


def test_raw_rings_null_elements_safety():
    """Verify that buildSystemMapTree safely ignores null or invalid elements in rings."""
    bodies = [
        {
            "body_id": 1,
            "body_name": "SafeStar",
            "star_type": "G",
            "parents": "[]",
            "distance_from_arrival_ls": 0.0,
            "rings": json.dumps([
                None,
                {
                    "Name": "SafeStar Asteroid Belt A",
                    "RingClass": "eRingClass_MetalRich",
                    "InnerRad": 1.0e11,
                    "OuterRad": 2.0e11
                },
                None
            ])
        }
    ]

    tree = run_js_build_system_map_tree(bodies, "SafeStar")
    assert len(tree) == 1
    assert len(tree[0]["planets"]) == 1
    assert tree[0]["planets"][0]["isAsteroidBelt"] is True


def test_star_does_not_inherit_belt_hotspots():
    """Verify that when an Asteroid Belt has DSS Hotspots, the star does NOT inherit them."""
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_map.js"
    runner_script = f"""
    const fs = require('fs');
    global.document = {{
      createElement: (tag) => ({{
        tagName: tag,
        className: '',
        dataset: {{}},
        style: {{}},
        appendChild: function(child) {{ this.children = this.children || []; this.children.push(child); }},
        innerHTML: ''
      }}),
      querySelectorAll: () => []
    }};
    global.window = global;
    global.t = (k) => k;
    global.state = {{ selectedSystem: {{ star_system: "TestStar" }} }};
    global.getBodyIconLabel = () => '⭐';
    global.getBodyIconClass = () => 'star-g';
    global.parseRingClass = (cls) => ({{ key: 'metal_rich', nameJa: '金属豊富', icon: '🪐', color: '#fb923c', bg: 'rgba(251,146,60,0.18)', border: 'rgba(251,146,60,0.5)' }});
    global.parseReserveLevel = (res) => ({{ key: 'pristine', en: 'Pristine', ja: '無垢', color: '#22c55e', icon: '💎' }});
    global.formatDistance = (ls) => ls + ' Ls';

    const code = fs.readFileSync({json.dumps(str(js_path))}, 'utf8');
    eval(code);

    const starBody = {{
      body_id: 1,
      body_name: "TestStar",
      isStar: true,
      star_type: "G",
      rings_list: [
        {{
          Name: "TestStar Asteroid Belt A",
          RingClass: "eRingClass_MetalRich",
          Hotspots: {{ Platinum: 3 }}
        }}
      ]
    }};

    const starCard = createSysMapBodyElement(starBody, 'root-star', "TestStar");
    const starCardHtml = JSON.stringify(starCard);

    // Now test belt body element
    const beltBody = {{
      body_id: "belt-1-0",
      body_name: "TestStar Belt A",
      isAsteroidBelt: true,
      ring_class: "eRingClass_MetalRich",
      rings_list: [
        {{
          Name: "TestStar Asteroid Belt A",
          RingClass: "eRingClass_MetalRich",
          Hotspots: {{ Platinum: 3 }}
        }}
      ]
    }};
    const beltCard = createSysMapBodyElement(beltBody, 'planet', "TestStar");
    const beltCardHtml = JSON.stringify(beltCard);

    console.log(JSON.stringify({{
      starHasPt: starCardHtml.includes("Pt x3"),
      beltHasPt: beltCardHtml.includes("Pt x3")
    }}));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)
    assert res["starHasPt"] is False, "Star card should NOT show belt hotspots"
    assert res["beltHasPt"] is True, "Belt card SHOULD show belt hotspots"

