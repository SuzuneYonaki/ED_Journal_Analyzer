import json
import shutil
import subprocess
from pathlib import Path
import pytest


def run_js_eval(expression, setup_code=""):
    node_exe = shutil.which("node")
    if not node_exe:
        pytest.skip("Node.js is not installed or not in PATH")

    i18n_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js").as_posix()
    utils_path = (Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "utils.js").as_posix()

    runner_script = f"""
    global.window = global;
    const i18nMod = require('{i18n_path}');
    const utilsMod = require('{utils_path}');
    Object.assign(global, i18nMod);
    Object.assign(global, utilsMod);
    {setup_code}
    const result = ({expression});
    console.log(JSON.stringify(result));
    """
    proc = subprocess.run([node_exe, "-e", runner_script], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(proc.stdout)


def test_i18n_dictionary_symmetry():
    keys_ja = set(run_js_eval('Object.keys(i18n.ja)'))
    keys_en = set(run_js_eval('Object.keys(i18n.en)'))

    missing_in_en = keys_ja - keys_en
    missing_in_ja = keys_en - keys_ja

    assert not missing_in_en, f"Keys present in JA but missing in EN: {missing_in_en}"
    assert not missing_in_ja, f"Keys present in EN but missing in JA: {missing_in_ja}"


def test_i18n_translation_lookup():
    ja_title = run_js_eval('t("mining_summary_title")', setup_code='setLanguage("ja");')
    assert "星系採掘サマリー" in ja_title

    en_title = run_js_eval('t("mining_summary_title")', setup_code='setLanguage("en");')
    assert "System Mining Summary" in en_title


def test_bilingual_parse_ring_class():
    icy_ja = run_js_eval('parseRingClass("eRingClass_Icy")', setup_code='setLanguage("ja");')
    assert icy_ja['name'] == '氷'
    assert '燃料' in icy_ja['description']

    icy_en = run_js_eval('parseRingClass("eRingClass_Icy")', setup_code='setLanguage("en");')
    assert icy_en['name'] == 'Icy'
    assert 'fuel' in icy_en['description']


def test_bilingual_parse_reserve_level():
    res_ja = run_js_eval('parseReserveLevel("PristineResources")', setup_code='setLanguage("ja");')
    assert res_ja['name'] == '無傷 (最高)'
    assert 'Pristine' in res_ja['label']

    res_en = run_js_eval('parseReserveLevel("PristineResources")', setup_code='setLanguage("en");')
    assert res_en['name'] == 'Pristine'
    assert res_en['label'] == 'Pristine'


def test_bilingual_time_formatting():
    ja_time = run_js_eval('formatSecondsToDaysOrHours(3600 * 5)', setup_code='setLanguage("ja");')
    assert '時間' in ja_time

    en_time = run_js_eval('formatSecondsToDaysOrHours(3600 * 5)', setup_code='setLanguage("en");')
    assert 'h' in en_time
