# Data from EDMC-BioScan (https://github.com/Silarn/EDMC-BioScan)
# Copyright (c) Jeremy Rimpo and contributors.
# Licensed under the GNU General Public License, version 2 or later
# (http://www.gnu.org/licenses/gpl-2.0.html); redistributed here under GPL-3.0-or-later.
# Imported unmodified except for the import paths. See app/parser/bioscan/NOTICE.md.
from typing import Mapping

catalog: dict[str, dict[str, Mapping]] = {
    '$Codex_Ent_Aleoids_Genus_Name;': {
        '$Codex_Ent_Aleoids_01_Name;': {
            'name': 'Aleoida Arcus',
            'value': 7252500,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 175.0,
                    'max_temperature': 180.0,
                    'min_pressure': 0.0161,
                    'body_type': ['Rocky body', 'High metal content body'],
                    'volcanism': 'None'
                }
            ],
        },
        '$Codex_Ent_Aleoids_02_Name;': {
            'name': 'Aleoida Coronamus',
            'value': 6284600,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 180.0,
                    'max_temperature': 190.0,
                    'min_pressure': 0.025,
                    'body_type': ['Rocky body', 'High metal content body'],
                    'volcanism': 'None'
                }
            ],
        },
        '$Codex_Ent_Aleoids_03_Name;': {
            'name': 'Aleoida Spica',
            'value': 3385200,
            'rulesets': [
                {
                    'atmosphere': ['Ammonia'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 170.0,
                    'max_temperature': 177.0,
                    'max_pressure': 0.0135,
                    'body_type': ['Rocky body', 'High metal content body'],
                    'regions': ['!orion-cygnus-core', '!sagittarius-carina-core']
                }
            ],
        },
        '$Codex_Ent_Aleoids_04_Name;': {
            'name': 'Aleoida Laminiae',
            'value': 3385200,
            'rulesets': [
                {
                    'atmosphere': ['Ammonia'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 152.0,
                    'max_temperature': 177.0,
                    'max_pressure': 0.0135,
                    'body_type': ['Rocky body', 'High metal content body'],
                    'regions': ['orion-cygnus', 'sagittarius-carina']
                }
            ],
        },
        '$Codex_Ent_Aleoids_05_Name;': {
            'name': 'Aleoida Gravis',
            'value': 12934900,
            'rulesets': [
                {
                    'atmosphere': ['CarbonDioxide'],
                    'min_gravity': 0.04,
                    'max_gravity': 0.276,
                    'min_temperature': 190.0,
                    'max_temperature': 197.0,
                    'min_pressure': 0.054,
                    'body_type': ['Rocky body', 'High metal content body'],
                    'volcanism': 'None'
                }
            ],
        }
    },
}
