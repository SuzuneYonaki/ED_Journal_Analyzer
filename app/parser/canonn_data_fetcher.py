# app/parser/canonn_data_fetcher.py
"""Parser and builder for Canonn Research Exobiology data.
Parses all raw text files from the `species` folder and combines them with
Stellar Class / Material variant color charts and environmental constraints
into `canonn_rules.json`.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SPECIES_DIR = Path(__file__).resolve().parents[2] / "species"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "canonn_rules.json"

# Stellar class variant mapping (Genus -> { StellarClass -> VariantColor })
STELLAR_CLASS_VARIANTS = {
    "Aleoida": {"B": "Yellow", "A": "Green", "F": "Teal", "K": "Turquoise", "M": "Emerald", "L": "Lime", "T": "Sage", "TTS": "Mauve", "Y": "Amethyst", "W": "Grey", "D": "Indigo", "N": "Ocher"},
    "Bacteria": {"O": "Turquoise", "B": "Grey", "A": "Yellow", "F": "Lime", "G": "Emerald", "K": "Green", "M": "Teal", "L": "Sage", "T": "Red", "TTS": "Maroon", "Ae": "Orange", "Y": "Mauve", "W": "Amethyst", "D": "Ocher", "N": "Indigo"},
    "Cactoida": {"O": "Grey", "A": "Green", "F": "Yellow", "G": "Teal", "M": "Amethyst", "L": "Mauve", "T": "Orange", "TTS": "Red", "Y": "Ocher", "W": "Indigo", "D": "Turquoise", "N": "Sage"},
    "Clypeus": {"B": "Maroon", "A": "Orange", "F": "Mauve", "G": "Amethyst", "K": "Grey", "M": "Turquoise", "L": "Teal", "Y": "Green", "D": "Lime", "N": "Yellow"},
    "Concha": {"B": "Indigo", "A": "Teal", "F": "Grey", "G": "Turquoise", "K": "Red", "M": "Orange", "Y": "Yellow", "W": "Lime", "D": "Green", "N": "Emerald"},
    "Fonticulua": {"O": "Grey", "B": "Lime", "A": "Green", "F": "Yellow", "G": "Teal", "K": "Emerald", "M": "Amethyst", "L": "Mauve", "T": "Orange", "TTS": "Red", "Ae": "Maroon", "Y": "Ocher", "W": "Indigo", "D": "Turquoise", "N": "Sage"},
    "Frutexa": {"O": "Yellow", "B": "Lime", "F": "Green", "G": "Emerald", "M": "Grey", "L": "Teal", "TTS": "Mauve", "Y": "Orange", "W": "Indigo", "D": "Red"},
    "Osseus": {"O": "Yellow", "A": "Lime", "F": "Turquoise", "G": "Grey", "K": "Indigo", "T": "Emerald", "TTS": "Green", "Y": "Maroon"},
    "Recepta": {"O": "Indigo", "B": "Turquoise", "A": "Amethyst", "F": "Mauve", "G": "Orange", "K": "Red", "M": "Maroon", "L": "Ocher", "T": "Teal", "TTS": "Sage", "Ae": "Grey", "Y": "Lime", "D": "Yellow", "N": "Emerald"},
    "Stratum": {"F": "Emerald", "K": "Lime", "M": "Green", "L": "Turquoise", "T": "Grey", "TTS": "Amethyst", "Ae": "Teal", "Y": "Indigo", "W": "Red", "D": "Mauve"},
    "Tubus": {"O": "Green", "B": "Emerald", "A": "Indigo", "F": "Grey", "G": "Red", "K": "Maroon", "M": "Teal", "L": "Turquoise", "T": "Mauve", "TTS": "Ocher", "W": "Lime", "D": "Yellow", "N": "Amethyst"},
    "Tussock": {"G": "Yellow", "K": "Lime", "M": "Green", "L": "Emerald", "T": "Sage", "TTS": "Teal", "Y": "Red", "W": "Orange", "D": "Maroon"},
}

# Material variant mapping (Species -> { Material -> Color })
MATERIAL_VARIANTS = {
    "Bacterium Acies": {"Antimony": "Cyan", "Polonium": "Magenta", "Ruthenium": "Cobalt", "Technetium": "Lime", "Tellurium": "White", "Yttrium": "Aquamarine"},
    "Bacterium Bullaris": {"Antimony": "Cobalt", "Polonium": "Yellow", "Ruthenium": "Aquamarine", "Technetium": "Gold", "Tellurium": "Lime", "Yttrium": "Red"},
    "Bacterium Informem": {"Antimony": "Red", "Polonium": "Lime", "Ruthenium": "Gold", "Technetium": "Aquamarine", "Tellurium": "Yellow", "Yttrium": "Cobalt"},
    "Bacterium Nebulus": {"Antimony": "Magenta", "Polonium": "Gold", "Ruthenium": "Orange", "Technetium": "Cyan", "Tellurium": "Green", "Yttrium": "Cobalt"},
    "Bacterium Omentum": {"Cadmium": "Lime", "Mercury": "White", "Molybdenum": "Aquamarine", "Niobium": "Peach", "Tin": "Red", "Tungsten": "Blue"},
    "Bacterium Scopulum": {"Cadmium": "White", "Mercury": "Peach", "Molybdenum": "Lime", "Niobium": "Red", "Tin": "Mulberry", "Tungsten": "Aquamarine"},
    "Bacterium Tela": {"Cadmium": "Gold", "Mercury": "Orange", "Molybdenum": "Yellow", "Niobium": "Magenta", "Tin": "Cobalt", "Tungsten": "Green"},
    "Bacterium Verrata": {"Cadmium": "Peach", "Mercury": "Red", "Molybdenum": "White", "Niobium": "Mulberry", "Tin": "Blue", "Tungsten": "Lime"},
    "Bacterium Vesicula": {"Antimony": "Cyan", "Polonium": "Orange", "Ruthenium": "Mulberry", "Technetium": "Gold", "Tellurium": "Red", "Yttrium": "Lime"},
    "Bacterium Volu": {"Antimony": "Red", "Polonium": "Aquamarine", "Ruthenium": "Cobalt", "Technetium": "Lime", "Tellurium": "Cyan", "Yttrium": "Gold"},
    "Concha Biconcavis": {"Antimony": "Peach", "Polonium": "Red", "Ruthenium": "Orange", "Technetium": "White", "Tellurium": "Yellow", "Yttrium": "Gold"},
    "Concha Renibus": {"Cadmium": "Red", "Mercury": "Mulberry", "Molybdenum": "Peach", "Niobium": "Blue", "Tin": "Aquamarine", "Tungsten": "White"},
    "Electricae Pluma": {"Antimony": "Cobalt", "Polonium": "Cyan", "Ruthenium": "Blue", "Technetium": "Magenta", "Tellurium": "Red", "Yttrium": "Mulberry"},
    "Electricae Radialem": {"Antimony": "Cyan", "Polonium": "Cobalt", "Ruthenium": "Blue", "Technetium": "Aquamarine", "Tellurium": "Magenta", "Yttrium": "Green"},
    "Fumerola Aquatis": {"Cadmium": "Green", "Mercury": "Yellow", "Molybdenum": "Cyan", "Niobium": "Gold", "Tin": "Orange", "Tungsten": "Cobalt"},
    "Fumerola Carbosis": {"Cadmium": "Orange", "Mercury": "Magenta", "Molybdenum": "Gold", "Niobium": "Cobalt", "Tin": "Cyan", "Tungsten": "Yellow"},
    "Fumerola Extremus": {"Cadmium": "Aquamarine", "Mercury": "Lime", "Molybdenum": "Blue", "Niobium": "White", "Tin": "Peach", "Tungsten": "Mulberry"},
    "Fumerola Nitris": {"Cadmium": "White", "Mercury": "Peach", "Molybdenum": "Lime", "Niobium": "Red", "Tin": "Mulberry", "Tungsten": "Aquamarine"},
    "Fungoida Bullarum": {"Antimony": "Red", "Polonium": "Mulberry", "Ruthenium": "Magenta", "Technetium": "Peach", "Tellurium": "Gold", "Yttrium": "Orange"},
    "Fungoida Gelata": {"Cadmium": "Cyan", "Mercury": "Lime", "Molybdenum": "Mulberry", "Niobium": "Green", "Tin": "Red", "Tungsten": "Orange"},
    "Fungoida Setisis": {"Antimony": "Peach", "Polonium": "White", "Ruthenium": "Gold", "Technetium": "Lime", "Tellurium": "Yellow", "Yttrium": "Orange"},
    "Fungoida Stabbitis": {"Cadmium": "Blue", "Mercury": "Green", "Molybdenum": "Magenta", "Niobium": "White", "Tin": "Orange", "Tungsten": "Peach"},
    "Osseus Discus": {"Cadmium": "White", "Mercury": "Lime", "Molybdenum": "Peach", "Niobium": "Aquamarine", "Tin": "Blue", "Tungsten": "Red"},
    "Osseus Pumice": {"Antimony": "White", "Polonium": "Peach", "Ruthenium": "Gold", "Technetium": "Lime", "Tellurium": "Green", "Yttrium": "Yellow"},
    "Recepta Conditivus": {"Antimony": "Lime", "Polonium": "White", "Ruthenium": "Yellow", "Technetium": "Aquamarine", "Tellurium": "Cyan", "Yttrium": "Green"},
    "Recepta Deltahedronix": {"Cadmium": "Lime", "Mercury": "Cyan", "Molybdenum": "Gold", "Niobium": "Mulberry", "Tin": "Orange", "Tungsten": "Red"},
}

def clean_text(val: str) -> str:
    return val.strip().replace("\xa0", " ")

def parse_species_files(directory: Path = SPECIES_DIR) -> Dict[str, Any]:
    all_species: Dict[str, Any] = {}
    txt_files = sorted(list(directory.glob("*.txt")))

    for file_path in txt_files:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        lines = [clean_text(l) for l in content.splitlines()]
        genus_name = lines[0].strip() if lines else file_path.stem.strip()
        # Clean genus name (remove trailing spaces, etc.)
        genus_name = genus_name.split()[0] if genus_name else file_path.stem.strip()

        # Extract Minimum Colonial Separation
        colony_dist_m = 0
        dist_match = re.search(r"Minimum Colonial Separation:\s*(\d+)m?", content, re.IGNORECASE)
        if dist_match:
            colony_dist_m = int(dist_match.group(1))

        # Extract Prices & Population % globally from file
        prices: Dict[str, int] = {}
        pop_pcts: Dict[str, str] = {}
        for m in re.finditer(r"^([A-Z][a-z]+\s+[A-Za-z]+)\s+([0-9.]+%)\s+([0-9, ]+)", content, re.MULTILINE):
            sp_name = m.group(1).strip()
            pop_pcts[sp_name] = m.group(2).strip()
            p_val = m.group(3).replace(",", "").replace(" ", "")
            if p_val.isdigit():
                prices[sp_name] = int(p_val)

        # Split content into individual species blocks
        # A species block starts with a line having "<Genus/SpeciesName> <SpeciesName>"
        # followed nearby by "– <Color>"
        species_blocks = re.split(r"\n(?=[A-Z][a-z]+\s+[A-Za-z]+(?:\s*\n[A-Z][a-z]+\s+[A-Za-z]+\s*–|\s*–))", content)

        for block in species_blocks:
            if "Planetary Body Type:" not in block or "Temperature" not in block:
                continue

            lines_b = [clean_text(l) for l in block.strip().splitlines() if clean_text(l)]
            if not lines_b:
                continue

            # Identify species name
            species_name = ""
            for l in lines_b[:4]:
                m = re.match(r"^([A-Z][a-z]+\s+[A-Za-z]+)(?:\s*–.*)?$", l)
                if m and not l.startswith("Stellar Class") and not l.startswith("Species Name") and not l.startswith("Temperature"):
                    species_name = m.group(1)
                    break

            if not species_name:
                continue

            # Description (between image line and next section)
            desc = ""
            desc_match = re.search(r"Image courtesy of.*?\n\n(.*?)\n\n(?:Material and Variant|Planetary Body Type:)", block, re.DOTALL)
            if desc_match:
                desc = desc_match.group(1).strip().replace("\n", " ")

            # Material and Variant table inside block (if present)
            block_mat_variants: Dict[str, str] = {}
            mat_table_match = re.search(r"Material\s+([A-Za-z\t ]+)\nVariant\s+([A-Za-z\t ]+)", block)
            if mat_table_match:
                mats = [x.strip() for x in re.split(r"\t+|\s{2,}", mat_table_match.group(1)) if x.strip()]
                vars_ = [x.strip() for x in re.split(r"\t+|\s{2,}", mat_table_match.group(2)) if x.strip()]
                for m_name, v_color in zip(mats, vars_):
                    block_mat_variants[m_name] = v_color

            # Planetary Body Type
            body_type_raw = ""
            pbt_match = re.search(r"Planetary Body Type:\s*([^\n]+)", block)
            if pbt_match:
                body_type_raw = pbt_match.group(1).strip()

            # Atmosphere
            atm_raw = ""
            atm_match = re.search(r"Atmosphere:\s*([^\n]+)", block)
            if atm_match:
                atm_raw = atm_match.group(1).strip()

            # Volcanism
            volcanism = ""
            volc_match = re.search(r"Volcanism:\s*([^\n]+)", block)
            if volc_match:
                volcanism = volc_match.group(1).strip()

            # Galactic Arm Preference
            galactic_arm = ""
            ga_match = re.search(r"Galactic Arm Preference:\s*([^\n]+)", block)
            if ga_match:
                galactic_arm = ga_match.group(1).strip()

            def extract_metrics(label: str) -> Dict[str, float]:
                m = re.search(rf"{label}.*?([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)", block)
                if m:
                    return {
                        "min": float(m.group(1)),
                        "avg": float(m.group(2)),
                        "mode": float(m.group(3)),
                        "max": float(m.group(4)),
                    }
                return {}

            temp_metrics = extract_metrics(r"Temperature\s*(?:\(K\))?")
            press_metrics = extract_metrics(r"Pressure\s*(?:\(atm\))?")
            grav_metrics = extract_metrics(r"Gravity\s*(?:\(G\))?")

            # Attach variants
            stellar_variants = STELLAR_CLASS_VARIANTS.get(genus_name, {})
            # Use block-extracted material variants or fallback to global dict
            mat_variants = block_mat_variants if block_mat_variants else MATERIAL_VARIANTS.get(species_name, {})

            all_species[species_name] = {
                "species_name": species_name,
                "genus": genus_name,
                "base_value": prices.get(species_name, 0),
                "population_pct": pop_pcts.get(species_name, ""),
                "colony_distance_m": colony_dist_m,
                "description": desc,
                "body_type_raw": body_type_raw,
                "atmosphere_raw": atm_raw,
                "volcanism": volcanism,
                "galactic_arm_preference": galactic_arm,
                "temperature": temp_metrics,
                "pressure_atm": press_metrics,
                "gravity_g": grav_metrics,
                "stellar_class_variants": stellar_variants,
                "material_variants": mat_variants,
            }

    return all_species

def build_and_save_rules(output_path: Path = OUTPUT_PATH) -> None:
    rules = parse_species_files()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(rules, fp, ensure_ascii=False, indent=2)
    print(f"[CanonnParser] Saved {len(rules)} species rules to {output_path}")

if __name__ == "__main__":
    build_and_save_rules()

