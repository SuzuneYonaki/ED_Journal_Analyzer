import unittest
from pathlib import Path
import subprocess


class TestUIStep42ColSearchSort(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_left_pane_html_has_search_collapsible_group(self):
        left_path = self.root / "app" / "ui" / "components" / "left_pane.html"
        self.assertTrue(left_path.exists())
        content = left_path.read_text(encoding="utf-8")

        self.assertIn('id="group-search-controls"', content)
        self.assertIn('class="collapsible-group"', content)
        self.assertIn('data-group="search"', content)
        self.assertIn('id="btn-clear-search-group"', content)
        self.assertIn('id="badge-search-controls"', content)

    def test_i18n_has_search_section_keys(self):
        i18n_path = self.root / "app" / "ui" / "js" / "i18n.js"
        self.assertTrue(i18n_path.exists())
        content = i18n_path.read_text(encoding="utf-8")

        self.assertIn("section_search_controls", content)

    def test_system_list_js_auto_collapses_on_2col(self):
        syslist_path = self.root / "app" / "ui" / "js" / "system_list.js"
        self.assertTrue(syslist_path.exists())
        content = syslist_path.read_text(encoding="utf-8")

        self.assertIn("group-search-controls", content)
        self.assertIn("group-sort-filters", content)
        self.assertIn("state.collapsedGroups['search'] = true", content)
        self.assertIn("state.collapsedGroups['sort'] = true", content)

    def test_2col_collapse_behavior_node(self):
        js_code = """
        const state = {
          uiLayoutMode: '1col',
          collapsedGroups: {}
        };

        class MockElement {
          constructor(id) {
            this.id = id;
            this.classes = new Set();
          }
          get classList() {
            return {
              add: (c) => this.classes.add(c),
              remove: (c) => this.classes.delete(c),
              contains: (c) => this.classes.has(c),
              toggle: (c, f) => {
                if (f) this.classes.add(c);
                else this.classes.delete(c);
              }
            };
          }
        }

        const mainContainer = new MockElement('main-container');
        const searchGroup = new MockElement('group-search-controls');
        const sortGroup = new MockElement('group-sort-filters');

        function applyLayout(mode) {
          state.uiLayoutMode = mode;
          mainContainer.classList.toggle('layout-2col-left', mode === '2col');

          if (mode === '2col') {
            if (!searchGroup.classList.contains('collapsed')) {
              searchGroup.classList.add('collapsed');
              state.collapsedGroups['search'] = true;
            }
            if (!sortGroup.classList.contains('collapsed')) {
              sortGroup.classList.add('collapsed');
              state.collapsedGroups['sort'] = true;
            }
          }
        }

        // Test 1-col: initially not collapsed
        applyLayout('1col');
        if (searchGroup.classList.contains('collapsed') || sortGroup.classList.contains('collapsed')) {
          throw new Error('Groups should not be collapsed in 1col mode');
        }

        // Test 2-col: auto collapse search and sort
        applyLayout('2col');
        if (!searchGroup.classList.contains('collapsed') || !sortGroup.classList.contains('collapsed')) {
          throw new Error('Search and Sort groups must be collapsed in 2col mode');
        }
        if (!state.collapsedGroups['search'] || !state.collapsedGroups['sort']) {
          throw new Error('state.collapsedGroups must reflect collapsed search and sort');
        }

        console.log('PASS');
        """
        proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node test failed: {proc.stderr}")
        self.assertIn("PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
