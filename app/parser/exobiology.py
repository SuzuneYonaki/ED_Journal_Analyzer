import json
import re
from pathlib import Path

# Load Canonn Research Species Rules if available
CANONN_RULES_FILE = Path(__file__).resolve().parents[1] / "data" / "canonn_rules.json"
CANONN_SPECIES_RULES: dict = {}
if CANONN_RULES_FILE.is_file():
    try:
        with CANONN_RULES_FILE.open("r", encoding="utf-8") as f:
            CANONN_SPECIES_RULES = json.load(f)
    except Exception as e:
        print(f"[Exobiology] Error loading canonn_rules.json: {e}")

# Atmosphere mapping
ATMOSPHERE_TYPE_MAP = {
    "ammonia": 0,
    "ammonia oxygen": 1,
    "ammonia-rich": 2,
    "ammoniarich": 2,
    "argon": 3,
    "argon-rich": 4,
    "argonrich": 4,
    "carbon dioxide": 5,
    "carbon dioxide-rich": 6,
    "carbondioxiderich": 6,
    "co2": 5,
    "earth-like": 7,
    "earthlike": 7,
    "helium": 8,
    "metallic vapour": 9,
    "methane": 10,
    "methane-rich": 11,
    "methanerich": 11,
    "neon": 12,
    "neon-rich": 13,
    "neonrich": 13,
    "nitrogen": 14,
    "none": 15,
    "no atmosphere": 15,
    "oxygen": 16,
    "silicate vapour": 17,
    "sulphur dioxide": 18,
    "water": 19,
    "water-rich": 20,
    "waterrich": 20
}

# Planet class mapping
PLANET_CLASS_MAP = {
    "ammonia world": 1,
    "earthlike body": 2,
    "earth-like body": 2,
    "gas giant with ammonia based life": 3,
    "gas giant with water based life": 4,
    "helium rich gas giant": 5,
    "high metal content body": 6,
    "high metal content world": 6,
    "high metal content": 6,
    "hmc": 6,
    "icy body": 7,
    "icy": 7,
    "metal rich body": 8,
    "metal-rich body": 8,
    "metal rich": 8,
    "rocky body": 9,
    "rocky": 9,
    "rocky ice body": 10,
    "rocky-ice body": 10,
    "rocky ice": 10
}

# Default fallback values
GENUS_DEFAULT_VALUES = {
    "Aleoida": 7252500,
    "Bacterium": 1000000,
    "Cactoida": 3667600,
    "Clypeus": 8418000,
    "Concha": 4572400,
    "Electricae": 6284600,
    "Fonticulua": 1000000,
    "Fonticula": 1000000,
    "Frutexa": 1632500,
    "Fumerola": 6284600,
    "Fungoida": 3330300,
    "Osseus": 1483000,
    "Recepta": 12934900,
    "Stratum": 2640700,
    "Tubus": 2865900,
    "Tussock": 1000000,
    "Radicoida": 7200000,
    "Brain Trees": 1593700,
    "Crystalline Shards": 1600000,
    "Amphora Plant": 1500000,
    "Bark Mounds": 1500000,
    "Anemone": 1500000,
    "Sinuous Tubers": 1514500
}

GENUS_DEFAULT_DISTANCE = {
    "Aleoida": 150,
    "Bacterium": 500,
    "Cactoida": 300,
    "Clypeus": 150,
    "Concha": 150,
    "Electricae": 1000,
    "Fonticulua": 500,
    "Fonticula": 500,
    "Frutexa": 150,
    "Fumerola": 100,
    "Fungoida": 300,
    "Osseus": 800,
    "Recepta": 150,
    "Stratum": 500,
    "Tubus": 800,
    "Tussock": 200,
    "Radicoida": 1000,
    "Brain Trees": 100,
    "Crystalline Shards": 100,
    "Amphora Plant": 100,
    "Bark Mounds": 100,
    "Anemone": 100,
    "Sinuous Tubers": 100
}

# Full BioInsights Codex Rules (118 species)
BIOINSIGHTS_SPECIES_RULES = {
    "Aleoida Arcus": {
        "species_name": "Aleoida Arcus",
        "genus": "Aleoida",
        "base_value": 7252500,
        "colony_distance_m": 150,
        "description": "This aleoida species has upright clumps of long serrated leaves, which can open up to expose a reproductive organ containing tiny round seeds.",
        "variants": {
            "B": "Yellow",
            "A": "Green",
            "F": "Teal",
            "K": "Turquoise",
            "M": "Emerald",
            "L": "Lime",
            "T": "Sage",
            "TTS": "Mauve",
            "N": "Ocher",
            "W": "Grey",
            "Y": "Amethyst",
            "D": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 175
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 180
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.016
                    }
                ]
            ]
        ]
    },
    "Aleoida Coronamus": {
        "species_name": "Aleoida Coronamus",
        "genus": "Aleoida",
        "base_value": 6284600,
        "colony_distance_m": 150,
        "description": "This interleaved crown of mottled leaves can grow to head height, with explosive seed pods emerging on long protruding stalks.",
        "variants": {
            "B": "Yellow",
            "A": "Green",
            "F": "Teal",
            "K": "Turquoise",
            "M": "Emerald",
            "L": "Lime",
            "T": "Sage",
            "TTS": "Mauve",
            "N": "Ocher",
            "W": "Grey",
            "Y": "Amethyst",
            "D": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 190
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.025
                    }
                ]
            ]
        ]
    },
    "Aleoida Gravis": {
        "species_name": "Aleoida Gravis",
        "genus": "Aleoida",
        "base_value": 12934900,
        "colony_distance_m": 150,
        "description": "These aleoida's wide flat leaves on a heavy bark base can reach huge sizes, and sprout a dome-shaped reproductive organ at their peak.",
        "variants": {
            "B": "Yellow",
            "A": "Green",
            "F": "Teal",
            "K": "Turquoise",
            "M": "Emerald",
            "L": "Lime",
            "T": "Sage",
            "TTS": "Mauve",
            "N": "Ocher",
            "W": "Grey",
            "Y": "Amethyst",
            "D": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 190
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.055
                    }
                ]
            ]
        ]
    },
    "Aleoida Laminiae": {
        "species_name": "Aleoida Laminiae",
        "genus": "Aleoida",
        "base_value": 3385200,
        "colony_distance_m": 150,
        "description": "These aleoida have a circle of upturned leaves marked with patterns, surrounding a bright fleshy pod with darker markings which matures in their centre.",
        "variants": {
            "B": "Yellow",
            "A": "Green",
            "F": "Teal",
            "K": "Turquoise",
            "M": "Emerald",
            "L": "Lime",
            "T": "Sage",
            "TTS": "Mauve",
            "N": "Ocher",
            "W": "Grey",
            "Y": "Amethyst",
            "D": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.013
                    }
                ]
            ]
        ]
    },
    "Aleoida Spica": {
        "species_name": "Aleoida Spica",
        "genus": "Aleoida",
        "base_value": 3385200,
        "colony_distance_m": 150,
        "description": "An aleoida species with long spiky leaves that can reach over two metres high, surrounding a single reproductive organ on a long central stalk.",
        "variants": {
            "B": "Yellow",
            "A": "Green",
            "F": "Teal",
            "K": "Turquoise",
            "M": "Emerald",
            "L": "Lime",
            "T": "Sage",
            "TTS": "Mauve",
            "N": "Ocher",
            "W": "Grey",
            "Y": "Amethyst",
            "D": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 170
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.013
                    }
                ]
            ]
        ]
    },
    "Bacterium Acies": {
        "species_name": "Bacterium Acies",
        "genus": "Bacterium",
        "base_value": 1000000,
        "colony_distance_m": 500,
        "description": "A bacterial species that converts energy from neon-based atmospheres, creating looping whirls of bright colour.",
        "variants": {
            "UNKNOWN": "Aquamarine"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 12
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 20
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 139
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.2578
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.61
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.079
                    }
                ]
            ]
        ]
    },
    "Bacterium Alcyoneum": {
        "species_name": "Bacterium Alcyoneum",
        "genus": "Bacterium",
        "base_value": 1658500,
        "colony_distance_m": 500,
        "description": "A bacterial species found in ammonia-based atmospheres that lives in sunlight. A colony's appearance resembles an intricate maze.",
        "variants": {
            "O": "Turquoise",
            "B": "Grey",
            "A": "Yellow",
            "F": "Lime",
            "G": "Emerald",
            "K": "Green",
            "M": "Teal",
            "L": "Sage",
            "T": "Red",
            "TTS": "Maroon",
            "W": "Amethyst",
            "D": "Ocher",
            "N": "Indigo",
            "Y": "Mauve",
            "AEBE": "Orange"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.373
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0133
                    }
                ]
            ]
        ]
    },
    "Bacterium Aurasus": {
        "species_name": "Bacterium Aurasus",
        "genus": "Bacterium",
        "base_value": 1000000,
        "colony_distance_m": 500,
        "description": "These bacteria thrive on sunlight in atmospheres rich with carbon dioxide. They cause blanket coloration across a planetary surface.",
        "variants": {
            "O": "Turquoise",
            "B": "Grey",
            "A": "Yellow",
            "F": "Lime",
            "G": "Emerald",
            "K": "Green",
            "M": "Teal",
            "L": "Sage",
            "T": "Red",
            "TTS": "Maroon",
            "W": "Amethyst",
            "D": "Ocher",
            "N": "Indigo",
            "Y": "Mauve",
            "AEBE": "Orange"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 145
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 400
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.605
                    }
                ]
            ]
        ]
    },
    "Bacterium Bullaris": {
        "species_name": "Bacterium Bullaris",
        "genus": "Bacterium",
        "base_value": 1152500,
        "colony_distance_m": 500,
        "description": "This species of bacteria thrives on atmospheric methane, appearing as a network of linked bubble patterns.",
        "variants": {
            "UNKNOWN": "Red"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 67
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 109
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 11
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 73
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 145
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.025
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.6
                    }
                ]
            ]
        ]
    },
    "Bacterium Cerbrus": {
        "species_name": "Bacterium Cerbrus",
        "genus": "Bacterium",
        "base_value": 1689800,
        "colony_distance_m": 500,
        "description": "A sunlight-converting bacterial species on worlds with atmospheres dominated by water and sulphur dioxide. Their colonies resemble a brain-shaped mass of smaller connected cells.",
        "variants": {
            "O": "Turquoise",
            "B": "Grey",
            "A": "Yellow",
            "F": "Lime",
            "G": "Emerald",
            "K": "Green",
            "M": "Teal",
            "L": "Sage",
            "T": "Red",
            "TTS": "Maroon",
            "W": "Amethyst",
            "D": "Ocher",
            "N": "Indigo",
            "Y": "Mauve",
            "AEBE": "Orange"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 132
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 499
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 392
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 452
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 20
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 220
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 330
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ]
        ]
    },
    "Bacterium Informem": {
        "species_name": "Bacterium Informem",
        "genus": "Bacterium",
        "base_value": 8418000,
        "colony_distance_m": 500,
        "description": "These bacteria can be found in nitrogen atmospheres, and form a shapeless mass across the surface.",
        "variants": {
            "UNKNOWN": "Cobalt"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 14
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 43
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 150
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.05
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.6
                    }
                ]
            ]
        ]
    },
    "Bacterium Nebulus": {
        "species_name": "Bacterium Nebulus",
        "genus": "Bacterium",
        "base_value": 5289900,
        "colony_distance_m": 500,
        "description": "A bacterial species that survives exclusively on atmospheric helium. They are distinguished by a radial pattern extending outward from the colony's centre.",
        "variants": {
            "UNKNOWN": "Cobalt"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 8
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 20
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 21
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.4
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.55
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.067
                    }
                ]
            ]
        ]
    },
    "Bacterium Omentum": {
        "species_name": "Bacterium Omentum",
        "genus": "Bacterium",
        "base_value": 4638900,
        "colony_distance_m": 500,
        "description": "These bacteria convert geothermal heat from nitrogen-based volcanic sites into energy. They appear as long interlinked strands across the surface.",
        "variants": {
            "UNKNOWN": "Red"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 12
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 13
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 8
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 20
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "NITROGEN_BASED"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "AMMONIA_BASED"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.025
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ]
            ]
        ]
    },
    "Bacterium Scopulum": {
        "species_name": "Bacterium Scopulum",
        "genus": "Bacterium",
        "base_value": 4934500,
        "colony_distance_m": 500,
        "description": "These bacteria thrive on the heat generated by carbon-based volcanic activity, and appear as long swirling ridges on the surface.",
        "variants": {
            "UNKNOWN": "Mulberry"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 12
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 13
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 8
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "CARBON_BASED"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "METHANE_BASED"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.025
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ]
        ]
    },
    "Bacterium Tela": {
        "species_name": "Bacterium Tela",
        "genus": "Bacterium",
        "base_value": 1949000,
        "colony_distance_m": 500,
        "description": "These bacteria appear as an intricate web pattern. They thrive in proximity to helium-based, iron-based and silicate-based volcanic sites.",
        "variants": {
            "UNKNOWN": "Cobalt"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    },
                    {
                        "type": "VOLCANISM",
                        "svalue": "NONE"
                    },
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 300
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "VOLCANISM",
                        "svalue": "NONE"
                    },
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 300
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    },
                    {
                        "type": "VOLCANISM",
                        "svalue": "NONE"
                    },
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 390
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 20
                    },
                    {
                        "type": "VOLCANISM",
                        "svalue": "NONE"
                    },
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 300
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.025
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.61
                    }
                ]
            ]
        ]
    },
    "Bacterium Verrata": {
        "species_name": "Bacterium Verrata",
        "genus": "Bacterium",
        "base_value": 3897000,
        "colony_distance_m": 500,
        "description": "These bacteria can be found at sites of water-based volcanic activity, and resemble a honeycomb structure.",
        "variants": {
            "UNKNOWN": "Blue"
        },
        "requirements": [
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "WATER_BASED"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.612
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ]
            ]
        ]
    },
    "Bacterium Vesicula": {
        "species_name": "Bacterium Vesicula",
        "genus": "Bacterium",
        "base_value": 1000000,
        "colony_distance_m": 500,
        "description": "These bacteria survive on worlds with argon-based atmospheres, and appear as a collection of tight loops on the ground.",
        "variants": {
            "UNKNOWN": "Lime"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 50
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 234
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.025
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.515
                    }
                ]
            ]
        ]
    },
    "Bacterium Volu": {
        "species_name": "Bacterium Volu",
        "genus": "Bacterium",
        "base_value": 7774700,
        "colony_distance_m": 500,
        "description": "A bacterial species dependent upon oxygen atmospheres, which creates random swirling patterns across the ground.",
        "variants": {
            "UNKNOWN": "Gold"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 16
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 145
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 245
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.24
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.515
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.014
                    }
                ]
            ]
        ]
    },
    "Cactoida Cortexum": {
        "species_name": "Cactoida Cortexum",
        "genus": "Cactoida",
        "base_value": 3667600,
        "colony_distance_m": 300,
        "description": "A species of cactoid that can reach over three metres in height. They are composed of multiple growths that sprout sealed pods at their peaks, which open up to distribute seeds.",
        "variants": {
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "TTS": "Red",
            "N": "Sage",
            "Y": "Ocher",
            "D": "Turquoise",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.026
                    }
                ]
            ]
        ]
    },
    "Cactoida Lapis": {
        "species_name": "Cactoida Lapis",
        "genus": "Cactoida",
        "base_value": 2483600,
        "colony_distance_m": 300,
        "description": "This cactoid species appears as a squat growth with latticed upper surface, which eventually produces a cluster of seed pods.",
        "variants": {
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "TTS": "Red",
            "N": "Sage",
            "Y": "Ocher",
            "D": "Turquoise",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.013
                    }
                ]
            ]
        ]
    },
    "Cactoida Peperatis": {
        "species_name": "Cactoida Peperatis",
        "genus": "Cactoida",
        "base_value": 2483600,
        "colony_distance_m": 300,
        "description": "A cactoid species appearing as a swollen fived-sided growth, reaching over two metres high and topped with an intersected crown.",
        "variants": {
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "TTS": "Red",
            "N": "Sage",
            "Y": "Ocher",
            "D": "Turquoise",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0133
                    }
                ]
            ]
        ]
    },
    "Cactoida Pullulanta": {
        "species_name": "Cactoida Pullulanta",
        "genus": "Cactoida",
        "base_value": 3667600,
        "colony_distance_m": 300,
        "description": "This species of cactoid has a globular base, from which extend vertical cylinders that can reach over four metres. Rounded pods grow in clusters along the cylinders, which break open to scatter seeds.",
        "variants": {
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "TTS": "Red",
            "N": "Sage",
            "Y": "Ocher",
            "D": "Turquoise",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.025
                    }
                ]
            ]
        ]
    },
    "Cactoida Vermis": {
        "species_name": "Cactoida Vermis",
        "genus": "Cactoida",
        "base_value": 16202800,
        "colony_distance_m": 300,
        "description": "These cactoids appear as a tall collection of cylinders linked by an undulating membrane and topped with a spiky crown. They often have a spiny life-form attached that is thought to form a symbiotic relationship with the larger organism, although the nature of this is not understood.",
        "variants": {
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "TTS": "Red",
            "N": "Sage",
            "Y": "Ocher",
            "D": "Turquoise",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 392
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 450
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    }
                ],
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 166
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ]
            ]
        ]
    },
    "Clypeus Lacrimam": {
        "species_name": "Clypeus Lacrimam",
        "genus": "Clypeus",
        "base_value": 8418000,
        "colony_distance_m": 150,
        "description": "A species of clypeus that grows a broad, tear-shaped shield to protect the sensitive organism from extreme sunlight. The shield's ridges help to direct water droplets down into the soil.",
        "variants": {
            "A": "Orange",
            "F": "Mauve",
            "G": "Amethyst",
            "K": "Grey",
            "M": "Turquoise",
            "L": "Teal",
            "N": "Yellow",
            "B": "Maroon",
            "D": "Lime",
            "Y": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.054
                    }
                ]
            ]
        ]
    },
    "Clypeus Margaritus": {
        "species_name": "Clypeus Margaritus",
        "genus": "Clypeus",
        "base_value": 11873200,
        "colony_distance_m": 150,
        "description": "This clypeus species produces a curved shield that resembles a large pearl in shape and texture. Up to three central organisms grow within it upon a supporting bed of leaves.",
        "variants": {
            "A": "Orange",
            "F": "Mauve",
            "G": "Amethyst",
            "K": "Grey",
            "M": "Turquoise",
            "L": "Teal",
            "N": "Yellow",
            "B": "Maroon",
            "D": "Lime",
            "Y": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.05
                    }
                ]
            ]
        ]
    },
    "Clypeus Speculumi": {
        "species_name": "Clypeus Speculumi",
        "genus": "Clypeus",
        "base_value": 16202800,
        "colony_distance_m": 150,
        "description": "A clypeus species that grows an angular shield with a mirrored exterior to protect the spiky organisms. This species can be found on planets orbiting their parent star at a distance of 5AU or greater.",
        "variants": {
            "A": "Orange",
            "F": "Mauve",
            "G": "Amethyst",
            "K": "Grey",
            "M": "Turquoise",
            "L": "Teal",
            "N": "Yellow",
            "B": "Maroon",
            "D": "Lime",
            "Y": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.052
                    }
                ]
            ]
        ]
    },
    "Concha Aureolas": {
        "species_name": "Concha Aureolas",
        "genus": "Concha",
        "base_value": 7774700,
        "colony_distance_m": 150,
        "description": "These concha are found on worlds with nitrogen-based atmospheres. Their rounded rock-like structure splits part to extend long stalks topped with loops.",
        "variants": {
            "A": "Teal",
            "F": "Grey",
            "G": "Turquoise",
            "K": "Red",
            "L": "Orange",
            "N": "Emerald",
            "B": "Indigo",
            "W": "Lime",
            "Y": "Yellow",
            "D": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 16,
                        "dvalue": 100
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SMA_MAX",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0134
                    }
                ]
            ]
        ]
    },
    "Concha Biconcavis": {
        "species_name": "Concha Biconcavis",
        "genus": "Concha",
        "base_value": 19010800,
        "colony_distance_m": 150,
        "description": "This concha species resembles a ridged, bisected egg until they crack in half, alllowing a thin stalk to sprout from its fleshy insides. This is covered with doughnut-shaped pods that create locations for chemical exchange.",
        "variants": {
            "UNKNOWN": "Gold"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 14
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 42
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 51
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 64,
                        "dvalue": 100
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.05
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.005
                    }
                ]
            ]
        ]
    },
    "Concha Labiata": {
        "species_name": "Concha Labiata",
        "genus": "Concha",
        "base_value": 2352400,
        "colony_distance_m": 150,
        "description": "A concha species that thrives in atmospheres rich with carbon dioxide. The lip-like upper opening cracks apart to allow a vertical growth of spiky leaves and bright seeds to stretch upward.",
        "variants": {
            "A": "Teal",
            "F": "Grey",
            "G": "Turquoise",
            "K": "Red",
            "L": "Orange",
            "N": "Emerald",
            "B": "Indigo",
            "W": "Lime",
            "Y": "Yellow",
            "D": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 150
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 199
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 97.5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.002
                    }
                ]
            ]
        ]
    },
    "Concha Renibus": {
        "species_name": "Concha Renibus",
        "genus": "Concha",
        "base_value": 4572400,
        "colony_distance_m": 150,
        "description": "A species of concha that relies on heat sources to survive. As the bisected growth increases in size, it sprouts a single stalk topped with an array of luminous fronds that facilitate metabolism.",
        "variants": {
            "UNKNOWN": "Aquamarine"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0254
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0987
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 97.5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 78
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 103
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0125
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0201
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 32,
                        "dvalue": 100
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 390
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 452.2
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0527
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0987
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 1,
                        "dvalue": 100
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 163
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.013
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 16,
                        "dvalue": 100
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    }
                ]
            ]
        ]
    },
    "Electricae Pluma": {
        "species_name": "Electricae Pluma",
        "genus": "Electricae",
        "base_value": 6284600,
        "colony_distance_m": 1000,
        "description": "A species of electricae that extends a tip of four connected loops above the ice, each covered with brightly luminous fronds. This species is typically found on planets orbiting bright white stars.",
        "variants": {
            "UNKNOWN": "Mulberry"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PARENT_TYPE",
                        "svalue": "A"
                    }
                ],
                [
                    {
                        "type": "PARENT_TYPE",
                        "svalue": "D"
                    }
                ],
                [
                    {
                        "type": "PARENT_TYPE",
                        "svalue": "N"
                    }
                ],
                [
                    {
                        "type": "PARENT_TYPE",
                        "svalue": "B"
                    }
                ],
                [
                    {
                        "type": "PARENT_TYPE",
                        "svalue": "H"
                    }
                ]
            ]
        ]
    },
    "Electricae Radialem": {
        "species_name": "Electricae Radialem",
        "genus": "Electricae",
        "base_value": 6284600,
        "colony_distance_m": 1000,
        "description": "These electricae species protrude bioluminescent stalks that radiate out in all directions. It is thought that this species may have an unspecified link with the proximity of nebulae to its host planet.",
        "variants": {
            "UNKNOWN": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "IS_IN_SPHERE",
                        "ivalue": 0
                    }
                ],
                [
                    {
                        "type": "IS_IN_SPHERE",
                        "ivalue": 1
                    }
                ]
            ]
        ]
    },
    "Fonticulua Campestris": {
        "species_name": "Fonticulua Campestris",
        "genus": "Fonticulua",
        "base_value": 1000000,
        "colony_distance_m": 500,
        "description": "These fonticulua thrive in argon atmospheres, and can reach four metres in height. They feature huge leaf-like structures to capture sunlight for conversion to energy.",
        "variants": {
            "B": "Lime",
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "K": "Emerald",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "Y": "Ocher",
            "D": "Turquoise",
            "N": "Sage",
            "TTS": "Red",
            "AEBE": "Maroon",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 50
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 150
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 1024,
                        "dvalue": 50
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.2755
                    }
                ]
            ]
        ]
    },
    "Fonticulua Digitos": {
        "species_name": "Fonticulua Digitos",
        "genus": "Fonticulua",
        "base_value": 1804100,
        "colony_distance_m": 500,
        "description": "A fonticulua species that thrives in methane-based atmospheres, sprouting a cluster of cylindrical tubes directly from the ice.",
        "variants": {
            "B": "Lime",
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "K": "Emerald",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "Y": "Ocher",
            "D": "Turquoise",
            "N": "Sage",
            "TTS": "Red",
            "AEBE": "Maroon",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 83
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 109
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 32,
                        "dvalue": 99.9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.058
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.03
                    }
                ]
            ]
        ]
    },
    "Fonticulua Fluctus": {
        "species_name": "Fonticulua Fluctus",
        "genus": "Fonticulua",
        "base_value": 20000000,
        "colony_distance_m": 500,
        "description": "A species of fonticulua that exists on worlds with oxygen atmospheres. They produce coiling wave-shaped structures which tilt toward sunlight.",
        "variants": {
            "B": "Lime",
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "K": "Emerald",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "Y": "Ocher",
            "D": "Turquoise",
            "N": "Sage",
            "TTS": "Red",
            "AEBE": "Maroon",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 16
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 142
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 200
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 2,
                        "dvalue": 50
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.23
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.2755
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.012
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.08
                    }
                ]
            ]
        ]
    },
    "Fonticulua Lapida": {
        "species_name": "Fonticulua Lapida",
        "genus": "Fonticulua",
        "base_value": 3111000,
        "colony_distance_m": 500,
        "description": "A fonticulua species that exists in atmospheres with a heavy concentration of nitrogen. Growing up along with the main stalk are bright gem-like pods, which can break off and create new colonies.",
        "variants": {
            "B": "Lime",
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "K": "Emerald",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "Y": "Ocher",
            "D": "Turquoise",
            "N": "Sage",
            "TTS": "Red",
            "AEBE": "Maroon",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 14
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 50
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 81
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 64,
                        "dvalue": 99.9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.19
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.2755
                    }
                ]
            ]
        ]
    },
    "Fonticulua Segmentatus": {
        "species_name": "Fonticulua Segmentatus",
        "genus": "Fonticulua",
        "base_value": 19010800,
        "colony_distance_m": 500,
        "description": "A species of fonticulua found in atmospheres dominated by neon, appearing as a pyramid-shaped cluster of frilled sections.",
        "variants": {
            "B": "Lime",
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "K": "Emerald",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "Y": "Ocher",
            "D": "Turquoise",
            "N": "Sage",
            "TTS": "Red",
            "AEBE": "Maroon",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 56
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 75
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 13
                    }
                ],
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 50
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 57
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 12
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.245
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.2755
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.045
                    }
                ]
            ]
        ]
    },
    "Fonticulua Upupam": {
        "species_name": "Fonticulua Upupam",
        "genus": "Fonticulua",
        "base_value": 5727600,
        "colony_distance_m": 500,
        "description": "This fonticulua species can be found on ice worlds with argon-rich atmospheres. They produce broad hoop-shaped structures to better reflect weak sunlight onto themselves for photosynthesis.",
        "variants": {
            "B": "Lime",
            "A": "Green",
            "F": "Yellow",
            "G": "Teal",
            "K": "Emerald",
            "M": "Amethyst",
            "L": "Mauve",
            "T": "Orange",
            "Y": "Ocher",
            "D": "Turquoise",
            "N": "Sage",
            "TTS": "Red",
            "AEBE": "Maroon",
            "O": "Grey",
            "W": "Indigo"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 4
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 60
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 120
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 64,
                        "dvalue": 50
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.2
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.2755
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.019
                    }
                ]
            ]
        ]
    },
    "Frutexa Acus": {
        "species_name": "Frutexa Acus",
        "genus": "Frutexa",
        "base_value": 7774700,
        "colony_distance_m": 150,
        "description": "This frutexa species has vivid colouration when young that alters as it matures. Its upper branches produce lines of small pea-like seed pods.",
        "variants": {
            "B": "Lime",
            "F": "Green",
            "G": "Emerald",
            "M": "Grey",
            "L": "Teal",
            "TTS": "Mauve",
            "D": "Indigo",
            "N": "Red",
            "W": "Orange",
            "O": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 146
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0027
                    }
                ]
            ]
        ]
    },
    "Frutexa Collum": {
        "species_name": "Frutexa Collum",
        "genus": "Frutexa",
        "base_value": 1639800,
        "colony_distance_m": 150,
        "description": "A species of frutexa characterised by its spiky lower branches surrounding a thick central column, which is dotted with spores and with a dark crown.",
        "variants": {
            "B": "Lime",
            "F": "Green",
            "G": "Emerald",
            "M": "Grey",
            "L": "Teal",
            "TTS": "Mauve",
            "D": "Indigo",
            "N": "Red",
            "W": "Orange",
            "O": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 130
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 215
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.00455
                    }
                ]
            ]
        ]
    },
    "Frutexa Fera": {
        "species_name": "Frutexa Fera",
        "genus": "Frutexa",
        "base_value": 1632500,
        "colony_distance_m": 150,
        "description": "This species of frutexa combines broad branches with long thin stalks, along which grow clusters of lightweight seed pods that are scattered by light winds.",
        "variants": {
            "B": "Lime",
            "F": "Green",
            "G": "Emerald",
            "M": "Grey",
            "L": "Teal",
            "TTS": "Mauve",
            "D": "Indigo",
            "N": "Red",
            "W": "Orange",
            "O": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 146
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0027
                    }
                ]
            ]
        ]
    },
    "Frutexa Flabellum": {
        "species_name": "Frutexa Flabellum",
        "genus": "Frutexa",
        "base_value": 1808900,
        "colony_distance_m": 150,
        "description": "A species of frutexa that appears as a bush of leaves with a similar texture to seaweed. Seeds are extended on long stalks and protected by a cage formation until ready to germinate.",
        "variants": {
            "B": "Lime",
            "F": "Green",
            "G": "Emerald",
            "M": "Grey",
            "L": "Teal",
            "TTS": "Mauve",
            "D": "Indigo",
            "N": "Red",
            "W": "Orange",
            "O": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0133
                    }
                ]
            ]
        ]
    },
    "Frutexa Flammasis": {
        "species_name": "Frutexa Flammasis",
        "genus": "Frutexa",
        "base_value": 10326000,
        "colony_distance_m": 150,
        "description": "A frutexa species that gives the appearance of flames, with vivid upright fronds extended from multiple stalks. The fronds are dotted with disc-shaped spores that are distributed by the wind.",
        "variants": {
            "B": "Lime",
            "F": "Green",
            "G": "Emerald",
            "M": "Grey",
            "L": "Teal",
            "TTS": "Mauve",
            "D": "Indigo",
            "N": "Red",
            "W": "Orange",
            "O": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0133
                    }
                ]
            ]
        ]
    },
    "Frutexa Metallicum": {
        "species_name": "Frutexa Metallicum",
        "genus": "Frutexa",
        "base_value": 1632500,
        "colony_distance_m": 150,
        "description": "This species of frutexa has an almost metallic shine to its small leaves. Along its upper branches grow spherical spores, which each have a star-shaped opening to increase germination.",
        "variants": {
            "B": "Lime",
            "F": "Green",
            "G": "Emerald",
            "M": "Grey",
            "L": "Teal",
            "TTS": "Mauve",
            "D": "Indigo",
            "N": "Red",
            "W": "Orange",
            "O": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 146
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 175
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ],
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 390
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 410
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    }
                ]
            ]
        ]
    },
    "Frutexa Sponsae": {
        "species_name": "Frutexa Sponsae",
        "genus": "Frutexa",
        "base_value": 5988000,
        "colony_distance_m": 150,
        "description": "A frutexa species that produces clusters of upright intertwining branches, which are crowned with bright seed sacks.",
        "variants": {
            "B": "Lime",
            "F": "Green",
            "G": "Emerald",
            "M": "Grey",
            "L": "Teal",
            "TTS": "Mauve",
            "D": "Indigo",
            "N": "Red",
            "W": "Orange",
            "O": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 399
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 452
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.052
                    }
                ]
            ]
        ]
    },
    "Fumerola Aquatis": {
        "species_name": "Fumerola Aquatis",
        "genus": "Fumerola",
        "base_value": 6284600,
        "colony_distance_m": 100,
        "description": "A species of fumerola that can be found near sites of water-based volcanic activity. They appear as small dark clusters with ridged folds that trap heat within.",
        "variants": {
            "UNKNOWN": "Orange"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.029
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "WATER_BASED"
                    }
                ]
            ]
        ]
    },
    "Fumerola Carbosis": {
        "species_name": "Fumerola Carbosis",
        "genus": "Fumerola",
        "base_value": 6284600,
        "colony_distance_m": 100,
        "description": "A fumerola species found near sites of carbon-based volcanism, appearing as a thin upright tube. An inner organism protrudes from an opening at its peak to increase heat absorption.",
        "variants": {
            "UNKNOWN": "Cyan"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.025
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "CARBON_BASED"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "METHANE_BASED"
                    }
                ]
            ]
        ]
    },
    "Fumerola Extremus": {
        "species_name": "Fumerola Extremus",
        "genus": "Fumerola",
        "base_value": 16202800,
        "colony_distance_m": 100,
        "description": "An exception among its kin, this fumerola species seems to have an arbitrary preference of specific volcanism types which have yet to be explicitly linked in any way. They appear as long vertical stalks with smaller fronds that can stretch out.",
        "variants": {
            "UNKNOWN": "Peach"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "IRON_BASED"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "SILICATE_BASED"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ROCKY_BASED"
                    }
                ]
            ]
        ]
    },
    "Fumerola Nitris": {
        "species_name": "Fumerola Nitris",
        "genus": "Fumerola",
        "base_value": 7500900,
        "colony_distance_m": 100,
        "description": "This species of fumerola prefers nitrogen-based volcanism. They produce an ovoid organism with dotted markings, which sits on top of a thin stalk.",
        "variants": {
            "UNKNOWN": "Mulberry"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.025
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "NITROGEN_BASED"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "AMMONIA_BASED"
                    }
                ]
            ]
        ]
    },
    "Fungoida Bullarum": {
        "species_name": "Fungoida Bullarum",
        "genus": "Fungoida",
        "base_value": 3703200,
        "colony_distance_m": 300,
        "description": "A fungoida that features clusters of mottled bubble-shaped growths atop a central stalk. These contain spores that can be exposed to the winds to facilitate distribution.",
        "variants": {
            "UNKNOWN": "Orange"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.0587
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 14
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 50
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 70
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 50
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 135
                    }
                ]
            ]
        ]
    },
    "Fungoida Gelata": {
        "species_name": "Fungoida Gelata",
        "genus": "Fungoida",
        "base_value": 3330300,
        "colony_distance_m": 300,
        "description": "This fungoida species resembles an upturned jellyfish, emerging from a solid case buried within the substrate. The exposed part is dominated by fleshy reproductive organisms that shed organic tissue. This tissue can float on the light breeze and form a new organism if it lands in the right location.",
        "variants": {
            "UNKNOWN": "Red"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0134
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 80
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 110
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0129
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 200
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 97.5
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0254
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0987
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 395
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 455
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.052
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0987
                    }
                ]
            ]
        ]
    },
    "Fungoida Setisis": {
        "species_name": "Fungoida Setisis",
        "genus": "Fungoida",
        "base_value": 1670100,
        "colony_distance_m": 300,
        "description": "This fungoida species produces vertical clusters interspersed with spore pods atop thin stalks, allowing them to break off and scatter to reproduce elsewhere.",
        "variants": {
            "UNKNOWN": "Orange"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.032
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 67
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 109
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 16,
                        "dvalue": 99.5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.013015
                    }
                ]
            ]
        ]
    },
    "Fungoida Stabitis": {
        "species_name": "Fungoida Stabitis",
        "genus": "Fungoida",
        "base_value": 2680300,
        "colony_distance_m": 300,
        "description": "A species of fungoida that thrives on geothermal energy, and can produce two-metre high tower structures composed of tightly clustered cylinders.",
        "variants": {
            "UNKNOWN": "Orange"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.041
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 78
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 110
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0125
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0987
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 390
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 452
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.056
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0987
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 97.5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0259
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0987
                    }
                ]
            ]
        ]
    },
    "Osseus Cornibus": {
        "species_name": "Osseus Cornibus",
        "genus": "Osseus",
        "base_value": 1483000,
        "colony_distance_m": 800,
        "description": "An osseus species that produces a stacked series of spiral structures up to about three metres. These ridged features are upturned to better absorb sunlight for photosynthesis.",
        "variants": {
            "A": "Lime",
            "F": "Turquoise",
            "G": "Grey",
            "K": "Indigo",
            "T": "Emerald",
            "TTS": "Green",
            "O": "Yellow",
            "Y": "Maroon"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.025
                    }
                ]
            ]
        ]
    },
    "Osseus Discus": {
        "species_name": "Osseus Discus",
        "genus": "Osseus",
        "base_value": 12934900,
        "colony_distance_m": 800,
        "description": "An osseus that appears as half-buried discs with radial patterns, which may resemble natural rock formations from a distance. They absorb geothermal energy from below the surface as well as available heat sources above ground.",
        "variants": {
            "UNKNOWN": "Blue"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ]
        ]
    },
    "Osseus Fractus": {
        "species_name": "Osseus Fractus",
        "genus": "Osseus",
        "base_value": 4027800,
        "colony_distance_m": 800,
        "description": "This osseus species can grow to over six metres across. The produce wide ridged frills for metabolic interactions including absorbing sunlight for energy production.",
        "variants": {
            "A": "Lime",
            "F": "Turquoise",
            "G": "Grey",
            "K": "Indigo",
            "T": "Emerald",
            "TTS": "Green",
            "O": "Yellow",
            "Y": "Maroon"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 180
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 190
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.025
                    }
                ]
            ]
        ]
    },
    "Osseus Pellebantus": {
        "species_name": "Osseus Pellebantus",
        "genus": "Osseus",
        "base_value": 9739000,
        "colony_distance_m": 800,
        "description": "A species of osseus with a single broad stalk from which extend wide circular structures, with the largest plate capping the top to maximize sunlight absorption.",
        "variants": {
            "A": "Lime",
            "F": "Turquoise",
            "G": "Grey",
            "K": "Indigo",
            "T": "Emerald",
            "TTS": "Green",
            "O": "Yellow",
            "Y": "Maroon"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 190
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.058
                    }
                ]
            ]
        ]
    },
    "Osseus Pumice": {
        "species_name": "Osseus Pumice",
        "genus": "Osseus",
        "base_value": 3156300,
        "colony_distance_m": 800,
        "description": "This osseus species grows a single thick stalk from which emerges a wide, broadly circular, pitted endoskeleton. This structure is designed to dramatically increase the surface area to volume of the organism, facilitating chemical capture and chemosynthesis on its catalytically active surface.",
        "variants": {
            "UNKNOWN": "Yellow"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 11
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 4
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 14
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ]
        ]
    },
    "Osseus Spiralis": {
        "species_name": "Osseus Spiralis",
        "genus": "Osseus",
        "base_value": 2404700,
        "colony_distance_m": 800,
        "description": "A species of osseus that produces coiling spiral structures up to six metres wide. There are ridged folds on their upturned surfaces designed to capture sunlight.",
        "variants": {
            "A": "Lime",
            "F": "Turquoise",
            "G": "Grey",
            "K": "Indigo",
            "T": "Emerald",
            "TTS": "Green",
            "O": "Yellow",
            "Y": "Maroon"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.015
                    }
                ]
            ]
        ]
    },
    "Recepta Conditivus": {
        "species_name": "Recepta Conditivus",
        "genus": "Recepta",
        "base_value": 14313700,
        "colony_distance_m": 150,
        "description": "A recepta species where the body of the organism is suspended above ground inside a sphere-shaped translucent membrane. This is filled with chemical-rich fluid that both protects the organism and provides the chemical soup needed for metabolism. Chemical exchange is controlled actively through the membrane and passively through the extensive root structure.",
        "variants": {
            "UNKNOWN": "Green"
        },
        "requirements": []
    },
    "Recepta Deltahedronix": {
        "species_name": "Recepta Deltahedronix",
        "genus": "Recepta",
        "base_value": 16202800,
        "colony_distance_m": 150,
        "description": "This species of recepta produces a thick lattice of trunks in a deltahedron shape. This grows around and above the globular central organism, and helps to capture, retain and focus geothermal heat for thermosynthesis.",
        "variants": {
            "UNKNOWN": "Gold"
        },
        "requirements": []
    },
    "Recepta Umbrux": {
        "species_name": "Recepta Umbrux",
        "genus": "Recepta",
        "base_value": 12934900,
        "colony_distance_m": 150,
        "description": "A recepta species that grows a thick latticed structure for protection. A fine translucent membrane stretches between its gaps, allowing sunlight to penetrate and reach the inner organism for photosynthesis.",
        "variants": {
            "A": "Amethyst",
            "F": "Mauve",
            "G": "Orange",
            "K": "Red",
            "M": "Maroon",
            "T": "Teal",
            "B": "Turquoise",
            "L": "Ocher",
            "N": "Emerald",
            "TTS": "Sage",
            "AEBE": "Grey",
            "D": "Yellow",
            "Y": "Lime",
            "O": "Indigo"
        },
        "requirements": []
    },
    "Stratum Araneamus": {
        "species_name": "Stratum Araneamus",
        "genus": "Stratum",
        "base_value": 2448900,
        "colony_distance_m": 500,
        "description": "A stratum species that has a vaguely octopoid shape. Their pale semi-translucent upper domes can reveal colourful inner organisms, which contrast with their darker outstretched tentacles.",
        "variants": {
            "B": "Emerald",
            "A": "Emerald",
            "N": "Emerald",
            "T": "Emerald"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 165
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 375
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.26
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.55
                    }
                ]
            ]
        ]
    },
    "Stratum Cucumisis": {
        "species_name": "Stratum Cucumisis",
        "genus": "Stratum",
        "base_value": 16202800,
        "colony_distance_m": 500,
        "description": "A species of stratum that displays fleshy ovoid shapes that are connected in a narrow pattern across the ground. These are covered with streaks of round photosynthetic cells that absorb sunlight.",
        "variants": {
            "F": "Emerald",
            "K": "Lime",
            "M": "Green",
            "T": "Grey",
            "TTS": "Amethyst",
            "D": "Mauve",
            "W": "Red",
            "L": "Turquoise",
            "Y": "Indigo",
            "AEBE": "Teal"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 190
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 16
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 8,
                        "dvalue": 0.05
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.6
                    }
                ]
            ]
        ]
    },
    "Stratum Excutitus": {
        "species_name": "Stratum Excutitus",
        "genus": "Stratum",
        "base_value": 2448900,
        "colony_distance_m": 500,
        "description": "This stratum species appears as a mixture of tight concentric ring patterns and mottled proto-leaves in a mixture of dark hues.",
        "variants": {
            "F": "Emerald",
            "K": "Lime",
            "M": "Green",
            "T": "Grey",
            "TTS": "Amethyst",
            "D": "Mauve",
            "W": "Red",
            "L": "Turquoise",
            "Y": "Indigo",
            "AEBE": "Teal"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 165
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 190
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 16
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 8,
                        "dvalue": 0.05
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.49
                    }
                ]
            ]
        ]
    },
    "Stratum Frigus": {
        "species_name": "Stratum Frigus",
        "genus": "Stratum",
        "base_value": 2637500,
        "colony_distance_m": 500,
        "description": "This species of stratum forms broad interconnected ring structures, which are composed of narrow ridges to capture sunlight.",
        "variants": {
            "F": "Emerald",
            "K": "Lime",
            "M": "Green",
            "T": "Grey",
            "TTS": "Amethyst",
            "D": "Mauve",
            "W": "Red",
            "L": "Turquoise",
            "Y": "Indigo",
            "AEBE": "Teal"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 190
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.55
                    }
                ]
            ]
        ]
    },
    "Stratum Laminamus": {
        "species_name": "Stratum Laminamus",
        "genus": "Stratum",
        "base_value": 2788300,
        "colony_distance_m": 500,
        "description": "This particular stratum species gives the appearance of overlapping rock plateaus, each with narrow bandsof colouration.",
        "variants": {
            "F": "Emerald",
            "K": "Lime",
            "M": "Green",
            "T": "Grey",
            "TTS": "Amethyst",
            "D": "Mauve",
            "W": "Red",
            "L": "Turquoise",
            "Y": "Indigo",
            "AEBE": "Teal"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 165
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.34
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.013
                    }
                ]
            ]
        ]
    },
    "Stratum Limaxus": {
        "species_name": "Stratum Limaxus",
        "genus": "Stratum",
        "base_value": 1362000,
        "colony_distance_m": 500,
        "description": "This species of stratum appears as a series of unconnected ovoid shapes across the ground, which are the protruding tips of the larger subterranean organism.",
        "variants": {
            "F": "Emerald",
            "K": "Lime",
            "M": "Green",
            "T": "Grey",
            "TTS": "Amethyst",
            "D": "Mauve",
            "W": "Red",
            "L": "Turquoise",
            "Y": "Indigo",
            "AEBE": "Teal"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 165
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 190
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.48
                    }
                ]
            ]
        ]
    },
    "Stratum Paleas": {
        "species_name": "Stratum Paleas",
        "genus": "Stratum",
        "base_value": 1362000,
        "colony_distance_m": 500,
        "description": "A stratum that blends thick overlapping vines with irregular growths, with varying colours appearing in bands or streaks.",
        "variants": {
            "F": "Emerald",
            "K": "Lime",
            "M": "Green",
            "T": "Grey",
            "TTS": "Amethyst",
            "D": "Mauve",
            "W": "Red",
            "L": "Turquoise",
            "Y": "Indigo",
            "AEBE": "Teal"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 165
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 16
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 450
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 394
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.0359
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.6
                    }
                ]
            ]
        ]
    },
    "Stratum Tectonicas": {
        "species_name": "Stratum Tectonicas",
        "genus": "Stratum",
        "base_value": 19010800,
        "colony_distance_m": 500,
        "description": "A stratum species with a thick rock-like outer shell, covered with an irregular lattice of brighter cells that absorb sunlight for photosynthesis.",
        "variants": {
            "F": "Emerald",
            "K": "Lime",
            "M": "Green",
            "T": "Grey",
            "TTS": "Amethyst",
            "D": "Mauve",
            "W": "Red",
            "L": "Turquoise",
            "Y": "Indigo",
            "AEBE": "Teal"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 165
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 16
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 450
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 450
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 178
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 4
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 250
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 250
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.0456
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.61
                    }
                ]
            ]
        ]
    },
    "Tubus Cavas": {
        "species_name": "Tubus Cavas",
        "genus": "Tubus",
        "base_value": 11873200,
        "colony_distance_m": 800,
        "description": "A tubus species that extends pale vertical stalks composed of rigid modules. Colourful fronds frequently appear in the gaps between segments and aid with controlling gaseous exchange.",
        "variants": {
            "B": "Emerald",
            "A": "Indigo",
            "F": "Grey",
            "G": "Red",
            "K": "Maroon",
            "M": "Teal",
            "L": "Turquoise",
            "T": "Mauve",
            "TTS": "Ocher",
            "N": "Amethyst",
            "W": "Lime",
            "D": "Yellow",
            "O": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 195.1
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.003
                    }
                ]
            ]
        ]
    },
    "Tubus Compagibus": {
        "species_name": "Tubus Compagibus",
        "genus": "Tubus",
        "base_value": 7774700,
        "colony_distance_m": 800,
        "description": "A tubus species with narrow pale segments and fronds growing between each module. A wide crown of leaves at the peak hold spores on their undersides, to germinate across a wide area.",
        "variants": {
            "B": "Emerald",
            "A": "Indigo",
            "F": "Grey",
            "G": "Red",
            "K": "Maroon",
            "M": "Teal",
            "L": "Turquoise",
            "T": "Mauve",
            "TTS": "Ocher",
            "N": "Amethyst",
            "W": "Lime",
            "D": "Yellow",
            "O": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196.1
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.003
                    }
                ]
            ]
        ]
    },
    "Tubus Conifer": {
        "species_name": "Tubus Conifer",
        "genus": "Tubus",
        "base_value": 2415500,
        "colony_distance_m": 800,
        "description": "A tubus species formed from hollow vertical cylinders that can reach heights of six metres. Mature specimens are capped with a downturned crown that can distribute seeds on the wind across a wide area.",
        "variants": {
            "B": "Emerald",
            "A": "Indigo",
            "F": "Grey",
            "G": "Red",
            "K": "Maroon",
            "M": "Teal",
            "L": "Turquoise",
            "T": "Mauve",
            "TTS": "Ocher",
            "N": "Amethyst",
            "W": "Lime",
            "D": "Yellow",
            "O": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 195.3
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.003
                    }
                ]
            ]
        ]
    },
    "Tubus Rosarium": {
        "species_name": "Tubus Rosarium",
        "genus": "Tubus",
        "base_value": 2637500,
        "colony_distance_m": 800,
        "description": "This tubus species is composed of squat tubes growing into a vertical spire. The upper pods of matures specimens produce explosive seed pods on their outer skin.",
        "variants": {
            "B": "Emerald",
            "A": "Indigo",
            "F": "Grey",
            "G": "Red",
            "K": "Maroon",
            "M": "Teal",
            "L": "Turquoise",
            "T": "Mauve",
            "TTS": "Ocher",
            "N": "Amethyst",
            "W": "Lime",
            "D": "Yellow",
            "O": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0134
                    }
                ]
            ]
        ]
    },
    "Tubus Sororibus": {
        "species_name": "Tubus Sororibus",
        "genus": "Tubus",
        "base_value": 5727600,
        "colony_distance_m": 800,
        "description": "This species of tubus grows a cluster of hollow stalks composed of rigid segments. Over time these become capped with a growth that flowers and produces seeds.",
        "variants": {
            "B": "Emerald",
            "A": "Indigo",
            "F": "Grey",
            "G": "Red",
            "K": "Maroon",
            "M": "Teal",
            "L": "Turquoise",
            "T": "Mauve",
            "TTS": "Ocher",
            "N": "Amethyst",
            "W": "Lime",
            "D": "Yellow",
            "O": "Green"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 160
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 189
                    }
                ]
            ],
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    }
                ]
            ]
        ]
    },
    "Tussock Albata": {
        "species_name": "Tussock Albata",
        "genus": "Tussock",
        "base_value": 3252500,
        "colony_distance_m": 200,
        "description": "A tussock species characterised by leaves with a distinctive striped pattern that are bisected like a snake's tongue. Mature versions also sprout smaller leaves which produce spores.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 97.5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 175
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 180
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.042
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.016
                    }
                ]
            ]
        ]
    },
    "Tussock Capillum": {
        "species_name": "Tussock Capillum",
        "genus": "Tussock",
        "base_value": 7025800,
        "colony_distance_m": 200,
        "description": "This tussock species is a squat cluster of leaves resembling thick matted hair. From the top of these sprout thick pods that carry a number of beans.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 3
                    }
                ],
                [
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 110
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 80
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 129
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.032
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ]
        ]
    },
    "Tussock Caputus": {
        "species_name": "Tussock Caputus",
        "genus": "Tussock",
        "base_value": 3472400,
        "colony_distance_m": 200,
        "description": "A tussock species with leaves that have a thick segmented lower half and a willowy upper half. Mature versions produce separate stalks that carry ovoid organisms dotted with spores.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 97.5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 179
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 190
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.027
                    }
                ]
            ]
        ]
    },
    "Tussock Catena": {
        "species_name": "Tussock Catena",
        "genus": "Tussock",
        "base_value": 1766600,
        "colony_distance_m": 200,
        "description": "This species of tussock has very thin stalks carrying twin sets of seed sacks along their entire length, resembling links on a chain.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 16,
                        "dvalue": 100
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0133
                    }
                ]
            ]
        ]
    },
    "Tussock Cultro": {
        "species_name": "Tussock Cultro",
        "genus": "Tussock",
        "base_value": 1766600,
        "colony_distance_m": 200,
        "description": "A tussock species with tall sharp reeds reaching about two metres, characterised by narrow markings along their length.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 16,
                        "dvalue": 99.4
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0134
                    }
                ]
            ]
        ]
    },
    "Tussock Divisa": {
        "species_name": "Tussock Divisa",
        "genus": "Tussock",
        "base_value": 1766600,
        "colony_distance_m": 200,
        "description": "This tussock species blends thick segmented lower growths with longer, narrower leaves. Mature versions have pale spores along the upper branches.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 0
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 16,
                        "dvalue": 99.4
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 152
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 177
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0133
                    }
                ]
            ]
        ]
    },
    "Tussock Ignis": {
        "species_name": "Tussock Ignis",
        "genus": "Tussock",
        "base_value": 1849000,
        "colony_distance_m": 200,
        "description": "This tussock species produces thick intertwined leaves, above which sprout narrow stems crowned with seed pods.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 96.5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 161
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 170
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0031
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0523
                    }
                ]
            ]
        ]
    },
    "Tussock Pennata": {
        "species_name": "Tussock Pennata",
        "genus": "Tussock",
        "base_value": 5853800,
        "colony_distance_m": 200,
        "description": "A tussock species that extends large seed pods on thin stems above a cluster of bright leaves.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "ATMOSPHERE_COMPOSITION",
                        "ivalue": 4,
                        "dvalue": 97.5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 145.6
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 154
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0027
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0115
                    }
                ]
            ]
        ]
    },
    "Tussock Pennatis": {
        "species_name": "Tussock Pennatis",
        "genus": "Tussock",
        "base_value": 1000000,
        "colony_distance_m": 200,
        "description": "A tussock species with feather-shaped growths surrounding a single segmented stem, which when mature is crowned with colourful seeds.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 146
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0027
                    }
                ]
            ]
        ]
    },
    "Tussock Propagito": {
        "species_name": "Tussock Propagito",
        "genus": "Tussock",
        "base_value": 1000000,
        "colony_distance_m": 200,
        "description": "A species of tussock that sprouts tapering leaves, with tips covered with colourful seed pods.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 145
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0027
                    }
                ]
            ]
        ]
    },
    "Tussock Serrati": {
        "species_name": "Tussock Serrati",
        "genus": "Tussock",
        "base_value": 4447100,
        "colony_distance_m": 200,
        "description": "This tussock species sprouts serrated leaves around thick stalks that produce dark seed pods.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 168
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 178
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.01
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0705
                    }
                ]
            ]
        ]
    },
    "Tussock Stigmasis": {
        "species_name": "Tussock Stigmasis",
        "genus": "Tussock",
        "base_value": 19010800,
        "colony_distance_m": 200,
        "description": "This tussock species resembles a patch of tough, wiry grasses. Taller stalks carrying disc-shaped seed pods rise above the main organism when mature.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 18
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 132
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 167
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.0057
                    }
                ]
            ]
        ]
    },
    "Tussock Triticum": {
        "species_name": "Tussock Triticum",
        "genus": "Tussock",
        "base_value": 7774700,
        "colony_distance_m": 200,
        "description": "A species of tussock with thin tough leaves marked with dark stripes. From these sprout taller stalks with small leaves, from which seeds are released to the winds.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 191
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 196
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.058
                    }
                ]
            ]
        ]
    },
    "Tussock Ventusa": {
        "species_name": "Tussock Ventusa",
        "genus": "Tussock",
        "base_value": 3227700,
        "colony_distance_m": 200,
        "description": "A species of tussock that blends tough lower stalks with taller willowy reeds, which produce small pale spores.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 155
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 160
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.0027
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.022
                    }
                ]
            ]
        ]
    },
    "Tussock Virgam": {
        "species_name": "Tussock Virgam",
        "genus": "Tussock",
        "base_value": 14313700,
        "colony_distance_m": 200,
        "description": "A species of tussock with thin reeds clustered around a central stalk, which is eventually crowned with spores.",
        "variants": {
            "F": "Yellow",
            "N": "Yellow",
            "G": "Lime",
            "K": "Green",
            "M": "Emerald",
            "L": "Sage",
            "T": "Teal",
            "D": "Maroon",
            "W": "Orange",
            "Y": "Red",
            "AEBE": "Amethyst"
        },
        "requirements": [
            [
                [
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 19
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 392
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 450
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.052
                    }
                ]
            ]
        ]
    },
    "Roseum Brain Tree": {
        "species_name": "Roseum Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 200
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 500
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.028
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 4.2
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ]
        ]
    },
    "Gypseeum Brain Tree": {
        "species_name": "Gypseeum Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 200
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 330
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.042
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.42
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "MINOR"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "REGULAR"
                    },
                    {
                        "type": "VOLCANISM",
                        "svalue": "IRON_BASED"
                    }
                ]
            ]
        ]
    },
    "Ostrinum Brain Tree": {
        "species_name": "Ostrinum Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 1000
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 1000
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.034
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 2.35
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "NOT_MAJOR"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "IS_IN_SPHERE",
                        "ivalue": 4
                    }
                ]
            ]
        ]
    },
    "Viride Brain Tree": {
        "species_name": "Viride Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 100
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 255
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.035
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.4
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ]
        ]
    },
    "Lividum Brain Tree": {
        "species_name": "Lividum Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 300
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 500
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.029
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.47
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ]
        ]
    },
    "Aureum Brain Tree": {
        "species_name": "Aureum Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 300
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 500
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.035
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 2.92
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ]
        ]
    },
    "Lindigoticum Brain Tree": {
        "species_name": "Lindigoticum Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 300
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 500
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.047
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 2.6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "NOT_MINOR"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "IS_IN_SPHERE",
                        "ivalue": 3
                    }
                ]
            ]
        ]
    },
    "Puniceum Brain Tree": {
        "species_name": "Puniceum Brain Tree",
        "genus": "Brain Trees",
        "base_value": 1593700,
        "colony_distance_m": 500,
        "description": "These resilient organic structures absorb minerals via their subsurface roots and energy via their outer skin.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.039
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 3.9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 1000
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 1000
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "IS_IN_SPHERE",
                        "ivalue": 5
                    }
                ]
            ]
        ]
    },
    "Crystalline Shards": {
        "species_name": "Crystalline Shards",
        "genus": "Crystalline Shards",
        "base_value": 1628800,
        "colony_distance_m": 500,
        "description": "These crystalline structures are created by large colonies of microorganisms.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.027
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 2
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 273
                    }
                ]
            ],
            [
                [
                    {
                        "type": "DISTANCE_LS_FROM_START_MIN",
                        "dvalue": 12000
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 3
                    }
                ],
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 4
                    }
                ],
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 5
                    }
                ],
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 18
                    }
                ]
            ]
        ]
    },
    "Amphora Plant": {
        "species_name": "Amphora Plant",
        "genus": "Amphora Plant",
        "base_value": 1628800,
        "colony_distance_m": 500,
        "description": "These organic structures take their name from a type of container dating from the Earth's Neolithic period.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 4.5
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 1000
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "MAJOR"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 3
                    }
                ]
            ]
        ]
    },
    "Bark Mounds": {
        "species_name": "Bark Mounds",
        "genus": "Bark Mounds",
        "base_value": 1471900,
        "colony_distance_m": 500,
        "description": "These organic structures survive by absorbing elements from nova and supernova, with the dense outer layer protecting them from the severest radiation.",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.0249
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 3.462
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 200
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 440
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "IS_IN_SPHERE",
                        "ivalue": 0
                    }
                ]
            ]
        ]
    },
    "Anemone Blatteum Bioluminescent Anemone": {
        "species_name": "Anemone Blatteum Bioluminescent Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 200
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.036
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 2
                    }
                ]
            ]
        ]
    },
    "Anemone Rubeum Bioluminescent Anemone": {
        "species_name": "Anemone Rubeum Bioluminescent Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 164
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.036
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 3
                    }
                ],
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 2
                    }
                ]
            ]
        ]
    },
    "Anemone Prasinum Bioluminescent Anemone": {
        "species_name": "Anemone Prasinum Bioluminescent Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.036
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 1
                    }
                ]
            ]
        ]
    },
    "Anemone Roseum Bioluminescent Anemone": {
        "species_name": "Anemone Roseum Bioluminescent Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 8
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 191
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.036
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 2
                    }
                ]
            ]
        ]
    },
    "Anemone Luteolum Anemone": {
        "species_name": "Anemone Luteolum Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 200
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.042
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 2
                    }
                ]
            ]
        ]
    },
    "Anemone Croceum Anemone": {
        "species_name": "Anemone Croceum Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 200
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.042
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 3
                    }
                ],
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 2
                    }
                ]
            ]
        ]
    },
    "Anemone Puniceum Anemone": {
        "species_name": "Anemone Puniceum Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 7
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.042
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 1
                    }
                ]
            ]
        ]
    },
    "Anemone Roseum Anemone": {
        "species_name": "Anemone Roseum Anemone",
        "genus": "Anemone",
        "base_value": 1499900,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 200
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.042
                    }
                ]
            ],
            [
                [
                    {
                        "type": "SYSTEM_HAS_STAR",
                        "ivalue": 2
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Roseum Sinuous Tubers": {
        "species_name": "Sinuous Tubers Roseum Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 10
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ROCKY"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "SILICATE_BASED"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.044
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Blatteum Sinuous Tubers": {
        "species_name": "Sinuous Tubers Blatteum Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.044
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Lindigoticum Sinuous Tubers": {
        "species_name": "Sinuous Tubers Lindigoticum Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "MAJOR"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.036
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Violaceum Sinuous Tubers": {
        "species_name": "Sinuous Tubers Violaceum Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.044
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Viride Sinuous Tubers": {
        "species_name": "Sinuous Tubers Viride Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "MAJOR"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.044
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Prasinum Sinuous Tubers": {
        "species_name": "Sinuous Tubers Prasinum Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ANY"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.044
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Albidum Sinuous Tubers": {
        "species_name": "Sinuous Tubers Albidum Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "ROCKY"
                    }
                ],
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "SILICATE_BASED"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.044
                    }
                ]
            ]
        ]
    },
    "Sinuous Tubers Caeruleum Sinuous Tubers": {
        "species_name": "Sinuous Tubers Caeruleum Sinuous Tubers",
        "genus": "Sinuous Tubers",
        "base_value": 1514500,
        "colony_distance_m": 500,
        "description": "",
        "variants": {
            "UNKNOWN": "Horizons"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    }
                ]
            ],
            [
                [
                    {
                        "type": "VOLCANISM",
                        "svalue": "MAJOR"
                    }
                ]
            ],
            [
                [
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.04
                    }
                ]
            ]
        ]
    },
    "Radicoida Unica": {
        "species_name": "Radicoida Unica",
        "genus": "Radicoida",
        "base_value": 7200000,
        "colony_distance_m": 1000,
        "description": "Unique flora found under hot thin carbon dioxide atmospheres.",
        "variants": {
            "O": "Teal",
            "B": "Cyan",
            "A": "Blue",
            "F": "Emerald",
            "G": "Yellow",
            "K": "Orange",
            "M": "Red",
            "L": "Maroon",
            "T": "Mauve"
        },
        "requirements": [
            [
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 6
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 467.0
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 699.0
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.007
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.06
                    },
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.05
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.38
                    }
                ],
                [
                    {
                        "type": "PLANET_TYPE",
                        "ivalue": 9
                    },
                    {
                        "type": "ATMOSPHERE_TYPE",
                        "ivalue": 5
                    },
                    {
                        "type": "TEMPERATURE_MIN",
                        "dvalue": 467.0
                    },
                    {
                        "type": "TEMPERATURE_MAX",
                        "dvalue": 699.0
                    },
                    {
                        "type": "PRESSURE_MIN",
                        "dvalue": 0.007
                    },
                    {
                        "type": "PRESSURE_MAX",
                        "dvalue": 0.06
                    },
                    {
                        "type": "GRAVITY_MIN",
                        "dvalue": 0.05
                    },
                    {
                        "type": "GRAVITY_MAX",
                        "dvalue": 0.38
                    }
                ]
            ]
        ]
    }
}

# Alias for backwards compatibility
EXOBIOLOGY_SPECIES_CONDITIONS = BIOINSIGHTS_SPECIES_RULES


def normalize_atmosphere_type(atmo_str: str) -> int:
    s = (atmo_str or "").lower().replace("thin ", "").replace("hot thin ", "").replace("thick ", "").strip()
    if s in ATMOSPHERE_TYPE_MAP:
        return ATMOSPHERE_TYPE_MAP[s]
    for k, v in ATMOSPHERE_TYPE_MAP.items():
        if k in s:
            return v
    return 15  # None


def normalize_planet_class(pc_str: str) -> int:
    s = (pc_str or "").lower().strip()
    if s in PLANET_CLASS_MAP:
        return PLANET_CLASS_MAP[s]
    for k, v in PLANET_CLASS_MAP.items():
        if k in s:
            return v
    return 0


def determine_variant_color(sp_rule: dict, body_data: dict) -> str:
    star_type = (body_data.get("star_type") or body_data.get("main_star_type") or "").upper().strip()
    if star_type:
        clean_star = star_type.split()[0].replace(",", "")
        variants = sp_rule.get("variants", {})
        if clean_star in variants:
            return variants[clean_star]
        if len(clean_star) > 0 and clean_star[0] in variants:
            return variants[clean_star[0]]
    return "Standard"


def match_species_conditions(species_name: str, sp_rule: dict, body_data: dict) -> bool:
    """
    Evaluates BioInsights criteria (Planet Type, Atmosphere, Temperature, Gravity,
    Pressure, Volcanism, SemiMajorAxis, Distance LS) for a celestial body.
    """
    planet_class_id = normalize_planet_class(body_data.get("planet_class", ""))
    atmo_str = body_data.get("atmosphere") or body_data.get("atmosphere_type") or ""
    atmo_type_id = normalize_atmosphere_type(atmo_str)

    # 1. Gravity handling (G units)
    if "surface_gravity_g" in body_data:
        gravity = float(body_data["surface_gravity_g"])
    elif "gravity" in body_data:
        gravity = float(body_data["gravity"])
    elif "surface_gravity" in body_data and body_data["surface_gravity"] is not None:
        raw_g = float(body_data["surface_gravity"])
        gravity = raw_g / 9.80665
    else:
        gravity = 0.1

    # 2. Temperature (Kelvin)
    temp = float(body_data.get("surface_temperature") or 0.0)

    # 3. Pressure (atm)
    raw_p = float(body_data.get("surface_pressure") or 0.0)
    pressure_atm = raw_p / 101325.0 if raw_p > 5.0 else raw_p

    # 4. Volcanism
    volcanism = (body_data.get("volcanism") or "").lower()

    # 5. Semi-major axis (AU)
    sma_au = float(body_data.get("semi_major_axis_au") or 0.0)
    if sma_au == 0.0 and "semi_major_axis" in body_data and body_data["semi_major_axis"] is not None:
        raw_sma = float(body_data["semi_major_axis"])
        sma_au = raw_sma / 149597870700.0

    # 6. Distance LS
    dist_ls = float(body_data.get("distance_from_arrival_ls") or body_data.get("distance_ls") or 0.0)

    requirements = sp_rule.get("requirements", [])
    if not requirements:
        return True

    for req in requirements:
        or_satisfied = False
        for and_group in req:
            and_satisfied = True
            for cond in and_group:
                c_type = cond.get("type")

                if c_type == "PLANET_TYPE":
                    req_pc = cond.get("ivalue")
                    if req_pc is not None and planet_class_id != req_pc:
                        and_satisfied = False
                        break

                elif c_type == "ATMOSPHERE_TYPE":
                    req_at = cond.get("ivalue")
                    if req_at is not None and atmo_type_id != req_at:
                        and_satisfied = False
                        break

                elif c_type == "NOT_ATMOSPHERE_TYPE":
                    req_not_at = cond.get("ivalue")
                    if req_not_at is not None and atmo_type_id == req_not_at:
                        and_satisfied = False
                        break

                elif c_type == "TEMPERATURE_MIN":
                    t_min = cond.get("dvalue", cond.get("ivalue", 0))
                    if temp > 0 and temp < (t_min * 0.95):  # 5% tolerance
                        and_satisfied = False
                        break

                elif c_type == "TEMPERATURE_MAX":
                    t_max = cond.get("dvalue", cond.get("ivalue", 9999))
                    if temp > 0 and temp > (t_max * 1.05):  # 5% tolerance
                        and_satisfied = False
                        break

                elif c_type == "PRESSURE_MIN":
                    p_min = cond.get("dvalue", cond.get("ivalue", 0))
                    if pressure_atm > 0 and pressure_atm < (p_min * 0.90):  # 10% tolerance
                        and_satisfied = False
                        break

                elif c_type == "PRESSURE_MAX":
                    p_max = cond.get("dvalue", cond.get("ivalue", 999))
                    if pressure_atm > 0 and pressure_atm > (p_max * 1.10):  # 10% tolerance
                        and_satisfied = False
                        break

                elif c_type == "GRAVITY_MIN":
                    g_min = cond.get("dvalue", cond.get("ivalue", 0))
                    if gravity > 0 and gravity < (g_min * 0.90):  # 10% tolerance
                        and_satisfied = False
                        break

                elif c_type == "GRAVITY_MAX":
                    g_max = cond.get("dvalue", cond.get("ivalue", 99))
                    if gravity > 0 and gravity > (g_max * 1.10):  # 10% tolerance
                        and_satisfied = False
                        break

                elif c_type == "VOLCANISM":
                    req_v = (cond.get("svalue") or "").upper()
                    if req_v == "NONE":
                        if volcanism and volcanism != "none":
                            and_satisfied = False
                            break
                    elif req_v == "ANY":
                        if not volcanism or volcanism == "none":
                            and_satisfied = False
                            break
                    elif "NITROGEN" in req_v:
                        if "nitrogen" not in volcanism:
                            and_satisfied = False
                            break
                    elif "WATER" in req_v:
                        if "water" not in volcanism:
                            and_satisfied = False
                            break
                    elif "CARBON" in req_v or "METHANE" in req_v:
                        if "carbon" not in volcanism and "methane" not in volcanism and "silicate" not in volcanism:
                            and_satisfied = False
                            break

                elif c_type == "SMA_MAX":
                    sma_max = cond.get("dvalue", cond.get("ivalue", 9999))
                    if sma_au > 0 and sma_au > (sma_max * 1.10):
                        and_satisfied = False
                        break

                elif c_type == "SMA_MIN":
                    sma_min = cond.get("dvalue", cond.get("ivalue", 0))
                    if sma_au > 0 and sma_au < (sma_min * 0.90):
                        and_satisfied = False
                        break

                elif c_type == "DISTANCE_LS_FROM_START_MIN":
                    dist_min = cond.get("dvalue", cond.get("ivalue", 0))
                    if dist_ls > 0 and dist_ls < dist_min:
                        and_satisfied = False
                        break

                elif c_type == "DISTANCE_LS_FROM_START_MAX":
                    dist_max = cond.get("dvalue", cond.get("ivalue", 999999999))
                    if dist_ls > 0 and dist_ls > dist_max:
                        and_satisfied = False
                        break

            if and_satisfied:
                or_satisfied = True
                break

        if not or_satisfied:
            return False

    return True


def match_canonn_species_conditions(species_name: str, rule: dict, body_data: dict) -> bool:
    """
    Evaluates whether a celestial body satisfies Canonn Research environmental constraints
    for a specific exobiology species.
    """
    # 1. Planet Body Type check
    planet_class = (body_data.get("planet_class") or body_data.get("PlanetClass") or "").lower()
    body_type_raw = (rule.get("body_type_raw") or "").lower()
    if body_type_raw and planet_class:
        match_found = False
        if "high metal content" in body_type_raw and ("high metal" in planet_class or "hmc" in planet_class):
            match_found = True
        elif "rocky ice" in body_type_raw and "rocky ice" in planet_class:
            match_found = True
        elif "rocky" in body_type_raw and "rocky" in planet_class and "rocky ice" not in planet_class:
            match_found = True
        elif "ice" in body_type_raw and "icy" in planet_class:
            match_found = True
        elif "metal rich" in body_type_raw and "metal rich" in planet_class:
            match_found = True
        
        if not match_found and body_type_raw != "no preference":
            return False

    # 2. Atmosphere check
    atmo_str = (body_data.get("atmosphere") or body_data.get("Atmosphere") or body_data.get("atmosphere_type") or body_data.get("AtmosphereType") or "").lower()
    atmo_raw = (rule.get("atmosphere_raw") or "").lower()
    if atmo_raw:
        raw_parts = [a.strip() for a in re.split(r"or|and|,", atmo_raw) if a.strip()]
        allowed_atmos = [re.sub(r"\(.*?\)", "", a).strip() for a in raw_parts if a.strip()]
        atmo_match = False
        for allowed in allowed_atmos:
            if not allowed:
                continue
            if allowed in atmo_str or (allowed == "carbon dioxide" and "co2" in atmo_str) or (allowed == "sulphur dioxide" and "so2" in atmo_str):
                atmo_match = True
                break
        if not atmo_match:
            return False

    # 3. Surface Temperature (Kelvin)
    temp = float(body_data.get("surface_temperature") or body_data.get("SurfaceTemperature") or 0.0)
    t_data = rule.get("temperature", {})
    if t_data and temp > 0:
        t_min = t_data.get("min")
        t_max = t_data.get("max")
        if t_min is not None and temp < (t_min * 0.95):  # 5% tolerance
            return False
        if t_max is not None and temp > (t_max * 1.05):  # 5% tolerance
            return False

    # 4. Surface Pressure (atm)
    raw_p = float(body_data.get("surface_pressure") or body_data.get("SurfacePressure") or 0.0)
    pressure_atm = raw_p / 101325.0 if raw_p > 5.0 else raw_p
    p_data = rule.get("pressure_atm", {})
    if p_data and pressure_atm > 0:
        p_min = p_data.get("min")
        p_max = p_data.get("max")
        if p_min is not None and pressure_atm < (p_min * 0.90):  # 10% tolerance
            return False
        if p_max is not None and pressure_atm > (p_max * 1.10):  # 10% tolerance
            return False

    # 5. Surface Gravity (G)
    if "surface_gravity_g" in body_data:
        gravity = float(body_data["surface_gravity_g"])
    elif "gravity" in body_data:
        gravity = float(body_data["gravity"])
    elif "surface_gravity" in body_data and body_data["surface_gravity"] is not None:
        gravity = float(body_data["surface_gravity"]) / 9.80665
    elif "SurfaceGravity" in body_data and body_data["SurfaceGravity"] is not None:
        gravity = float(body_data["SurfaceGravity"]) / 9.80665
    else:
        gravity = 0.1
    
    g_data = rule.get("gravity_g", {})
    if g_data and gravity > 0:
        g_min = g_data.get("min")
        g_max = g_data.get("max")
        if g_min is not None and gravity < (g_min * 0.90):  # 10% tolerance
            return False
        if g_max is not None and gravity > (g_max * 1.10):  # 10% tolerance
            return False

    # 6. Volcanism check
    volcanism = (body_data.get("volcanism") or body_data.get("Volcanism") or "").lower()
    volc_raw = (rule.get("volcanism") or "").lower()
    if volc_raw and volc_raw == "none":
        if volcanism and "no volcanism" not in volcanism and volcanism != "none":
            return False

    return True


def determine_canonn_variant_color(rule: dict, body_data: dict) -> str:
    """
    Determines variant color from Canonn material variants or stellar class variants.
    """
    # 1. Material Variants (e.g. for Bacterium, Fumerola, Fungoida, etc.)
    mat_variants = rule.get("material_variants", {})
    if mat_variants:
        body_materials = body_data.get("materials") or body_data.get("Materials") or {}
        if isinstance(body_materials, dict):
            for mat_name, color in mat_variants.items():
                if mat_name in body_materials or mat_name.lower() in [k.lower() for k in body_materials.keys()]:
                    return color
        elif isinstance(body_materials, list):
            for item in body_materials:
                m_name = item.get("Name", "") if isinstance(item, dict) else str(item)
                for req_mat, color in mat_variants.items():
                    if req_mat.lower() == m_name.lower():
                        return color

    # 2. Stellar Class Variants
    stellar_variants = rule.get("stellar_class_variants", {})
    if stellar_variants:
        star_type = (body_data.get("star_type") or body_data.get("StarType") or body_data.get("parent_star_type") or body_data.get("main_star_type") or "").upper().strip()
        main_class = star_type.split('_')[0] if star_type else ""
        if main_class in stellar_variants:
            return stellar_variants[main_class]
        if star_type and star_type[0] in stellar_variants:
            return stellar_variants[star_type[0]]

    return "Standard"


# Canonn Research Temperature Band Distribution Matrix
# Table 1: Percentage of each Genus Population in each Temperature Band (K)
GENUS_TEMP_BAND_DISTRIBUTION = {
    "Aleoida":    { (151, 200): 100.0 },
    "Bacteria":   { (0, 50): 13.17, (51, 100): 27.85, (101, 150): 5.92, (151, 200): 37.37, (201, 250): 5.67, (251, 300): 2.52, (301, 350): 3.13, (351, 400): 1.42, (401, 450): 2.84, (451, 500): 0.11 },
    "Cactoida":   { (151, 200): 82.71, (351, 400): 0.17, (401, 450): 17.12 },
    "Clypeus":    { (151, 200): 49.70, (351, 400): 0.48, (401, 450): 49.75, (451, 500): 0.07 },
    "Concha":     { (0, 50): 0.74, (51, 100): 0.09, (101, 150): 1.16, (151, 200): 82.97, (351, 400): 0.15, (401, 450): 14.87, (451, 500): 0.02 },
    "Electricae": { (0, 50): 2.41, (51, 100): 85.06, (101, 150): 12.53 },
    "Fonticulua": { (0, 50): 1.69, (51, 100): 87.40, (101, 150): 10.67, (151, 200): 0.23 },
    "Frutexa":    { (101, 150): 1.84, (151, 200): 93.39, (351, 400): 0.07, (401, 450): 4.69, (451, 500): 0.01 },
    "Fumerola":   { (0, 50): 1.11, (51, 100): 74.35, (101, 150): 16.89, (151, 200): 5.70, (201, 250): 1.06, (251, 300): 0.17, (401, 450): 0.71, (451, 500): 0.01 },
    "Fungoida":   { (0, 50): 0.03, (51, 100): 9.54, (101, 150): 1.37, (151, 200): 78.68, (351, 400): 0.11, (401, 450): 10.26, (451, 500): 0.01 },
    "Osseus":     { (0, 50): 0.54, (51, 100): 14.72, (101, 150): 2.01, (151, 200): 74.66, (351, 400): 0.07, (401, 450): 7.97, (451, 500): 0.01 },
    "Recepta":    { (101, 150): 30.36, (151, 200): 54.69, (201, 250): 13.01, (251, 300): 1.94 },
    "Stratum":    { (151, 200): 80.68, (201, 250): 9.45, (251, 300): 3.65, (301, 350): 2.60, (351, 400): 0.99, (401, 450): 2.63 },
    "Tubus":      { (151, 200): 100.0 },
    "Tussock":    { (51, 100): 2.52, (101, 150): 2.69, (151, 200): 90.56, (351, 400): 0.05, (401, 450): 4.19 }
}

# Table 2: Genus Population as Percentage of Total Population in each Temperature Band
TEMP_BAND_TOTAL_POPULATION_SHARE = {
    (0, 50): {
        "Bacteria": 94.23, "Fonticulua": 2.98, "Osseus": 1.02, "Concha": 1.00, "Electricae": 0.52, "Fumerola": 0.20, "Fungoida": 0.05
    },
    (51, 100): {
        "Bacteria": 45.21, "Fonticulua": 34.90, "Osseus": 6.23, "Electricae": 4.15, "Fungoida": 4.03, "Fumerola": 3.11, "Tussock": 2.34
    },
    (101, 150): {
        "Bacteria": 45.02, "Fonticulua": 19.95, "Tussock": 11.68, "Recepta": 4.78, "Frutexa": 4.04, "Osseus": 3.98, "Fumerola": 3.31, "Electricae": 2.86, "Fungoida": 2.70, "Concha": 1.68
    },
    (151, 200): {
        "Tussock": 20.35, "Bacteria": 14.68, "Stratum": 12.88, "Frutexa": 10.59, "Fungoida": 8.04, "Tubus": 7.99, "Osseus": 7.64, "Concha": 6.19, "Aleoida": 5.01, "Cactoida": 4.85, "Clypeus": 1.25, "Recepta": 0.44, "Fumerola": 0.06, "Fonticulua": 0.02
    },
    (201, 250): {
        "Bacteria": 57.82, "Stratum": 39.14, "Recepta": 2.75, "Fumerola": 0.28
    },
    (251, 300): {
        "Bacteria": 62.21, "Stratum": 36.69, "Recepta": 0.99, "Fumerola": 0.11
    },
    (301, 350): {
        "Bacteria": 74.74, "Stratum": 25.26
    },
    (351, 400): {
        "Bacteria": 71.01, "Stratum": 20.13, "Clypeus": 1.55, "Concha": 1.39, "Fungoida": 1.39, "Tussock": 1.35, "Cactoida": 1.27, "Osseus": 0.95, "Frutexa": 0.94
    },
    (401, 450): {
        "Clypeus": 15.20, "Bacteria": 13.54, "Concha": 13.45, "Fungoida": 12.71, "Cactoida": 12.16, "Tussock": 11.41, "Osseus": 9.89, "Frutexa": 6.46, "Stratum": 5.09, "Fumerola": 0.09
    },
    (451, 500): {
        "Bacteria": 86.54, "Clypeus": 3.48, "Concha": 3.48, "Fungoida": 2.72, "Osseus": 2.42, "Frutexa": 1.21, "Fumerola": 0.15
    },
    (501, 550): { "Bacteria": 100.00 },
    (551, 600): { "Bacteria": 100.00 },
    (601, 650): { "Bacteria": 100.00 }
}

def calculate_species_probability_score(sp_rule: dict, body_data: dict) -> float:
    """
    Calculates comprehensive occurrence probability weight based on Canonn population percentage,
    planetary body type distribution, atmosphere type distribution, temperature centrality,
    and Canonn Temperature Band Genus distribution matrix.
    """
    # 1. Base Species population percentage (e.g. "28.91%" -> 28.91)
    pop_str = sp_rule.get("population_pct", "")
    pop_score = 1.0
    if pop_str and "%" in pop_str:
        try:
            pop_score = float(pop_str.replace("%", "").strip())
        except ValueError:
            pop_score = 1.0

    # 2. Planetary body type specific population ratio (e.g. "High Metal Content (6%) or Rocky (94%)")
    planet_class = (body_data.get("planet_class") or body_data.get("PlanetClass") or "").lower()
    body_type_raw = sp_rule.get("body_type_raw", "")
    body_multiplier = 1.0
    if body_type_raw and planet_class:
        for part in re.split(r"or|/|,", body_type_raw):
            part_lower = part.lower()
            p_match = re.search(r"\((\d+)\s*%\)", part)
            pct_val = float(p_match.group(1)) / 100.0 if p_match else 1.0

            if "rocky ice" in part_lower and "rocky ice" in planet_class:
                body_multiplier = pct_val
                break
            elif "high metal" in part_lower and ("high metal" in planet_class or "hmc" in planet_class):
                body_multiplier = pct_val
                break
            elif "rocky" in part_lower and "rocky" in planet_class and "rocky ice" not in planet_class:
                body_multiplier = pct_val
                break
            elif "ice" in part_lower and "icy" in planet_class and "rocky ice" not in planet_class:
                body_multiplier = pct_val
                break

    # 3. Atmosphere specific population ratio (e.g. "Carbon Dioxide (93%) or Sulphur Dioxide (7%)")
    atmo_str = (body_data.get("atmosphere") or body_data.get("Atmosphere") or body_data.get("atmosphere_type") or "").lower()
    atmo_raw = sp_rule.get("atmosphere_raw", "")
    atmo_multiplier = 1.0
    if atmo_raw and atmo_str:
        for part in re.split(r"or|/|,", atmo_raw):
            part_lower = part.lower()
            p_match = re.search(r"\((\d+)\s*%\)", part)
            pct_val = float(p_match.group(1)) / 100.0 if p_match else 1.0
            clean_part = re.sub(r"\(.*?\)", "", part_lower).strip()

            if clean_part and (clean_part in atmo_str or (clean_part == "carbon dioxide" and "co2" in atmo_str) or (clean_part == "sulphur dioxide" and "so2" in atmo_str)):
                atmo_multiplier = pct_val
                break

    # 4. Temperature Band & Centrality Multiplier
    temp = float(body_data.get("surface_temperature") or body_data.get("SurfaceTemperature") or 0.0)
    genus = sp_rule.get("genus", "")
    temp_band_multiplier = 1.0

    if temp > 0 and genus:
        # Match temperature band
        matched_band = None
        for (b_min, b_max) in TEMP_BAND_TOTAL_POPULATION_SHARE.keys():
            if b_min <= temp <= b_max:
                matched_band = (b_min, b_max)
                break

        if matched_band:
            band_shares = TEMP_BAND_TOTAL_POPULATION_SHARE.get(matched_band, {})
            # Look up genus share in this temperature band
            g_share = band_shares.get(genus) or band_shares.get(genus.capitalize())
            if g_share is not None:
                # Normalize share to a healthy multiplier (e.g. 20% -> 2.0, 5% -> 0.8)
                temp_band_multiplier = max(0.1, (g_share / 10.0))
            else:
                # Check genus distribution matrix
                g_dists = GENUS_TEMP_BAND_DISTRIBUTION.get(genus, {})
                if matched_band in g_dists:
                    temp_band_multiplier = max(0.1, g_dists[matched_band] / 50.0)
                else:
                    temp_band_multiplier = 0.05

    t_data = sp_rule.get("temperature", {})
    t_factor = 1.0
    if t_data and temp > 0:
        center_t = t_data.get("mode") or t_data.get("avg")
        t_min = t_data.get("min")
        t_max = t_data.get("max")
        if center_t and t_min and t_max and (t_max > t_min):
            span = max(1.0, (t_max - t_min) / 2.0)
            diff = abs(temp - center_t)
            t_factor = max(0.6, 1.0 - 0.4 * (diff / span))

    return pop_score * body_multiplier * atmo_multiplier * temp_band_multiplier * t_factor


def predict_exobiology_candidates(body_data: dict) -> list:
    """
    Predicts candidate exobiology species and variants using Canonn Research
    & BioInsights high-precision rule formulas.
    When DSS confirmed genuses (from SAASignalsFound) are present, strictly limits
    predictions to those confirmed genera, selecting the single highest-probability
    subspecies for each.
    """
    if not body_data:
        return []

    atmosphere = (body_data.get("atmosphere") or body_data.get("Atmosphere") or "").lower()
    bio_signals = body_data.get("bio_signals") or body_data.get("BioSignals") or 0
    confirmed_genuses_raw = body_data.get("confirmed_genuses") or body_data.get("genuses")

    if not confirmed_genuses_raw and bio_signals == 0 and ("no atmosphere" in atmosphere or not atmosphere):
        return []
    target_genuses = set()
    if confirmed_genuses_raw:
        if isinstance(confirmed_genuses_raw, str):
            try:
                parsed = json.loads(confirmed_genuses_raw)
                if isinstance(parsed, list):
                    confirmed_genuses_raw = parsed
            except Exception:
                confirmed_genuses_raw = [confirmed_genuses_raw]

        if isinstance(confirmed_genuses_raw, list):
            for item in confirmed_genuses_raw:
                g_str = item.get("Genus_Localised") or item.get("Genus") if isinstance(item, dict) else str(item)
                if g_str:
                    clean_g = re.sub(r"^\$Codex_Ent_|_Genus_Name;?$", "", g_str, flags=re.IGNORECASE).strip().lower()
                    target_genuses.add(clean_g)

    def is_genus_matched(g_name: str) -> bool:
        if not target_genuses:
            return True
        g_l = g_name.lower().strip()
        g_prefix = g_l[:4] if len(g_l) >= 4 else g_l
        for tg in target_genuses:
            tg_l = tg.lower().strip()
            tg_prefix = tg_l[:4] if len(tg_l) >= 4 else tg_l
            if g_prefix == tg_prefix or tg_l in g_l or g_l in tg_l:
                return True
        return False

    # Map genus -> candidates (or list of all matching species)
    genus_candidates: Dict[str, dict] = {}

    # Use Canonn Research Rules (90 species) if available
    if CANONN_SPECIES_RULES:
        for species_name, sp_rule in CANONN_SPECIES_RULES.items():
            genus = sp_rule.get("genus", "")

            # If DSS confirmed genera are present, strictly filter to those genera
            if target_genuses and not is_genus_matched(genus):
                continue

            if match_canonn_species_conditions(species_name, sp_rule, body_data):
                base_val = sp_rule.get("base_value", 1000000)
                colony_dist = sp_rule.get("colony_distance_m", 500)
                desc = sp_rule.get("description", "")
                color_variant = determine_canonn_variant_color(sp_rule, body_data)
                prob_score = calculate_species_probability_score(sp_rule, body_data)

                variant_display = f"{species_name} - {color_variant}" if color_variant and color_variant != "Standard" else species_name

                candidate = {
                    "species": species_name,
                    "species_variant": variant_display,
                    "genus": genus,
                    "base_value": base_val,
                    "first_discovery_value": base_val * 5,
                    "colony_distance_m": colony_dist,
                    "description": desc,
                    "variant_color": color_variant,
                    "population_pct": sp_rule.get("population_pct", ""),
                    "probability_score": prob_score
                }

                # Select the highest-probability representative subspecies for this genus
                if genus not in genus_candidates or prob_score > genus_candidates[genus]["probability_score"]:
                    genus_candidates[genus] = candidate
    else:
        # Fallback to BioInsights Codex Rules
        for species_name, sp_rule in BIOINSIGHTS_SPECIES_RULES.items():
            if match_species_conditions(species_name, sp_rule, body_data):
                genus = sp_rule.get("genus", "")
                base_val = sp_rule.get("base_value", 1000000)
                colony_dist = sp_rule.get("colony_distance_m", 500)
                desc = sp_rule.get("description", "")
                color_variant = determine_variant_color(sp_rule, body_data)

                variant_display = f"{species_name} - {color_variant}" if color_variant and color_variant != "Standard" else species_name

                candidate = {
                    "species": species_name,
                    "species_variant": variant_display,
                    "genus": genus,
                    "base_value": base_val,
                    "first_discovery_value": base_val * 5,
                    "colony_distance_m": colony_dist,
                    "description": desc,
                    "variant_color": color_variant,
                    "probability_score": 1.0
                }

                if genus not in genus_candidates or base_val > genus_candidates[genus]["base_value"]:
                    genus_candidates[genus] = candidate

    matched_candidates = list(genus_candidates.values())

    # Sort candidates strictly from highest payout value to lowest
    matched_candidates.sort(key=lambda x: (x.get("base_value", 0), x.get("probability_score", 0)), reverse=True)

    # Fallback if bio_signals > 0 and no match
    if bio_signals > 0 and len(matched_candidates) == 0:
        planet_class = (body_data.get("planet_class") or "").lower()
        if "icy" in planet_class:
            matched_candidates.append({
                "species": "Fonticulua Campestris",
                "species_variant": "Fonticulua Campestris",
                "genus": "Fonticulua",
                "base_value": 1000000,
                "first_discovery_value": 5000000,
                "colony_distance_m": 500,
                "description": "General icy flora",
                "variant_color": ""
            })
        else:
            matched_candidates.append({
                "species": "Bacterium Aurasus",
                "species_variant": "Bacterium Aurasus",
                "genus": "Bacterium",
                "base_value": 1000000,
                "first_discovery_value": 5000000,
                "colony_distance_m": 500,
                "description": "Microbial colony",
                "variant_color": ""
            })

    return matched_candidates


def get_species_value(species_name: str = "", genus_name: str = "") -> dict:
    """
    Returns dict containing base_value, first_discovery_value, colony_distance_m
    for a given species or genus name.
    """
    clean_name = (species_name or "").split(" - ")[0].strip()
    clean_genus = (genus_name or "").strip()

    if CANONN_SPECIES_RULES and clean_name in CANONN_SPECIES_RULES:
        rule = CANONN_SPECIES_RULES[clean_name]
        base_val = rule.get("base_value", 1000000)
        colony_dist = rule.get("colony_distance_m", 500)
        return {
            "base_value": base_val,
            "first_discovery_value": base_val * 5,
            "colony_distance_m": colony_dist
        }

    if clean_name in BIOINSIGHTS_SPECIES_RULES:
        rule = BIOINSIGHTS_SPECIES_RULES[clean_name]
        base_val = rule["base_value"]
        colony_dist = rule.get("colony_distance_m", 500)
        return {
            "base_value": base_val,
            "first_discovery_value": base_val * 5,
            "colony_distance_m": colony_dist
        }

    for genus, def_val in GENUS_DEFAULT_VALUES.items():
        if clean_name.lower().startswith(genus.lower()) or (clean_genus and clean_genus.lower() == genus.lower()):
            dist = GENUS_DEFAULT_DISTANCE.get(genus, 500)
            return {
                "base_value": def_val,
                "first_discovery_value": def_val * 5,
                "colony_distance_m": dist
            }

    return {
        "base_value": 1000000,
        "first_discovery_value": 5000000,
        "colony_distance_m": 500
    }

