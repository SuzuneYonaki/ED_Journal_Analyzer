# Data from EDMC-BioScan (https://github.com/Silarn/EDMC-BioScan)
# Copyright (c) Jeremy Rimpo and contributors.
# Licensed under the GNU General Public License, version 2 or later
# (http://www.gnu.org/licenses/gpl-2.0.html); redistributed here under GPL-3.0-or-later.
# Imported unmodified except for the import paths. See app/parser/bioscan/NOTICE.md.
from typing import Mapping

catalog: dict[str, dict[str, Mapping]] = {
    '$Codex_Ent_Cactoid_Genus_Name;': {
        '$Codex_Ent_Cactoid_01_Name;': {
            'name': 'Cactoida Cortexum',
            'value': 3667600,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'body_type': ['Rocky body', 'High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 180.0,
                    'max_temperature': 197.0,
                    'min_pressure': 0.025,
                    'volcanism': 'None',
                    'regions': ['orion-cygnus']
                }
            ],
        },
        '$Codex_Ent_Cactoid_02_Name;': {
            'name': 'Cactoida Lapis',
            'value': 2483600,
            'rulesets': [
                {
                    'atmosphere': ['Ammonia'],
                    'body_type': ['Rocky body', 'High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 160.0,
                    'max_temperature': 177.0,
                    'max_pressure': 0.0135,
                    'regions': ['sagittarius-carina']
                }
            ],
        },
        '$Codex_Ent_Cactoid_03_Name;': {
            'name': 'Cactoida Vermis',
            'value': 16202800,
            'rulesets': [
                {
                    'atmosphere': ['SulphurDioxide'],
                    'body_type': ['Rocky body'],
                    'min_gravity': 0.265,
                    'max_gravity': 0.276,
                    'min_temperature': 160.0,
                    'max_temperature': 210.0,
                    'max_pressure': 0.005,
                    'volcanism': 'None'
                },
                {
                    'atmosphere': ['Water'],
                    'body_type': ['Rocky body', 'High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'volcanism': 'None'
                },
                {
                    'atmosphere': ['Water'],
                    'body_type': ['Rocky body', 'High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'volcanism': ['water']
                }
            ],
        },
        '$Codex_Ent_Cactoid_04_Name;': {
            'name': 'Cactoida Pullulanta',
            'value': 3667600,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'body_type': ['Rocky body', 'High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 180.0,
                    'max_temperature': 197.0,
                    'min_pressure': 0.025,
                    'volcanism': 'None',
                    'regions': ['perseus']
                }
            ],
        },
        '$Codex_Ent_Cactoid_05_Name;': {
            'name': 'Cactoida Peperatis',
            'value': 2483600,
            'rulesets': [
                {
                    'atmosphere': ['Ammonia'],
                    'body_type': ['Rocky body', 'High metal content body'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 160.0,
                    'max_temperature': 177.0,
                    'max_pressure': 0.0135,
                    'regions': ['scutum-centaurus']
                }
            ],
        },
    },
}
