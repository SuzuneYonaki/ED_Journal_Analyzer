# Third-party notice: species rules and matcher

The files in this directory are derived from two Elite Dangerous Market Connector (EDMC) plugins
by Jeremy Rimpo (Silarn), both licensed under the GNU General Public License, version 2 or later:

- **EDMC-BioScan** — https://github.com/Silarn/EDMC-BioScan
  - `rulesets/*.py`, `species.py`, `regions.py`, `nebula_sectors.py`, `nebula_stars.py` are the
    species rule definitions, region/guardian/tuber zone data and nebula data, imported unmodified
    apart from import paths.
  - `matcher.py` is a re-implementation of the rule evaluation in BioScan's `value_estimate()`
    (`src/load.py`) adapted to this application's data structures.
- **EDMC-ExploData** — https://github.com/Silarn/EDMC-ExploData
  - `genus.py` is its genus data (genus names, minimum sample distances, colour tables), imported unmodified.

Region membership is resolved with klightspeed's EliteDangerousRegionMap (MIT License); see
`app/data/region_map/`.

Those projects credit the Deep Space Network, the Codex NSP and Bio requirements spreadsheet and the
Canonn Biosheet as the sources of the species rules, the Catalog of Galactic Nebulae for nebula
positions, and EDSM for procedurally generated nebula reference stars.

This application is distributed under GPL-3.0 (see the repository `LICENSE`), which is compatible with the
"version 2 or later" terms of the two plugins above.
