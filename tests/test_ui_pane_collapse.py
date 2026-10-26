import unittest
from pathlib import Path
import re


class TestUIPaneCollapse(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_html_components_contain_collapse_elements(self):
        header_path = self.root / "app" / "ui" / "components" / "header.html"
        self.assertTrue(header_path.exists())
        header_content = header_path.read_text(encoding="utf-8")
        self.assertIn('id="btn-toggle-left-pane"', header_content)
        self.assertIn('id="btn-toggle-right-pane"', header_content)

        left_path = self.root / "app" / "ui" / "components" / "left_pane.html"
        self.assertTrue(left_path.exists())
        left_content = left_path.read_text(encoding="utf-8")
        self.assertIn('id="btn-collapse-left-pane"', left_content)

        right_path = self.root / "app" / "ui" / "components" / "right_pane.html"
        self.assertTrue(right_path.exists())
        right_content = right_path.read_text(encoding="utf-8")
        self.assertIn('id="btn-collapse-right-pane"', right_content)

        center_path = self.root / "app" / "ui" / "components" / "center_pane.html"
        self.assertTrue(center_path.exists())
        center_content = center_path.read_text(encoding="utf-8")
        self.assertIn('id="pane-expand-tab-left"', center_content)
        self.assertIn('id="pane-expand-tab-right"', center_content)

    def test_css_contains_collapsed_styles(self):
        css_path = self.root / "app" / "ui" / "css" / "style.css"
        self.assertTrue(css_path.exists())
        css_content = css_path.read_text(encoding="utf-8")
        self.assertIn(".left-pane.collapsed", css_content)
        self.assertIn(".right-pane.collapsed", css_content)
        self.assertIn(".pane-expand-tab-left", css_content)
        self.assertIn(".pane-expand-tab-right", css_content)

    def test_i18n_keys_for_panes(self):
        i18n_path = self.root / "app" / "ui" / "js" / "i18n.js"
        self.assertTrue(i18n_path.exists())
        i18n_content = i18n_path.read_text(encoding="utf-8")
        
        required_keys = [
            "btn_toggle_left_pane",
            "btn_toggle_right_pane",
            "tip_toggle_left_pane",
            "tip_toggle_right_pane",
            "tip_collapse_left_pane",
            "tip_collapse_right_pane",
            "btn_expand_left_pane",
            "btn_expand_right_pane"
        ]
        for key in required_keys:
            self.assertIn(key, i18n_content, f"Key {key} missing in i18n.js")

    def test_app_js_initializes_pane_manager(self):
        app_js_path = self.root / "app" / "ui" / "js" / "app.js"
        self.assertTrue(app_js_path.exists())
        app_js_content = app_js_path.read_text(encoding="utf-8")
        self.assertTrue("initPaneCollapseManager" in app_js_content or "initPaneManager" in app_js_content)
        self.assertIn("ed_left_pane_collapsed", app_js_content)
        self.assertIn("ed_right_pane_collapsed", app_js_content)


if __name__ == "__main__":
    unittest.main()
