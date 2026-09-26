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


def test_i18n_interpolation_and_fallback():
    # Interpolation
    res_interp = run_js_eval('t("custom_tpl", { user: "Commander", count: 42 })', setup_code="""
    registerTranslations('en', { custom_tpl: "Hello {user}, you found {count} items!" });
    setLanguage('en');
    """)
    assert res_interp == "Hello Commander, you found 42 items!"

    # Fallback string when key is missing
    res_fallback = run_js_eval('t("non_existing_key", "Default Fallback Value")')
    assert res_fallback == "Default Fallback Value"


def test_i18n_dynamic_registration():
    res = run_js_eval(
        "getSupportedLanguages()",
        setup_code="registerTranslations('fr', { greeting: 'Bonjour' });"
    )
    assert 'fr' in res


def test_i18n_translate_unknown():
    res_ja_null = run_js_eval('translateUnknown(null)', setup_code='setLanguage("ja");')
    assert res_ja_null == "不明"

    res_en_null = run_js_eval('translateUnknown(null)', setup_code='setLanguage("en");')
    assert res_en_null == "Unknown"

    res_en_from_ja = run_js_eval('translateUnknown("不明")', setup_code='setLanguage("en");')
    assert res_en_from_ja == "Unknown"

    res_valid = run_js_eval('translateUnknown("High Metal Content")', setup_code='setLanguage("en");')
    assert res_valid == "High Metal Content"


def test_i18n_apply_dom():
    setup_code = """
    function createEl(tag = 'div') {
      return {
        tagName: tag.toUpperCase(),
        innerText: '',
        innerHTML: '',
        placeholder: '',
        title: '',
        dataset: {},
        setAttribute(k, v) { this[k] = v; }
      };
    }
    const elText = createEl('span');
    elText.dataset.i18n = 'unknown';
    const elTitle = createEl('button');
    elTitle.dataset.i18nTitle = 'unknown';
    const elInput = createEl('input');
    elInput.dataset.i18nPlaceholder = 'unknown';

    const container = {
      querySelectorAll(sel) {
        if (sel === '[data-i18n]') return [elText];
        if (sel === '[data-i18n-html]') return [];
        if (sel === '[data-i18n-title]') return [elTitle];
        if (sel === '[data-i18n-placeholder]') return [elInput];
        if (sel === '[data-i18n-aria-label]') return [];
        return [];
      }
    };

    setLanguage('en');
    applyI18n(container);
    """
    res = run_js_eval("""
    ({
      text: elText.innerText,
      title: elTitle.title,
      placeholder: elInput.placeholder
    })
    """, setup_code=setup_code)
    assert res["text"] == "Unknown"
    assert res["title"] == "Unknown"
    assert res["placeholder"] == "Unknown"


def test_header_tooltip_keys_exist():
    expected_header_tips = [
        "stat_systems_tip", "stat_bodies_tip", "stat_elw_tip", "stat_ww_tip",
        "stat_ammonia_tip", "stat_hmc_tip", "stat_mr_tip", "stat_icy_tip",
        "stat_rocky_tip", "stat_rocky_ice_tip", "stat_bio_tip", "stat_payout_tip"
    ]
    for key in expected_header_tips:
        ja_val = run_js_eval(f't("{key}")', setup_code='setLanguage("ja");')
        en_val = run_js_eval(f't("{key}")', setup_code='setLanguage("en");')
        assert ja_val and ja_val != key, f"Missing JA translation for {key}"
        assert en_val and en_val != key, f"Missing EN translation for {key}"


def test_all_html_and_js_keys_present_in_dictionaries():
    import re
    ui_dir = Path(__file__).resolve().parent.parent / "app" / "ui"

    html_keys = set()
    for html_file in ui_dir.rglob("*.html"):
        txt = html_file.read_text(encoding="utf-8")
        matches = re.findall(r'data-i18n(?:-placeholder|-title|-aria-label|-html)?=["\']([^"\']+)["\']', txt)
        html_keys.update(matches)

    js_keys = set()
    for js_file in (ui_dir / "js").glob("*.js"):
        if js_file.name == "i18n.js":
            continue
        txt = js_file.read_text(encoding="utf-8")
        matches = re.findall(r'\bt\(\s*["\']([^"\']+)["\']', txt)
        js_keys.update(matches)

    keys_ja = set(run_js_eval('Object.keys(i18n.ja)'))
    keys_en = set(run_js_eval('Object.keys(i18n.en)'))

    missing_html_in_ja = html_keys - keys_ja
    missing_html_in_en = html_keys - keys_en
    missing_js_in_ja = js_keys - keys_ja
    missing_js_in_en = js_keys - keys_en

    assert not missing_html_in_ja, f"HTML keys missing in JA dictionary: {missing_html_in_ja}"
    assert not missing_html_in_en, f"HTML keys missing in EN dictionary: {missing_html_in_en}"
    assert not missing_js_in_ja, f"JS t() keys missing in JA dictionary: {missing_js_in_ja}"
    assert not missing_js_in_en, f"JS t() keys missing in EN dictionary: {missing_js_in_en}"


