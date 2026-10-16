# Data from EDMC-BioScan (https://github.com/Silarn/EDMC-BioScan)
# Copyright (c) Jeremy Rimpo and contributors.
# Licensed under the GNU General Public License, version 2 or later
# (http://www.gnu.org/licenses/gpl-2.0.html); redistributed here under GPL-3.0-or-later.
# Imported unmodified except for the import paths. See app/parser/bioscan/NOTICE.md.
from typing import Mapping

catalog: dict[str, dict[str, Mapping]] = {
    '$Codex_Ent_Clypeus_Genus_Name;': {
        '$Codex_Ent_Clypeus_01_Name;': {
            'name': 'Clypeus Lacrimam',
            'value': 8418000,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'body_type': ['Rocky body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 190.0,
                    # 'max_temperature': 197.0,
                    'min_pressure': 0.054,
                    'volcanism': 'None'
                },
                {
                    'atmosphere': ['Water'],
                    'body_type': ['Rocky body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'volcanism': 'None'
                },
                {
                    'atmosphere': ['Water'],
                    'body_type': ['Rocky body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'volcanism': ['water']
                }
            ],
        },
        '$Codex_Ent_Clypeus_02_Name;': {
            'name': 'Clypeus Margaritus',
            'value': 11873200,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'body_type': ['High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 190.0,
                    'max_temperature': 197.0,
                    'min_pressure': 0.054,
                    'volcanism': 'None'
                },
                {
                    'atmosphere': ['Water'],
                    'body_type': ['High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'volcanism': 'None'
                }
            ],
        },
        '$Codex_Ent_Clypeus_03_Name;': {
            'name': 'Clypeus Speculumi',
            'value': 16202800,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 190.0,
                    'max_temperature': 197.0,
                    'min_pressure': 0.055,
                    'body_type': ['Rocky body'],
                    'volcanism': 'None',
                    'distance': 2000.0
                },
                {
                    'atmosphere': ['Water'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'body_type': ['Rocky body'],
                    'volcanism': 'None',
                    'distance': 2000.0
                },
                {
                    'atmosphere': ['Water'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'body_type': ['Rocky body'],
                    'volcanism': ['water'],
                    'distance': 2000.0
                }
            ],
        },
    },
}
