"""
Elite Dangerous Odyssey Exobiology Database & Prediction Engine.
Contains updated payout tables (post-Update 14) and atmosphere/temperature conditions
for determining potential botanical/fungal species and their sample values.
"""

EXOBIOLOGY_SPECIES_DB = {
    # Stratum
    "Stratum Tectonicas": {"genus": "Stratum", "value": 19010800, "colony_distance": 500, "description": "High metal content/Rocky, CO2/SO2/Water/Nitrogen atmosphere, high value!"},
    "Stratum Cucumisis": {"genus": "Stratum", "value": 19010800, "colony_distance": 500, "description": "CO2/SO2/Water atmosphere on HMC/Rocky"},
    "Stratum Laminaris": {"genus": "Stratum", "value": 2754200, "colony_distance": 500, "description": "CO2 atmosphere, flat rocky plains"},
    "Stratum Paleas": {"genus": "Stratum", "value": 1638900, "colony_distance": 500, "description": "CO2/SO2 atmosphere, wide distribution"},
    "Stratum Limax": {"genus": "Stratum", "value": 1638900, "colony_distance": 500, "description": "SO2/CO2 atmosphere"},
    "Stratum Frigus": {"genus": "Stratum", "value": 2637500, "colony_distance": 500, "description": "Cold CO2/SO2 icy/rocky atmosphere"},
    "Stratum Excutitus": {"genus": "Stratum", "value": 2416200, "colony_distance": 500, "description": "Rocky body with thin CO2"},
    "Stratum Araneamus": {"genus": "Stratum", "value": 2416200, "colony_distance": 500, "description": "Spider-like stratum on rocky bodies"},

    # Bacterium
    "Bacterium Informache": {"genus": "Bacterium", "value": 8405000, "colony_distance": 500, "description": "Neon/Argon atmosphere, high value microbe"},
    "Bacterium Volu": {"genus": "Bacterium", "value": 7816500, "colony_distance": 500, "description": "Methane/Nitrogen atmosphere"},
    "Bacterium Scopulum": {"genus": "Bacterium", "value": 4941800, "colony_distance": 500, "description": "Water/Ammonia atmosphere rocky terrain"},
    "Bacterium Omentum": {"genus": "Bacterium", "value": 4772000, "colony_distance": 500, "description": "CO2/Methane atmosphere"},
    "Bacterium Alcyoneum": {"genus": "Bacterium", "value": 1689700, "colony_distance": 500, "description": "Ammonia/Nitrogen atmosphere"},
    "Bacterium Cerbrus": {"genus": "Bacterium", "value": 1689700, "colony_distance": 500, "description": "SO2 atmosphere"},
    "Bacterium Vesicula": {"genus": "Bacterium", "value": 1600000, "colony_distance": 500, "description": "Rocky icy bodies, Nitrogen atmosphere"},
    "Bacterium Acisa": {"genus": "Bacterium", "value": 1000000, "colony_distance": 500, "description": "Widespread thin atmosphere"},
    "Bacterium Aurasus": {"genus": "Bacterium", "value": 1000000, "colony_distance": 500, "description": "Common microbial mats"},
    "Bacterium Bullaris": {"genus": "Bacterium", "value": 1176500, "colony_distance": 500, "description": "Thin CO2/Water atmosphere"},

    # Clypeus
    "Clypeus Speculbi": {"genus": "Clypeus", "value": 16396400, "colony_distance": 150, "description": "Hydrocarbon/Methane rich thin atmosphere"},
    "Clypeus Margaritus": {"genus": "Clypeus", "value": 11848500, "colony_distance": 150, "description": "Water rich/Ammonia atmosphere"},
    "Clypeus Lacrimata": {"genus": "Clypeus", "value": 8405000, "colony_distance": 150, "description": "CO2 atmosphere shield fungi"},

    # Concha
    "Concha Biconvexa": {"genus": "Concha", "value": 19010800, "colony_distance": 150, "description": "Nitrogen atmosphere, high value concha"},
    "Concha Aureolas": {"genus": "Concha", "value": 7816500, "colony_distance": 150, "description": "Ammonia/Water atmosphere"},
    "Concha Renibus": {"genus": "Concha", "value": 4473000, "colony_distance": 150, "description": "CO2 atmosphere rocky canyon floors"},
    "Concha Labiata": {"genus": "Concha", "value": 2416200, "colony_distance": 150, "description": "Thin atmosphere valley formations"},

    # Tubus
    "Tubus Cavas": {"genus": "Tubus", "value": 11848500, "colony_distance": 800, "description": "Methane/Nitrogen atmosphere tubular growth"},
    "Tubus Compagibus": {"genus": "Tubus", "value": 7816500, "colony_distance": 800, "description": "Ammonia/Water thin atmosphere"},
    "Tubus Sororibus": {"genus": "Tubus", "value": 5861500, "colony_distance": 800, "description": "CO2 atmosphere highlands"},
    "Tubus Rosarium": {"genus": "Tubus", "value": 2637500, "colony_distance": 800, "description": "SO2 atmosphere"},
    "Tubus Conifer": {"genus": "Tubus", "value": 2416200, "colony_distance": 800, "description": "Rocky/Icy thin atmosphere"},

    # Recepta
    "Recepta Umbrux": {"genus": "Recepta", "value": 16396400, "colony_distance": 150, "description": "SO2 atmosphere, deep valleys"},
    "Recepta Deltahedron": {"genus": "Recepta", "value": 13000000, "colony_distance": 150, "description": "CO2/Nitrogen atmosphere"},
    "Recepta Condensata": {"genus": "Recepta", "value": 7816500, "colony_distance": 150, "description": "Water/Ammonia atmosphere"},

    # Osseus
    "Osseus Pumice": {"genus": "Osseus", "value": 13000000, "colony_distance": 800, "description": "Methane/CO2 atmosphere, bone-like formations"},
    "Osseus Discus": {"genus": "Osseus", "value": 11848500, "colony_distance": 800, "description": "Nitrogen/Argon atmosphere"},
    "Osseus Fractus": {"genus": "Osseus", "value": 4000000, "colony_distance": 800, "description": "Rocky bodies with volcanism"},
    "Osseus Spiralis": {"genus": "Osseus", "value": 2416200, "colony_distance": 800, "description": "SO2/CO2 atmosphere ridges"},
    "Osseus Pelleas": {"genus": "Osseus", "value": 1773600, "colony_distance": 800, "description": "Thin atmosphere crags"},

    # Fonticula
    "Fonticula Fluctus": {"genus": "Fonticula", "value": 19010800, "colony_distance": 500, "description": "Icy/Rocky icy body with Methane/CO2, geyser vents"},
    "Fonticula Lapida": {"genus": "Fonticula", "value": 3141600, "colony_distance": 500, "description": "SO2/Argon icy bodies"},
    "Fonticula Campestris": {"genus": "Fonticula", "value": 1000000, "colony_distance": 500, "description": "Common fonticula on icy worlds"},

    # Frutexa
    "Frutexa Flammas": {"genus": "Frutexa", "value": 10329800, "colony_distance": 150, "description": "CO2 atmosphere shrubs in low valleys"},
    "Frutexa Acies": {"genus": "Frutexa", "value": 7816500, "colony_distance": 150, "description": "Ammonia/Water atmosphere shrubland"},
    "Frutexa Fimbriata": {"genus": "Frutexa", "value": 7816500, "colony_distance": 150, "description": "Nitrogen atmosphere rocky terrain"},
    "Frutexa Metallic": {"genus": "Frutexa", "value": 1638900, "colony_distance": 150, "description": "Metal-rich plains with thin atmosphere"},

    # Aleoida
    "Aleoida Gravis": {"genus": "Aleoida", "value": 12934700, "colony_distance": 150, "description": "Methane/CO2 atmosphere heavy succulents"},
    "Aleoida Araneae": {"genus": "Aleoida", "value": 7816500, "colony_distance": 150, "description": "SO2/Ammonia atmosphere"},
    "Aleoida Coronamus": {"genus": "Aleoida", "value": 6284400, "colony_distance": 150, "description": "CO2 atmosphere rocky mountains"},
    "Aleoida Spica": {"genus": "Aleoida", "value": 3375000, "colony_distance": 150, "description": "Spiky flora on rocky bodies"},

    # Tussock
    "Tussock Pennata": {"genus": "Tussock", "value": 5861500, "colony_distance": 200, "description": "Nitrogen atmosphere grass tufts"},
    "Tussock Caputus": {"genus": "Tussock", "value": 3845900, "colony_distance": 200, "description": "Methane/Ammonia plains"},
    "Tussock Albatus": {"genus": "Tussock", "value": 3845900, "colony_distance": 200, "description": "Cold CO2/SO2 icy plains"},
    "Tussock Divisa": {"genus": "Tussock", "value": 1773600, "colony_distance": 200, "description": "CO2 atmosphere grassy valleys"},
    "Tussock Cultrum": {"genus": "Tussock", "value": 1773600, "colony_distance": 200, "description": "Thin CO2 rocky plains"},
    "Tussock Viridans": {"genus": "Tussock", "value": 1638900, "colony_distance": 200, "description": "Common green tussock"},
    "Tussock Propinquus": {"genus": "Tussock", "value": 1000000, "colony_distance": 200, "description": "Low value widespread tussock"},

    # Electricae
    "Electricae Pluma": {"genus": "Electricae", "value": 6284400, "colony_distance": 1000, "description": "Airless or ultra-thin atmosphere glowing bio-electric flora"},
    "Electricae Radial": {"genus": "Electricae", "value": 6284400, "colony_distance": 1000, "description": "Extreme radiation/magnetic fields"},
}

GENUS_DEFAULT_VALUES = {
    "Stratum": 19010800,
    "Clypeus": 11848500,
    "Concha": 7816500,
    "Recepta": 13000000,
    "Tubus": 5861500,
    "Aleoida": 7816500,
    "Frutexa": 7816500,
    "Osseus": 4000000,
    "Fonticula": 3141600,
    "Tussock": 2500000,
    "Bacterium": 1689700,
    "Electricae": 6284400,
    "Fungoida": 3600000,
    "Cactoida": 3600000,
    "Brain Tree": 1500000,
    "Anemone": 1500000,
    "Sinuous Tuber": 1500000,
}

FIRST_DISCOVERY_MULTIPLIER = 5.0  # 5x payout for First Vista Genomics Discovery

def predict_exobiology_candidates(body_data: dict) -> list:
    """
    Predict potential exobiology species based on body characteristics:
    - PlanetClass (High metal content, Rocky body, Icy body, Rocky ice)
    - Atmosphere (Carbon dioxide, Sulphur dioxide, Methane, Ammonia, Nitrogen, Argon, Water, Oxygen, etc.)
    - SurfaceTemperature (Kelvin)
    - SurfaceGravity (m/s^2 or G)
    - Landable flag
    """
    if not body_data.get("landable"):
        return []
        
    atmosphere = (body_data.get("atmosphere") or "").lower()
    planet_class = (body_data.get("planet_class") or "").lower()
    temp = body_data.get("surface_temperature") or 200.0
    gravity = body_data.get("surface_gravity_g") or (body_data.get("surface_gravity", 9.81) / 9.81 if body_data.get("surface_gravity") else 1.0)
    volcanism = (body_data.get("volcanism") or "").lower()
    bio_signals = body_data.get("bio_signals", 0)

    # If no bio signals and not predicted to have atmosphere, return empty
    if bio_signals == 0 and ("no atmosphere" in atmosphere or not atmosphere):
        return []

    candidates = []

    # 1. Stratum rules (Very high payout)
    if "high metal" in planet_class or "rocky" in planet_class:
        if any(atm in atmosphere for atm in ["carbon dioxide", "sulphur dioxide", "water", "nitrogen"]):
            if 150 <= temp <= 350:
                candidates.append("Stratum Tectonicas")
            elif temp < 180:
                candidates.append("Stratum Frigus")
            else:
                candidates.append("Stratum Cucumisis")
                candidates.append("Stratum Laminaris")

    # 2. Clypeus / Concha rules
    if any(atm in atmosphere for atm in ["methane", "nitrogen", "water", "ammonia", "carbon dioxide"]):
        if 130 <= temp <= 270:
            if "methane" in atmosphere or "hydrocarbon" in atmosphere:
                candidates.append("Clypeus Speculbi")
            if "nitrogen" in atmosphere:
                candidates.append("Concha Biconvexa")
            if "ammonia" in atmosphere:
                candidates.append("Concha Aureolas")

    # 3. Tubus / Recepta rules
    if "methane" in atmosphere or "nitrogen" in atmosphere or "sulphur dioxide" in atmosphere:
        if "sulphur" in atmosphere:
            candidates.append("Recepta Umbrux")
        if "methane" in atmosphere:
            candidates.append("Tubus Cavas")
        if "nitrogen" in atmosphere:
            candidates.append("Recepta Deltahedron")

    # 4. Fonticula (Icy / Rocky-Icy)
    if "icy" in planet_class:
        if "methane" in atmosphere or "carbon dioxide" in atmosphere:
            candidates.append("Fonticula Fluctus")
        elif "sulphur" in atmosphere or "argon" in atmosphere:
            candidates.append("Fonticula Lapida")
        else:
            candidates.append("Fonticula Campestris")

    # 5. Frutexa / Aleoida / Tussock
    if "carbon dioxide" in atmosphere or "ammonia" in atmosphere or "nitrogen" in atmosphere:
        if temp >= 200:
            candidates.append("Frutexa Flammas")
            candidates.append("Aleoida Gravis")
        if temp < 250:
            candidates.append("Tussock Albatus")
            candidates.append("Tussock Pennata")

    # 6. Osseus
    if volcanism != "none" and volcanism != "" or "methane" in atmosphere:
        candidates.append("Osseus Pumice")
        candidates.append("Osseus Fractus")

    # 7. Bacterium (Ubiquitous on almost all thin atmosphere worlds)
    if "neon" in atmosphere or "argon" in atmosphere:
        candidates.append("Bacterium Informache")
    elif "methane" in atmosphere:
        candidates.append("Bacterium Volu")
    elif "water" in atmosphere or "ammonia" in atmosphere:
        candidates.append("Bacterium Scopulum")
    elif "carbon dioxide" in atmosphere:
        candidates.append("Bacterium Omentum")
    elif "sulphur" in atmosphere:
        candidates.append("Bacterium Cerbrus")
    else:
        candidates.append("Bacterium Aurasus")

    # Deduplicate while preserving order
    seen = set()
    result = []
    for item in candidates:
        if item not in seen and item in EXOBIOLOGY_SPECIES_DB:
            seen.add(item)
            info = EXOBIOLOGY_SPECIES_DB[item]
            result.append({
                "species": item,
                "genus": info["genus"],
                "base_value": info["value"],
                "first_discovery_value": int(info["value"] * FIRST_DISCOVERY_MULTIPLIER),
                "colony_distance_m": info["colony_distance"],
                "description": info["description"]
            })

    # Sort candidates by value descending
    result.sort(key=lambda x: x["base_value"], reverse=True)

    # If bio_signals is known (e.g. 3), tag top N as most probable
    if bio_signals > 0:
        return result[:max(bio_signals, 3)]
    return result

def get_species_value(species_name: str, genus_name: str = "") -> dict:
    """Lookup exact or genus-based value for scanned organic."""
    if species_name in EXOBIOLOGY_SPECIES_DB:
        val = EXOBIOLOGY_SPECIES_DB[species_name]["value"]
        genus = EXOBIOLOGY_SPECIES_DB[species_name]["genus"]
    elif genus_name and genus_name in GENUS_DEFAULT_VALUES:
        val = GENUS_DEFAULT_VALUES[genus_name]
        genus = genus_name
    else:
        val = 1000000
        genus = genus_name or "Unknown"

    return {
        "species": species_name,
        "genus": genus,
        "base_value": val,
        "first_discovery_value": int(val * FIRST_DISCOVERY_MULTIPLIER)
    }
