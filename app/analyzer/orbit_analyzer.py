"""
Orbit and Hierarchy Tree Analyzer for Elite Dangerous star systems.
Constructs full celestial hierarchy tree (Stars, Planets, Moons, Sub-moons)
and extracts orbital characteristics.
"""

def parse_parents(parents_raw) -> list:
    """Parse parents list from journal format into structured list."""
    if not parents_raw:
        return []
    if isinstance(parents_raw, list):
        return parents_raw
    return []

def build_system_hierarchy(bodies: list) -> list:
    """
    Build a nested hierarchy tree from flat list of bodies in a system.
    Bodies contain: body_id, body_name, parents, semi_major_axis, orbital_period, etc.
    """
    if not bodies:
        return []

    # Map by body_id and body_name for quick lookup
    body_map = {}
    for b in bodies:
        b_dict = dict(b)
        b_dict["children"] = []
        b_id = b_dict.get("body_id")
        if b_id is not None:
            body_map[b_id] = b_dict

    root_nodes = []
    
    for b_id, b_dict in body_map.items():
        parents = b_dict.get("parents") or []
        if isinstance(parents, str):
            import json
            try:
                parents = json.loads(parents)
            except Exception:
                parents = []

        if not parents:
            # Main star or root barycentre
            root_nodes.append(b_dict)
        else:
            # First parent is direct parent
            direct_parent = parents[0]
            parent_id = None
            for p_type, p_id in direct_parent.items():
                parent_id = p_id
                break

            if parent_id is not None and parent_id in body_map:
                body_map[parent_id]["children"].append(b_dict)
            else:
                # If direct parent not found in map (e.g. barycentre not scanned), keep in roots
                root_nodes.append(b_dict)

    # Sort children and roots by distance from arrival / semi_major_axis
    def sort_tree(node):
        if "children" in node and node["children"]:
            node["children"].sort(key=lambda x: (x.get("semi_major_axis") or x.get("distance_from_arrival_ls") or 0))
            for child in node["children"]:
                sort_tree(child)

    root_nodes.sort(key=lambda x: (x.get("distance_from_arrival_ls") or 0))
    for r in root_nodes:
        sort_tree(r)

    return root_nodes
