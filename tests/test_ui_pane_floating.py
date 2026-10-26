import unittest
from pathlib import Path


class TestUIPaneFloating(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_right_pane_html_contains_floating_button(self):
        right_path = self.root / "app" / "ui" / "components" / "right_pane.html"
        self.assertTrue(right_path.exists())
        right_content = right_path.read_text(encoding="utf-8")
        self.assertIn('id="btn-float-right-pane"', right_content)
        self.assertIn('data-i18n-title="tip_float_right_pane"', right_content)

    def test_css_contains_floating_styles(self):
        css_path = self.root / "app" / "ui" / "css" / "style.css"
        self.assertTrue(css_path.exists())
        css_content = css_path.read_text(encoding="utf-8")
        self.assertIn(".right-pane.floating", css_content)
        self.assertIn("position: fixed", css_content)
        self.assertIn(".right-pane.floating .inspector-header", css_content)
        self.assertIn(".right-pane.floating.dragging", css_content)

    def test_i18n_keys_for_floating(self):
        i18n_path = self.root / "app" / "ui" / "js" / "i18n.js"
        self.assertTrue(i18n_path.exists())
        i18n_content = i18n_path.read_text(encoding="utf-8")

        required_keys = [
            "btn_float_pane",
            "btn_dock_pane",
            "tip_float_right_pane",
            "tip_dock_right_pane",
        ]
        for key in required_keys:
            self.assertIn(key, i18n_content, f"Key {key} missing in i18n.js")

    def test_app_js_implements_floating_logic(self):
        app_js_path = self.root / "app" / "ui" / "js" / "app.js"
        self.assertTrue(app_js_path.exists())
        app_js_content = app_js_path.read_text(encoding="utf-8")
        self.assertIn("setRightPaneFloating", app_js_content)
        self.assertIn("toggleRightPaneFloating", app_js_content)
        self.assertIn("ed_right_pane_is_floating", app_js_content)
        self.assertIn("ed_right_pane_floating_pos", app_js_content)


if __name__ == "__main__":
    unittest.main()
