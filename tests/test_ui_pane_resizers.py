import unittest
from pathlib import Path


class TestUIPaneResizers(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_html_contains_resizers(self):
        index_path = self.root / "app" / "ui" / "index.html"
        self.assertTrue(index_path.exists())
        index_content = index_path.read_text(encoding="utf-8")
        self.assertIn('id="resizer-left"', index_content)
        self.assertIn('id="resizer-right"', index_content)
        self.assertIn('pane-resizer-left', index_content)
        self.assertIn('pane-resizer-right', index_content)

    def test_css_contains_resizer_styles(self):
        css_path = self.root / "app" / "ui" / "css" / "style.css"
        self.assertTrue(css_path.exists())
        css_content = css_path.read_text(encoding="utf-8")
        self.assertIn(".pane-resizer", css_content)
        self.assertIn(".pane-resizer-left", css_content)
        self.assertIn(".pane-resizer-right", css_content)
        self.assertIn("body.resizing-pane", css_content)

    def test_app_js_implements_resizers(self):
        app_js_path = self.root / "app" / "ui" / "js" / "app.js"
        self.assertTrue(app_js_path.exists())
        app_js_content = app_js_path.read_text(encoding="utf-8")
        self.assertIn("ed_left_pane_width", app_js_content)
        self.assertIn("ed_right_pane_width", app_js_content)
        self.assertIn("setupResizer(resizerLeft", app_js_content)
        self.assertIn("setupResizer(resizerRight", app_js_content)
        self.assertIn("initPaneManager()", app_js_content)


if __name__ == "__main__":
    unittest.main()
