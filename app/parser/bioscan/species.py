# Data from EDMC-BioScan (https://github.com/Silarn/EDMC-BioScan)
# Copyright (c) Jeremy Rimpo and contributors.
# Licensed under the GNU General Public License, version 2 or later
# (http://www.gnu.org/licenses/gpl-2.0.html); redistributed here under GPL-3.0-or-later.
# Imported unmodified except for the import paths. See app/parser/bioscan/NOTICE.md.
from typing import Mapping
from app.parser.bioscan.rulesets.aleoida import catalog as aleoida
from app.parser.bioscan.rulesets.anemone import catalog as anemone
from app.parser.bioscan.rulesets.bacterium import catalog as bacterium
from app.parser.bioscan.rulesets.brain_tree import catalog as brain_tree
from app.parser.bioscan.rulesets.cactoida import catalog as cactoida
from app.parser.bioscan.rulesets.clypeus import catalog as clypeus
from app.parser.bioscan.rulesets.concha import catalog as concha
from app.parser.bioscan.rulesets.electricae import catalog as electricae
from app.parser.bioscan.rulesets.fonticulua import catalog as fonticulua
from app.parser.bioscan.rulesets.frutexa import catalog as frutexa
from app.parser.bioscan.rulesets.fumerola import catalog as fumerola
from app.parser.bioscan.rulesets.fungoida import catalog as fungoida
from app.parser.bioscan.rulesets.osseus import catalog as osseus
from app.parser.bioscan.rulesets.recepta import catalog as recepta
from app.parser.bioscan.rulesets.shard import catalog as shard
from app.parser.bioscan.rulesets.stratum import catalog as stratum
from app.parser.bioscan.rulesets.tubers import catalog as tubers
from app.parser.bioscan.rulesets.tubus import catalog as tubus
from app.parser.bioscan.rulesets.tussock import catalog as tussock

_mound_amphora: dict[str, dict[str, Mapping]] = {
    '$Codex_Ent_Cone_Name;': {  # No atmos, near center of nebula
        '$Codex_Ent_Cone_Name;': {
            'name': 'Bark Mound',
            'value': 1471900,
            'rulesets': [
                {
                    'volcanism': 'Any',
                    'nebula': 'large',
                    'regions': ['!center']
                }
            ]
        }
    },
    '$Codex_Ent_Vents_Name;': {
        '$Codex_Ent_Vents_Name;': {
            'name': 'Amphora Plant',
            'value': 1628800,
            'rulesets': [
                {
                    'body_type': ['Metal rich body'],
                    'atmosphere': ['None'],
                    'star': 'A',
                    'min_temperature': 1000.0,
                    'max_temperature': 1750.0,
                    'volcanism': ['metallic', 'rocky', 'silicate'],
                    'bodies': ['Earthlike body', 'Gas giant with water based life', 'Water giant'],
                    'regions': ['amphora']
                }
            ]
        }
    },
    '$Codex_Ent_Ingensradices_Genus_Name;': {
        '$Codex_Ent_Ingensradices_Unicus_Name;': {
            'name': 'Radicoida Unicus',
            'value': 119037,
            'rulesets': [
                {
                    'system': 'HIP 87621'
                }
            ]
        }
    }
}

rules: dict[str, dict[str, Mapping]] = (_mound_amphora | aleoida | anemone | bacterium | brain_tree | cactoida |
                                        clypeus | concha | electricae | fonticulua | frutexa | fumerola | fungoida |
                                        osseus | recepta | shard | stratum | tubers | tubus | tussock)
