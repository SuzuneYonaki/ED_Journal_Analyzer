import re
from collections import defaultdict
from typing import Dict, Iterable, Optional, Tuple

# Procedurally generated names: "<Sector> <VoxelCode> <massCode>[<n>-]<number>",
# e.g. "Noijo AA-Z e5" or "Noijo JR-W f1-57".
_PROCGEN_NAME = re.compile(
    r"^(?P<sector>.+?) (?P<voxel>[A-Z]{2}-[A-Z]) (?P<mass>[a-h])(?:\d+-)?\d+$"
)


def voxel_key(star_system: Optional[str]) -> Optional[str]:
    """'Noijo AA-Z e5' -> 'Noijo AA-Z e' (sector + voxel code + mass code).

    The same voxel code can be reused at a different mass code (a different
    box size), so the mass code is part of the key. Returns None for names
    that are not procedurally generated.
    """
    if not star_system:
        return None
    m = _PROCGEN_NAME.match(star_system)
    if not m:
        return None
    return f"{m.group('sector')} {m.group('voxel')} {m.group('mass')}"


def voxel_age_stats(conn, keys: Iterable[str]) -> Dict[str, Tuple[float, int]]:
    """Average Age_MY and sample count per voxel key, over systems with a known age."""
    wanted = set(keys)
    if not wanted:
        return {}
    ages = defaultdict(list)
    cur = conn.execute("SELECT star_system, system_age_my FROM systems WHERE system_age_my IS NOT NULL")
    for name, age in cur.fetchall():
        key = voxel_key(name)
        if key in wanted:
            ages[key].append(age)
    return {k: (sum(v) / len(v), len(v)) for k, v in ages.items()}
