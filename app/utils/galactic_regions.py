"""
Galactic Regions Coordinate Resolver Module.

Provides pure-function, stateless 3D bounding-box spatial partitioning
for the 42 official Frontier Developments Galactic Regions (Ly coords, Sol at 0,0,0).
"""

from typing import Optional, Tuple, List, Dict, Any

# Galactic Regions Dictionary (ID: (English Name, Japanese Name))
GALACTIC_REGIONS: Dict[int, Tuple[str, str]] = {
    1: ("Galactic Centre", "銀河中心核"),
    2: ("Empyrean Straits", "エンピリアン・ストレイツ"),
    3: ("Ryker's Hope", "ライカーズ・ホープ"),
    4: ("Odin's Hold", "オーディンズ・ホールド"),
    5: ("Norma Arm", "ノーマ腕"),
    6: ("Arcadian Stream", "アルカディアン・ストリーム"),
    7: ("Izanami", "イザナミ"),
    8: ("Inner Orion-Perseus Conflux", "内オリオン・ペルセウス合流帯"),
    9: ("Inner Scutum-Centaurus Arm", "内たて・ケンタウルス腕"),
    10: ("Norma Expanse", "ノーマ大回廊"),
    11: ("Trojan Belt", "トロージャン・ベルト"),
    12: ("The Veils", "ヴェールズ"),
    13: ("Newton's Vault", "ニュートンズ・ヴォールト"),
    14: ("The Conduit", "コンジット"),
    15: ("Outer Orion-Perseus Conflux", "外オリオン・ペルセウス合流帯"),
    16: ("Orion-Cygnus Arm", "オリオン・はくちょう腕"),
    17: ("Formidine Rift", "フォーミディン・リフト"),
    18: ("Elysian Shore", "エリュシオン・ショア"),
    19: ("Inner Orion Spur", "インナー・オリオン・スパー"),
    20: ("Hawking's Gap", "ホーキングズ・ギャップ"),
    21: ("Sagittarius-Carina Arm", "いて・りゅうこつ腕"),
    22: ("Dryman's Point", "ドライマンズ・ポイント"),
    23: ("Mare Somnia", "マーレ・ソムニア"),
    24: ("Acheron", "アケロン"),
    25: ("Formorian Frontier", "フォモリアン・フロンティア"),
    26: ("Hieronymus Delta", "ヒエロニムス・デルタ"),
    27: ("Outer Scutum-Centaurus Arm", "外たて・ケンタウルス腕"),
    28: ("Outer Arm", "外腕"),
    29: ("Aquila's Halo", "アクィラズ・ヘイロー"),
    30: ("Errant Marches", "エラント・マーチズ"),
    31: ("Perseus Arm", "ペルセウス腕"),
    32: ("Temple", "テンプル"),
    33: ("Vulcan Gate", "バルカン・ゲート"),
    34: ("Sanguineous Rim", "サングイネウス・リム"),
    35: ("Outer Orion Spur", "外オリオン・スパー"),
    36: ("Achilles's Altar", "アキリーズ・オルター"),
    37: ("Xibalba", "シバルバー"),
    38: ("Lyra's Song", "ライラズ・ソング"),
    39: ("Tenebrae", "テネブラエ"),
    40: ("The Abyss", "ジ・アビス"),
    41: ("Kepler's Crest", "ケプラーズ・クレスト"),
    42: ("The Void", "ザ・ヴォイド"),
}

DEFAULT_FALLBACK_REGION = (19, "Inner Orion Spur", "インナー・オリオン・スパー")

# 3D Bounding Boxes: (region_id, min_x, max_x, min_y, max_y, min_z, max_z)
# Prioritized order: inner/focal core regions first, followed by specific arms, then outer sectors.
REGION_BOUNDING_BOXES: List[Tuple[int, float, float, float, float, float, float]] = [
    # 1. Galactic Centre (Sag A* at ~ 25, -21, 25900)
    (1, -3500.0, 3500.0, -2500.0, 2500.0, 22000.0, 29000.0),

    # 19. Inner Orion Spur (Sol at 0, 0, 0 and human bubble)
    (19, -3500.0, 3500.0, -2000.0, 2000.0, -4000.0, 4500.0),

    # 4. Odin's Hold (core-adjacent)
    (4, -8000.0, 8000.0, -3000.0, 3000.0, 29000.0, 38000.0),

    # 2. Empyrean Straits
    (2, 3500.0, 14000.0, -3000.0, 3000.0, 22000.0, 32000.0),

    # 3. Ryker's Hope
    (3, -14000.0, -3500.0, -3000.0, 3000.0, 22000.0, 32000.0),

    # 17. Formidine Rift (North-West gap between spiral arms)
    (17, -15000.0, -5000.0, -3000.0, 3000.0, 4000.0, 18000.0),

    # 18. Elysian Shore (West / rim edge)
    (18, -25000.0, -7000.0, -3500.0, 3500.0, -12000.0, 4000.0),

    # 20. Hawking's Gap (East gap)
    (20, 5000.0, 16000.0, -3000.0, 3000.0, 4000.0, 18000.0),

    # 22. Dryman's Point (East arm region)
    (22, 10000.0, 25000.0, -3000.0, 3000.0, 15000.0, 30000.0),

    # 8. Inner Orion-Perseus Conflux
    (8, -12000.0, -3500.0, -3000.0, 3000.0, 12000.0, 22000.0),

    # 9. Inner Scutum-Centaurus Arm
    (9, -8000.0, 2000.0, -3000.0, 3000.0, 12000.0, 22000.0),

    # 5. Norma Arm
    (5, -18000.0, -8000.0, -3000.0, 3000.0, 16000.0, 30000.0),

    # 6. Arcadian Stream
    (6, 4000.0, 16000.0, -3000.0, 3000.0, 14000.0, 24000.0),

    # 7. Izanami
    (7, 12000.0, 25000.0, -3000.0, 3000.0, 24000.0, 38000.0),

    # 10. Norma Expanse
    (10, -22000.0, -10000.0, -3000.0, 3000.0, 8000.0, 20000.0),

    # 11. Trojan Belt
    (11, -25000.0, -12000.0, -3000.0, 3000.0, 18000.0, 32000.0),

    # 12. The Veils
    (12, -18000.0, -6000.0, -3000.0, 3000.0, 28000.0, 42000.0),

    # 13. Newton's Vault
    (13, -12000.0, 0.0, -3000.0, 3000.0, 36000.0, 48000.0),

    # 14. The Conduit
    (14, 0.0, 14000.0, -3000.0, 3000.0, 36000.0, 48000.0),

    # 15. Outer Orion-Perseus Conflux
    (15, -20000.0, -8000.0, -3000.0, 3000.0, 32000.0, 45000.0),

    # 16. Orion-Cygnus Arm
    (16, -10000.0, 5000.0, -3000.0, 3000.0, -12000.0, -3500.0),

    # 21. Sagittarius-Carina Arm
    (21, 5000.0, 20000.0, -3000.0, 3000.0, 0.0, 14000.0),

    # 23. Mare Somnia
    (23, 14000.0, 28000.0, -3000.0, 3000.0, 30000.0, 44000.0),

    # 24. Acheron
    (24, 8000.0, 22000.0, -3000.0, 3000.0, 40000.0, 52000.0),

    # 25. Formorian Frontier
    (25, 18000.0, 32000.0, -3000.0, 3000.0, 38000.0, 52000.0),

    # 26. Hieronymus Delta
    (26, 20000.0, 35000.0, -3000.0, 3000.0, 20000.0, 35000.0),

    # 27. Outer Scutum-Centaurus Arm
    (27, 18000.0, 34000.0, -3000.0, 3000.0, 5000.0, 20000.0),

    # 28. Outer Arm
    (28, -32000.0, -16000.0, -3500.0, 3500.0, 16000.0, 38000.0),

    # 29. Aquila's Halo
    (29, 12000.0, 30000.0, -3500.0, 3500.0, -15000.0, 2000.0),

    # 30. Errant Marches
    (30, 24000.0, 42000.0, -3500.0, 3500.0, 12000.0, 30000.0),

    # 31. Perseus Arm
    (31, -26000.0, -10000.0, -3500.0, 3500.0, 0.0, 18000.0),

    # 32. Temple
    (32, -6000.0, 6000.0, -3000.0, 3000.0, 15000.0, 24000.0),

    # 33. Vulcan Gate
    (33, -20000.0, -6000.0, -3500.0, 3500.0, -8000.0, 4000.0),

    # 34. Sanguineous Rim
    (34, 4000.0, 20000.0, -3500.0, 3500.0, -10000.0, 2000.0),

    # 35. Outer Orion Spur
    (35, -12000.0, 4000.0, -3500.0, 3500.0, -22000.0, -10000.0),

    # 36. Achilles's Altar
    (36, -30000.0, -12000.0, -3500.0, 3500.0, -10000.0, 8000.0),

    # 37. Xibalba
    (37, -35000.0, -15000.0, -3500.0, 3500.0, 4000.0, 24000.0),

    # 38. Lyra's Song
    (38, -25000.0, -5000.0, -3500.0, 3500.0, 45000.0, 60000.0),

    # 39. Tenebrae
    (39, -5000.0, 15000.0, -3500.0, 3500.0, 48000.0, 62000.0),

    # 40. The Abyss (far northern galactic edge)
    (40, -15000.0, 15000.0, -3500.0, 3500.0, 58000.0, 75000.0),

    # 41. Kepler's Crest
    (41, -30000.0, -10000.0, -3500.0, 3500.0, 55000.0, 72000.0),

    # 42. The Void (far north-east rim)
    (42, 10000.0, 35000.0, -3500.0, 3500.0, 50000.0, 75000.0),
]


def get_region_from_coords(
    x: Optional[float], y: Optional[float], z: Optional[float]
) -> Tuple[int, str, str]:
    """
    Calculates the Galactic Region (region_id, english_name, japanese_name)
    from 3D coordinates (Sol at 0, 0, 0 in Light Years).
    
    If coordinates are None or fall outside all defined bounding boxes,
    safely falls back to (19, "Inner Orion Spur", "インナー・オリオン・スパー").
    
    This is a pure stateless function that retains zero memory between calls.
    """
    if x is None or y is None or z is None:
        return DEFAULT_FALLBACK_REGION

    try:
        fx = float(x)
        fy = float(y)
        fz = float(z)
    except (ValueError, TypeError):
        return DEFAULT_FALLBACK_REGION

    for reg_id, min_x, max_x, min_y, max_y, min_z, max_z in REGION_BOUNDING_BOXES:
        if (min_x <= fx <= max_x) and (min_y <= fy <= max_y) and (min_z <= fz <= max_z):
            info = GALACTIC_REGIONS.get(reg_id)
            if info:
                return (reg_id, info[0], info[1])
            return (reg_id, f"Region {reg_id}", f"リージョン {reg_id}")

    return DEFAULT_FALLBACK_REGION


def get_region_info(region_id: Optional[int]) -> Tuple[int, str, str]:
    """
    Returns (region_id, english_name, japanese_name) for a known region_id.
    Safely falls back to Inner Orion Spur if unknown or None.
    """
    if region_id is not None and region_id in GALACTIC_REGIONS:
        info = GALACTIC_REGIONS[region_id]
        return (region_id, info[0], info[1])
    return DEFAULT_FALLBACK_REGION
