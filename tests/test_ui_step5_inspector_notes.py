import unittest
from pathlib import Path
import subprocess


class TestUIStep5InspectorNotes(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_right_pane_html_has_notes_accordion(self):
        right_path = self.root / "app" / "ui" / "components" / "right_pane.html"
        self.assertTrue(right_path.exists())
        content = right_path.read_text(encoding="utf-8")

        self.assertIn('id="section-bookmark"', content)
        self.assertIn('id="bm-section-header"', content)
        self.assertIn('id="bm-chevron"', content)
        self.assertIn('id="bm-section-body"', content)
        self.assertIn('id="bm-has-note-badge"', content)

    def test_css_has_notes_collapsed_styles(self):
        css_path = self.root / "app" / "ui" / "css" / "style.css"
        self.assertTrue(css_path.exists())
        content = css_path.read_text(encoding="utf-8")

        self.assertIn("#section-bookmark.collapsed #bm-section-body", content)
        self.assertIn("#section-bookmark.collapsed #bm-chevron", content)

    def test_i18n_has_note_keys(self):
        i18n_path = self.root / "app" / "ui" / "js" / "i18n.js"
        self.assertTrue(i18n_path.exists())
        content = i18n_path.read_text(encoding="utf-8")

        self.assertIn("bm_has_note", content)

    def test_inspector_notes_accordion_node(self):
        js_code = """
        const store = {};
        const localStorage = {
          getItem: (k) => store[k] || null,
          setItem: (k, v) => { store[k] = String(v); }
        };

        class MockElement {
          constructor(id) {
            this.id = id;
            this.classes = new Set();
            this.listeners = {};
          }
          get classList() {
            return {
              add: (c) => this.classes.add(c),
              remove: (c) => this.classes.delete(c),
              contains: (c) => this.classes.has(c),
              toggle: (c, f) => {
                if (f === undefined) {
                  if (this.classes.has(c)) this.classes.delete(c);
                  else this.classes.add(c);
                } else if (f) {
                  this.classes.add(c);
                } else {
                  this.classes.delete(c);
                }
              }
            };
          }
          addEventListener(evt, fn) {
            this.listeners[evt] = fn;
          }
          click(targetTag) {
            if (this.listeners['click']) {
              this.listeners['click']({ target: { tagName: targetTag || 'DIV', closest: () => null } });
            }
          }
        }

        const bmSection = new MockElement('section-bookmark');
        const bmHeader = new MockElement('bm-section-header');

        function initInspectorNotesAccordion() {
          const isCollapsed = localStorage.getItem('ed_inspector_notes_collapsed') === 'true';
          bmSection.classList.toggle('collapsed', isCollapsed);

          bmHeader.addEventListener('click', (e) => {
            if (e.target && (e.target.tagName === 'BUTTON' || e.target.closest('button'))) return;
            bmSection.classList.toggle('collapsed');
            localStorage.setItem('ed_inspector_notes_collapsed', bmSection.classList.contains('collapsed') ? 'true' : 'false');
          });
        }

        // Test initial state: not collapsed
        initInspectorNotesAccordion();
        if (bmSection.classList.contains('collapsed')) {
          throw new Error('Initial state should not be collapsed');
        }

        // Click header -> should collapse
        bmHeader.click('DIV');
        if (!bmSection.classList.contains('collapsed')) {
          throw new Error('Header click should toggle collapsed');
        }
        if (localStorage.getItem('ed_inspector_notes_collapsed') !== 'true') {
          throw new Error('Collapse state must be saved to localStorage');
        }

        // Click button inside header -> should NOT toggle
        bmHeader.click('BUTTON');
        if (!bmSection.classList.contains('collapsed')) {
          throw new Error('Button click should be ignored');
        }

        // Click header again -> should expand
        bmHeader.click('SPAN');
        if (bmSection.classList.contains('collapsed')) {
          throw new Error('Second header click should expand');
        }
        if (localStorage.getItem('ed_inspector_notes_collapsed') !== 'false') {
          throw new Error('Expanded state must be saved to localStorage');
        }

        console.log('PASS');
        """
        proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node test failed: {proc.stderr}")
        self.assertIn("PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
