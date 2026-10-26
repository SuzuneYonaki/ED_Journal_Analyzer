import unittest
from pathlib import Path


class TestUIStep1Layout(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_left_pane_header_layout(self):
        left_path = self.root / "app" / "ui" / "components" / "left_pane.html"
        self.assertTrue(left_path.exists())
        content = left_path.read_text(encoding="utf-8")

        # Must have left-pane-concept-header with column layout
        self.assertIn('class="left-pane-concept-header"', content)
        self.assertIn('flex-direction: column', content)
        self.assertIn('id="btn-collapse-left-pane"', content)
        self.assertIn('id="btn-clear-all-filters"', content)
        self.assertIn('id="btn-live-toggle"', content)
        self.assertIn('id="btn-pane-tab-explorer"', content)

    def test_center_pane_title_and_mass_layout(self):
        center_path = self.root / "app" / "ui" / "components" / "center_pane.html"
        self.assertTrue(center_path.exists())
        content = center_path.read_text(encoding="utf-8")

        # Ensure structured 2-row layout in system-title-row
        self.assertIn('id="current-system-name"', content)
        self.assertIn('id="current-system-mass-badge"', content)
        self.assertIn('id="current-system-physics-badge"', content)
        self.assertIn('id="pane-expand-tab-left"', content)
        self.assertIn('id="pane-expand-tab-right"', content)

    def test_css_ggg_font_and_expand_tabs(self):
        css_path = self.root / "app" / "ui" / "css" / "style.css"
        self.assertTrue(css_path.exists())
        content = css_path.read_text(encoding="utf-8")

        # Check GGG font enlargement
        self.assertIn(".stat-gg-sub.stat-gg-sub-ggg", content)
        self.assertIn("0.70rem", content)
        self.assertIn("0.78rem", content)

        # Check expand tab positioning (side handles that don't overlap system name)
        self.assertIn(".pane-expand-tab-left", content)
        self.assertIn("top: 105px", content)
        self.assertIn("left: 0", content)
        self.assertIn("border-radius: 0 5px 5px 0", content)


if __name__ == "__main__":
    unittest.main()
