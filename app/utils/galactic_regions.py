"""
Galactic Regions Coordinate Resolver Module.

Resolves the 42 official Frontier Developments Galactic Regions from system
coordinates (ly, Sol at 0,0,0) using the community region map by klightspeed
(https://github.com/klightspeed/EliteDangerousRegionMap, MIT License; see
app/data/region_map/LICENSE.klightspeed.txt). The map is a run-length encoded
grid over the X/Z plane, so a lookup depends only on x and z.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REGION_MAP_FILE = Path(__file__).resolve().parents[1] / "data" / "region_map" / "RegionMapData.json"

# Grid origin and scale of RegionMapData.json (83 cells per 4096 ly).
_X0 = -49985
_Z0 = -24105
_CELLS_PER_4096_LY = 83

_JA_NAMES: Dict[str, str] = {
    "Galactic Centre": "銀河中心核",
    "Empyrean Straits": "エンピリアン・ストレイツ",
    "Ryker's Hope": "ライカーズ・ホープ",
    "Odin's Hold": "オーディンズ・ホールド",
    "Norma Arm": "ノーマ腕",
    "Arcadian Stream": "アルカディアン・ストリーム",
    "Izanami": "イザナミ",
    "Inner Orion-Perseus Conflux": "内オリオン・ペルセウス合流帯",
    "Inner Scutum-Centaurus Arm": "内たて・ケンタウルス腕",
    "Norma Expanse": "ノーマ大回廊",
    "Trojan Belt": "トロージャン・ベルト",
    "The Veils": "ヴェールズ",
    "Newton's Vault": "ニュートンズ・ヴォールト",
    "The Conduit": "コンジット",
    "Outer Orion-Perseus Conflux": "外オリオン・ペルセウス合流帯",
    "Orion-Cygnus Arm": "オリオン・はくちょう腕",
    "Temple": "テンプル",
    "Inner Orion Spur": "インナー・オリオン・スパー",
    "Hawking's Gap": "ホーキングズ・ギャップ",
    "Dryman's Point": "ドライマンズ・ポイント",
    "Sagittarius-Carina Arm": "いて・りゅうこつ腕",
    "Mare Somnia": "マーレ・ソムニア",
    "Acheron": "アケロン",
    "Formorian Frontier": "フォモリアン・フロンティア",
    "Hieronymus Delta": "ヒエロニムス・デルタ",
    "Outer Scutum-Centaurus Arm": "外たて・ケンタウルス腕",
    "Outer Arm": "外腕",
    "Aquila's Halo": "アクィラズ・ヘイロー",
    "Errant Marches": "エラント・マーチズ",
    "Perseus Arm": "ペルセウス腕",
    "Formidine Rift": "フォーミディン・リフト",
    "Vulcan Gate": "バルカン・ゲート",
    "Elysian Shore": "エリュシオン・ショア",
    "Sanguineous Rim": "サングイネウス・リム",
    "Outer Orion Spur": "外オリオン・スパー",
    "Achilles's Altar": "アキリーズ・オルター",
    "Xibalba": "シバルバー",
    "Lyra's Song": "ライラズ・ソング",
    "Tenebrae": "テネブラエ",
    "The Abyss": "ジ・アビス",
    "Kepler's Crest": "ケプラーズ・クレスト",
    "The Void": "ザ・ヴォイド",
}


def _load_map() -> Tuple[List[Optional[str]], List[List[List[int]]]]:
    with REGION_MAP_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["regions"], data["regionmap"]


_REGION_NAMES, _REGION_ROWS = _load_map()

# Galactic Regions Dictionary (ID: (English Name, Japanese Name)) -- official Frontier region IDs
GALACTIC_REGIONS: Dict[int, Tuple[str, str]] = {
    rid: (name, _JA_NAMES.get(name, name))
    for rid, name in enumerate(_REGION_NAMES)
    if rid > 0 and name
}

DEFAULT_FALLBACK_REGION = (18, "Inner Orion Spur", "インナー・オリオン・スパー")


def find_region_id(x: Optional[float], z: Optional[float]) -> Optional[int]:
    """Region ID for the given X/Z (ly), or None when outside the mapped area."""
    if x is None or z is None:
        return None
    px = int((x - _X0) * _CELLS_PER_4096_LY / 4096)
    pz = int((z - _Z0) * _CELLS_PER_4096_LY / 4096)
    if px < 0 or pz < 0 or pz >= len(_REGION_ROWS):
        return None
    offset = 0
    for run_length, region_id in _REGION_ROWS[pz]:
        if px < offset + run_length:
            return region_id or None
        offset += run_length
    return None


def get_region_from_coords(
    x: Optional[float], y: Optional[float], z: Optional[float]
) -> Tuple[int, str, str]:
    """
    Galactic Region (region_id, english_name, japanese_name) for system coordinates.

    Falls back to DEFAULT_FALLBACK_REGION (Inner Orion Spur) when a coordinate is missing,
    invalid, or outside the mapped area. Stateless: retains nothing between calls.
    """
    if x is None or y is None or z is None:
        return DEFAULT_FALLBACK_REGION
    try:
        fx = float(x)
        float(y)
        fz = float(z)
    except (ValueError, TypeError):
        return DEFAULT_FALLBACK_REGION

    region_id = find_region_id(fx, fz)
    info = GALACTIC_REGIONS.get(region_id) if region_id else None
    if not info:
        return DEFAULT_FALLBACK_REGION
    return (region_id, info[0], info[1])


def get_region_info(region_id: Optional[int]) -> Tuple[int, str, str]:
    """
    Returns (region_id, english_name, japanese_name) for a known region_id.
    Safely falls back to Inner Orion Spur if unknown or None.
    """
    if region_id is not None and region_id in GALACTIC_REGIONS:
        info = GALACTIC_REGIONS[region_id]
        return (region_id, info[0], info[1])
    return DEFAULT_FALLBACK_REGION
