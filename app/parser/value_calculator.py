import math

# Star base values
STAR_VALUES = {
    "O": 4110,
    "B": 3400,
    "A": 2900,
    "F": 2800,
    "G": 2700,
    "K": 2600,
    "M": 2500,
    "L": 2400,
    "T": 2300,
    "Y": 2200,
    "TTS": 2400,
    "AeBe": 3500,
    "W": 5000,
    "WN": 5000,
    "WNC": 5000,
    "WC": 5000,
    "WO": 5000,
    "CS": 3000,
    "C": 3000,
    "CN": 3000,
    "CJ": 3000,
    "CH": 3000,
    "CHd": 3000,
    "MS": 3000,
    "S": 3000,
    "D": 14057,
    "DA": 14057,
    "DAB": 14057,
    "DAO": 14057,
    "DAZ": 14057,
    "DAV": 14057,
    "DB": 14057,
    "DBZ": 14057,
    "DBV": 14057,
    "DO": 14057,
    "DOV": 14057,
    "DQ": 14057,
    "DC": 14057,
    "DCV": 14057,
    "DX": 14057,
    "N": 22628,
    "H": 22628,
    "SupermassiveBlackHole": 33.5678,
    "X": 2500,
    "A_BlueWhiteSuperGiant": 4000,
    "F_WhiteSuperGiant": 4000,
    "M_RedSuperGiant": 4000,
    "M_RedGiant": 3500,
    "K_OrangeGiant": 3500,
    "B_BlueWhiteSuperGiant": 4000,
    "G_WhiteSuperGiant": 4000,
}

# Planet base value constants
PLANET_K = {
    "Metal rich body": 21790,
    "High metal content world": 9654,
    "High metal content body": 9654,
    "Earthlike body": 64831,
    "Earth-like world": 64831,
    "Water world": 64831,
    "Ammonia world": 96932,
    "Sudarsky class I gas giant": 1656,
    "Sudarsky class II gas giant": 9654,
    "Sudarsky class III gas giant": 965,
    "Sudarsky class IV gas giant": 1110,
    "Sudarsky class V gas giant": 722,
    "Gas giant with water based life": 883,
    "Gas giant with ammonia based life": 816,
    "Helium rich gas giant": 900,
    "Helium gas giant": 900,
    "Water giant": 900,
    "Rocky body": 300,
    "Rocky ice body": 300,
    "Rocky ice world": 300,
    "Icy body": 300,
}

PLANET_TF_K = {
    "Metal rich body": 65631,
    "High metal content world": 100677,
    "High metal content body": 100677,
    "Earthlike body": 116295,
    "Earth-like world": 116295,
    "Water world": 116295,
    "Rocky body": 93328,
}

def calculate_star_value(star_type: str, stellar_mass: float) -> dict:
    """Calculate FSS scan value for a star."""
    k = STAR_VALUES.get(star_type, 1200)
    # Frontier formula for stars
    base_val = max(1200, int(k + (stellar_mass * k / 66.25)))
    first_discovery_val = int(base_val * 2.6)
    
    return {
        "fss_value": base_val,
        "dss_value": 0,
        "first_discovered_fss": first_discovery_val,
        "first_mapped_dss": 0,
        "max_potential_value": first_discovery_val
    }

def calculate_planet_value(
    planet_class: str,
    mass_em: float,
    terraformable: bool = False,
    is_odyssey: bool = True
) -> dict:
    """
    Calculate FSS, DSS, and first discovery/mapped bonuses for a planet/moon.
    Formulas based on Frontier ED 3.3+ Exploration payout specifications.
    """
    p_class = planet_class or ""
    # Normalize class string
    norm_class = None
    for k in PLANET_K.keys():
        if k.lower() == p_class.lower() or k.lower() in p_class.lower():
            norm_class = k
            break
    
    if not norm_class:
        norm_class = "Icy body"
        
    k = PLANET_K.get(norm_class, 300)
    k_tf = PLANET_TF_K.get(norm_class, 0) if terraformable else 0
    
    # Base calculation
    q = 0.56591828
    m = max(0.00001, mass_em if mass_em is not None else 0.001)
    
    # Base value for FSS
    base_val = max(500, int(k + (k * q * (m ** 0.2))))
    if terraformable and k_tf > 0:
        base_val += int(k_tf + (k_tf * q * (m ** 0.2)))
        
    # DSS Mapping value (standard without efficiency bonus)
    # Mapping multiplier formula
    dss_val = max(int(base_val * 3.3333333333), 8333)
    if terraformable and k_tf > 0:
        dss_val = int(dss_val * 1.0)
    
    # Efficiency bonus multiplier (1.25x)
    dss_efficient = int(dss_val * 1.25)
    
    # First discovery / First mapped multipliers
    # First Discovered: FSS * 2.6
    first_discovered_fss = int(base_val * 2.6)
    
    # First Mapped bonus: (DSS base + FD bonus)
    first_mapped_dss = int(dss_efficient * 3.699622554)
    
    # Total if First to Discover AND First to Map (with efficiency)
    max_potential = first_discovered_fss + first_mapped_dss
    
    return {
        "fss_value": base_val,
        "dss_value": dss_efficient,
        "first_discovered_fss": first_discovered_fss,
        "first_mapped_dss": first_mapped_dss,
        "max_potential_value": max_potential,
        "is_terraformable": terraformable
    }

def calculate_body_value(body: dict) -> dict:
    """Dispatcher for celestial body value calculation."""
    if body.get("star_type"):
        return calculate_star_value(
            body.get("star_type"),
            body.get("stellar_mass", 1.0) or 1.0
        )
    else:
        tf_state = body.get("terraforming_state") or ""
        is_tf = "terraformable" in tf_state.lower() or "candidate for terraforming" in tf_state.lower()
        if "earthlike" in (body.get("planet_class") or "").lower():
            is_tf = True
        return calculate_planet_value(
            body.get("planet_class", ""),
            body.get("mass_em", 1.0) or 1.0,
            terraformable=is_tf
        )
