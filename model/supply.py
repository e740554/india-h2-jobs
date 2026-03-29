"""PLFS supply data loading and subdivision-to-occupation allocation.

Loads PLFS labour supply estimates (from plfs_supply.json) and allocates
subdivision-level headcounts to individual occupations using the same
weighted approach as the scenario engine (h2_adjacency + transition_demand).

Output fields per occupation:
  - supply_estimate (int) — estimated current workforce headcount
  - supply_source (str) — "PLFS 2023-24"
  - supply_nco_subdivision (str) — 2-digit NCO subdivision used for allocation
"""

import json
import os


def load_supply(path: str = None) -> dict:
    """Load PLFS supply data from plfs_supply.json.

    Args:
        path: Path to plfs_supply.json. Defaults to model/plfs_supply.json.

    Returns:
        dict keyed by 2-digit NCO subdivision:
        {
            "72": {"pct": 2.3, "headcount": 11500000},
            ...
        }
        Returns empty dict if file doesn't exist.
    """
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "plfs_supply.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def allocate_supply(supply_data: dict, occupations: list) -> list:
    """Distribute subdivision headcounts to occupations by weighted allocation.

    For each occupation, determines its 2-digit NCO subdivision from nco_code[:2],
    then allocates a share of the subdivision headcount proportional to
    (h2_adjacency + transition_demand) weight.

    Args:
        supply_data: dict from load_supply() — {subdivision: {headcount: int, ...}}
        occupations: list of occupation dicts with scores

    Returns:
        occupations list with supply fields added:
          - supply_estimate (int or None)
          - supply_source (str or None)
          - supply_nco_subdivision (str or None)
    """
    if not supply_data:
        for occ in occupations:
            occ["supply_estimate"] = None
            occ["supply_source"] = None
            occ["supply_nco_subdivision"] = None
        return occupations

    # Group occupations by 2-digit NCO subdivision
    subdiv_groups = {}
    for occ in occupations:
        nco_code = occ.get("nco_code", "")
        subdiv = nco_code[:2] if len(nco_code) >= 2 else ""
        if subdiv:
            subdiv_groups.setdefault(subdiv, []).append(occ)

    # Compute weights and allocate within each subdivision
    for subdiv, group_occs in subdiv_groups.items():
        subdiv_data = supply_data.get(subdiv)
        if not subdiv_data:
            for occ in group_occs:
                occ["supply_estimate"] = None
                occ["supply_source"] = None
                occ["supply_nco_subdivision"] = subdiv
            continue

        total_headcount = subdiv_data.get("headcount", 0)

        # Compute allocation weights (same formula as scenario engine)
        weights = []
        for occ in group_occs:
            scores = occ.get("scores") or {}
            w = (scores.get("h2_adjacency") or 0) + (scores.get("transition_demand") or 0)
            weights.append(w)

        total_weight = sum(weights)

        for occ, w in zip(group_occs, weights):
            if total_weight > 0:
                norm_weight = w / total_weight
            else:
                norm_weight = 1.0 / len(group_occs) if group_occs else 0

            occ["supply_estimate"] = round(total_headcount * norm_weight)
            occ["supply_source"] = "PLFS 2023-24"
            occ["supply_nco_subdivision"] = subdiv

    # Handle occupations without a valid NCO code
    for occ in occupations:
        if "supply_estimate" not in occ:
            occ["supply_estimate"] = None
            occ["supply_source"] = None
            occ["supply_nco_subdivision"] = None

    return occupations
