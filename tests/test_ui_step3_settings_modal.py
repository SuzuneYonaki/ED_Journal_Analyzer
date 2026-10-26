import unittest
from pathlib import Path


class TestUIStep3SettingsModal(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_css_contains_fixed_top_settings_modal_rules(self):
        css_path = self.root / "app" / "ui" / "css" / "style.css"
        self.assertTrue(css_path.exists())
        content = css_path.read_text(encoding="utf-8")

        self.assertIn("#settings-modal", content)
        self.assertIn("align-items: flex-start", content)
        self.assertIn("padding-top: max(32px, 5vh)", content)
        self.assertIn("#settings-modal .modal-content", content)
        self.assertIn("height: 82vh", content)

    def test_modals_html_settings_modal_structure(self):
        modals_path = self.root / "app" / "ui" / "components" / "modals.html"
        self.assertTrue(modals_path.exists())
        content = modals_path.read_text(encoding="utf-8")

        self.assertIn('id="settings-modal"', content)
        self.assertIn('id="tab-btn-logs"', content)
        self.assertIn('id="tab-btn-ui"', content)
        self.assertIn('id="tab-btn-tts"', content)
        self.assertIn('id="tab-btn-addons"', content)
        self.assertIn('id="tab-btn-credits"', content)


if __name__ == "__main__":
    unittest.main()
