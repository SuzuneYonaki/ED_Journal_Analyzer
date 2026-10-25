import json
import shutil
import subprocess
from pathlib import Path
import pytest


def test_gg_life_icon_class_and_label():
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    runner_script = f"""
    const fs = require('fs');
    global.window = global;
    const code = fs.readFileSync({json.dumps(str(utils_path))}, 'utf8');
    eval(code);

    const gg = {{ planet_class: 'Sudarsky class I gas giant' }};
    const gg_wbl = {{ planet_class: 'Gas giant with water based life' }};
    const gg_abl = {{ planet_class: 'Gas giant with ammonia based life' }};
    const ww = {{ planet_class: 'Water world' }};
    const aw = {{ planet_class: 'Ammonia world' }};

    console.log(JSON.stringify({{
        gg_cls: getBodyIconClass(gg),
        gg_lbl: getBodyIconLabel(gg),
        gg_wbl_cls: getBodyIconClass(gg_wbl),
        gg_wbl_lbl: getBodyIconLabel(gg_wbl),
        gg_abl_cls: getBodyIconClass(gg_abl),
        gg_abl_lbl: getBodyIconLabel(gg_abl),
        ww_cls: getBodyIconClass(ww),
        ww_lbl: getBodyIconLabel(ww),
        aw_cls: getBodyIconClass(aw),
        aw_lbl: getBodyIconLabel(aw)
    }}));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)

    # Standard Gas Giant: class 'icon-gas', label 'GG'
    assert res['gg_cls'] == 'icon-gas'
    assert res['gg_lbl'] == 'GG'

    # Gas giant with water based life: class 'icon-gas' (shares GG palette), label 'WW-GG'
    assert res['gg_wbl_cls'] == 'icon-gas'
    assert res['gg_wbl_lbl'] == 'WW-GG'

    # Gas giant with ammonia based life: class 'icon-gas' (shares GG palette), label 'AW-GG'
    assert res['gg_abl_cls'] == 'icon-gas'
    assert res['gg_abl_lbl'] == 'AW-GG'

    # Standard Water world: class 'icon-water', label 'WW'
    assert res['ww_cls'] == 'icon-water'
    assert res['ww_lbl'] == 'WW'

    # Standard Ammonia world: class 'icon-ammonia', label 'AW'
    assert res['aw_cls'] == 'icon-ammonia'
    assert res['aw_lbl'] == 'AW'


def test_system_map_ggg_element_styling():
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    utils_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js"
    sysmap_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "system_map.js"

    runner_script = f"""
    const fs = require('fs');
    global.window = global;
    global.document = {{
      createElement: (tag) => ({{
        tagName: tag.toUpperCase(),
        className: '',
        style: {{}},
        dataset: {{}},
        appendChild: function(c) {{ this.children = this.children || []; this.children.push(c); }},
        addEventListener: () => {{}},
        closest: () => null,
        innerHTML: ''
      }}),
      querySelectorAll: () => []
    }};
    global.t = (k) => k;
    global.state = {{ selectedSystem: {{ star_system: "TestSystem" }} }};
    global.formatDistance = (ls) => ls + ' Ls';

    const utilsCode = fs.readFileSync({json.dumps(str(utils_path))}, 'utf8');
    eval(utilsCode);

    const sysmapCode = fs.readFileSync({json.dumps(str(sysmap_path))}, 'utf8');
    eval(sysmapCode);

    const gggBody = {{
      body_id: 1,
      body_name: "Test GGG 1",
      planet_class: "Gas giant with water based life",
      distance_from_arrival_ls: 100,
      is_confirmed_ggg: true,
      confirmed_ggg_variant: "Viride"
    }};

    const wwggBody = {{
      body_id: 2,
      body_name: "Test WW-GG 2",
      planet_class: "Gas giant with water based life",
      distance_from_arrival_ls: 200,
      is_confirmed_ggg: false
    }};

    const gggCard = createSysMapBodyElement(gggBody, 'planet', "TestSystem");
    const gggSphere = gggCard.children[0];

    const wwggCard = createSysMapBodyElement(wwggBody, 'planet', "TestSystem");
    const wwggSphere = wwggCard.children[0];

    console.log(JSON.stringify({{
      gggHtml: gggSphere.innerHTML,
      wwggHtml: wwggSphere.innerHTML
    }}));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)

    # Confirmed GGG: icon-ggg and GGG
    assert 'icon-ggg' in res['gggHtml']
    assert 'GGG' in res['gggHtml']

    # Unconfirmed WW-GG: icon-gas, WW-GG, and label-long class for compact text fitting
    assert 'icon-gas' in res['wwggHtml']
    assert 'WW-GG' in res['wwggHtml']
    assert 'label-long' in res['wwggHtml']
