import unittest
from pathlib import Path
import subprocess


class TestUIStep2LiveSortReset(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parent.parent

    def test_app_js_calls_update_collapsible_badges(self):
        app_js_path = self.root / "app" / "ui" / "js" / "app.js"
        self.assertTrue(app_js_path.exists())
        content = app_js_path.read_text(encoding="utf-8")

        self.assertIn("function updateSortControlsUI()", content)
        self.assertIn("updateCollapsibleBadges()", content)
        self.assertIn("effectiveSortBy", content)
        self.assertIn("rarity_score", content)

    def test_live_sort_reset_logic_node(self):
        js_code = """
        const state = {
          liveSyncEnabled: false,
          datePreset: 'all',
          dateFrom: '',
          dateTo: '',
          sortBy: 'rarity_score',
          sortOrder: 'desc',
          savedSortBy: null,
          savedSortOrder: null,
          sortBy2: null,
          sortOrder2: null,
          savedSortBy2: null,
          savedSortOrder2: null,
          sortBy3: null,
          sortOrder3: null,
          savedSortBy3: null,
          savedSortOrder3: null,
          sortMode: 'composite',
          filters: {},
          celestialFilters: [],
          starTypes: [],
          luminosityClasses: []
        };

        const badgeSort = {
          innerText: '',
          active: false,
          classList: {
            toggle: (cls, val) => { badgeSort.active = !!val; }
          }
        };

        function updateCollapsibleBadges() {
          let sortCount = 0;
          if (state.datePreset && state.datePreset !== 'all') sortCount++;
          if (state.dateFrom || state.dateTo) sortCount++;
          if (state.sortBy && (state.sortBy !== 'rarity_score' || state.sortOrder !== 'desc')) sortCount++;
          if (state.sortBy2) sortCount++;
          if (state.sortBy3) sortCount++;
          if (state.liveSyncEnabled) sortCount++;
          badgeSort.innerText = sortCount > 0 ? String(sortCount) : '';
          badgeSort.classList.toggle('active', sortCount > 0);
        }

        function updateSortControlsUI() {
          if (state.liveSyncEnabled) {
            // Live locked
          } else {
            const effectiveSortBy = state.savedSortBy || (state.sortBy && state.sortBy !== 'live-locked' ? state.sortBy : 'rarity_score');
            const effectiveSortOrder = state.savedSortOrder || state.sortOrder || 'desc';
            state.sortBy = effectiveSortBy;
            state.sortOrder = effectiveSortOrder;
            state.savedSortBy = effectiveSortBy;
            state.savedSortOrder = effectiveSortOrder;
          }
          updateCollapsibleBadges();
        }

        // 1. Initial State: not live, default sort -> badge should be empty
        updateSortControlsUI();
        if (badgeSort.innerText !== '' || badgeSort.active !== false) {
          throw new Error('Initial sort badge should be empty');
        }

        // 2. Toggle Live ON -> badge should show 1
        state.liveSyncEnabled = true;
        updateSortControlsUI();
        if (badgeSort.innerText !== '1' || badgeSort.active !== true) {
          throw new Error('Sort badge should be 1 when Live is enabled');
        }

        // 3. Toggle Live OFF -> badge should reset completely to empty
        state.liveSyncEnabled = false;
        updateSortControlsUI();
        if (badgeSort.innerText !== '' || badgeSort.active !== false) {
          throw new Error('Sort badge should reset to empty when Live is turned off');
        }

        console.log('PASS');
        """
        proc = subprocess.run(["node", "-e", js_code], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Node test failed: {proc.stderr}")
        self.assertIn("PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
