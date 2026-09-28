import pytest
from pathlib import Path
from app.services.export_service import build_interactive_orrery


def test_build_interactive_orrery_en():
    """Verifies build_interactive_orrery outputs English strings when lang='en'."""
    sys_data = {
        "star_system": "Test System",
        "system_address": 12345678,
        "main_star_type": "G"
    }
    bodies = [
        {
            "body_id": 1,
            "body_name": "Test System A",
            "star_type": "G",
            "distance_from_arrival_ls": 0,
            "surface_temperature": 5778
        },
        {
            "body_id": 2,
            "body_name": "Test System B",
            "star_type": "M",
            "distance_from_arrival_ls": 5000,
            "surface_temperature": 3200
        },
        {
            "body_id": 3,
            "body_name": "Test System A 1",
            "planet_class": "High metal content body",
            "distance_from_arrival_ls": 200,
            "surface_gravity_g": 1.1,
            "surface_temperature": 310
        }
    ]

    html_en = build_interactive_orrery(sys_data, bodies, lang="en")
    assert "System Orrery &amp; Orbital Hierarchy (Interactive Zoom &amp; Orbit Map)" in html_en or "Interactive Zoom & Orbit Map" in html_en or "Interactive Zoom" in html_en
    assert "Zoom In" in html_en
    assert "Zoom Out" in html_en
    assert "Reset" in html_en
    assert "Focus Jump:" in html_en
    assert "Primary A" in html_en or "Primary" in html_en
    assert "Companion B" in html_en or "Companion" in html_en
    # Japanese phrases must not appear in English mode
    assert "全星系軌道図" not in html_en
    assert "フォーカスジャンプ" not in html_en
    assert "拡大" not in html_en


def test_build_interactive_orrery_ja():
    """Verifies build_interactive_orrery outputs Japanese strings when lang='ja'."""
    sys_data = {
        "star_system": "Test System",
        "system_address": 12345678,
        "main_star_type": "G"
    }
    bodies = [
        {
            "body_id": 1,
            "body_name": "Test System A",
            "star_type": "G",
            "distance_from_arrival_ls": 0,
            "surface_temperature": 5778
        }
    ]

    html_ja = build_interactive_orrery(sys_data, bodies, lang="ja")
    assert "全星系軌道図" in html_ja
    assert "拡大" in html_ja
    assert "全体リセット" in html_ja
    assert "フォーカスジャンプ:" in html_ja


def test_i18n_dictionary_completeness():
    """Verifies that all new keys exist in both ja and en dictionaries in i18n.js."""
    i18n_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "i18n.js"
    assert i18n_path.exists()
    content = i18n_path.read_text(encoding="utf-8")

    required_keys = [
        "bio_sampling_progress",
        "active_target_survey",
        "bio_alt_candidates_toggle",
        "bio_status_analyzed_short",
        "bio_status_sample_1_short",
        "bio_status_sample_2_short",
        "orrery_generating",
    ]

    # Split into ja and en regions (roughly before and after "en: {")
    assert "en: {" in content
    ja_part, en_part = content.split("en: {", 1)

    for k in required_keys:
        assert f"{k}:" in ja_part, f"Missing key '{k}' in ja dictionary"
        assert f"{k}:" in en_part, f"Missing key '{k}' in en dictionary"


def test_app_js_orrery_and_bio_i18n():
    """Verifies that app.js properly uses i18n for Orrery and Bio badges without hardcoded Japanese."""
    app_js_path = Path(__file__).resolve().parent.parent / "app" / "ui" / "js" / "app.js"
    assert app_js_path.exists()
    content = app_js_path.read_text(encoding="utf-8")

    # 1. Orrery lang resolution
    assert "getAppLang" in content
    orrery_idx = content.find("async function renderOrreryView")
    assert orrery_idx != -1
    orrery_section = content[orrery_idx:orrery_idx + 1500]
    assert "getAppLang" in orrery_section
    assert "state.lang || 'ja'" not in orrery_section
    assert "orrery_generating" in orrery_section

    # 2. Orrery cache clear in updateStaticTexts
    update_idx = content.find("function updateStaticTexts()")
    assert update_idx != -1
    update_section = content[update_idx:update_idx + 2500]
    assert "_orreryHtml = null" in update_section
    assert "_orreryCacheKey = null" in update_section

    # 3. Bio progress badge in renderBioOnlyView
    bio_view_idx = content.find("function renderBioOnlyView")
    assert bio_view_idx != -1
    bio_view_section = content[bio_view_idx:bio_view_idx + 3500]
    assert "bio_sampling_progress" in bio_view_section
    assert "active_target_survey" in bio_view_section
    # Hardcoded Japanese must not be directly in badge HTML
    assert "🌱 採取進捗: ${body.completed_bio_count" not in bio_view_section
    assert "bold; font-size: 0.72rem;\">🎯 ACTIVE TARGET (探査中)</span>" not in bio_view_section
    assert "activeTargetText" in bio_view_section
    assert "samplingProgressPattern" in bio_view_section
