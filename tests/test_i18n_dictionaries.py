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

