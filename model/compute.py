"""Thin Python validation/export engine for the scenario demand model.

This is NOT the runtime engine (that's JavaScript in the frontend).
This module is for validation, batch CSV exports, and parity testing
against the JS engine.

Model chain (5 steps):
  1. MT target -> units  (units = target_mt / archetype.h2_output_mt_per_year)
  2. For each coefficient -> raw demand  (units * headcount_per_unit)
  3. Distribute to occupations within each NCO group by allocation weight
  4. Split by phase (already phase-specific from coefficients)
  5. Aggregate totals per occupation
"""

import csv
import json
import os


def load_archetype(archetype_id: str) -> dict:
    """Load a specific archetype from model/archetypes.json."""
    path = os.path.join(os.path.dirname(__file__), "archetypes.json")
    with open(path) as f:
        archetypes = json.load(f)
    for arch in archetypes:
        if arch["id"] == archetype_id:
            return arch
    raise KeyError(f"Archetype '{archetype_id}' not found")


def load_scenarios() -> list:
    """Load all scenarios from model/scenarios.json."""
    path = os.path.join(os.path.dirname(__file__), "scenarios.json")
    with open(path) as f:
        return json.load(f)


def compute_demand_for_units(units: float, archetype: dict, occupations: list) -> list:
    """Low-level demand computation for a pre-computed number of units.

    Refactored from compute_demand() to decouple unit derivation from
    demand distribution. compute_demand() remains as the public API for
    single-archetype scenarios (calls this internally).

    Returns list of dicts, each containing:
      - occupation_id: str or None (None if no matching occupations)
      - archetype_id: str
      - nco_group: str
      - phase: str
      - demand: int (rounded to whole workers)
      - allocation_weight: float
      - source: str
      - source_type: str
    """
    if units <= 0:
        return []

    # Index occupations by 4-digit NCO group
    group_index = {}
    for occ in occupations:
        nco_code = occ.get("nco_code", "")
        group = nco_code[:4] if nco_code else ""
        if group:
            group_index.setdefault(group, []).append(occ)

    archetype_id = archetype.get("id", "")
    records = []

    for coeff in archetype["coefficients"]:
        nco_group = coeff["nco_group"]
        phase = coeff["phase"]
        raw_demand = units * coeff["headcount_per_unit"]
        source = coeff.get("source", "")
        source_type = coeff.get("source_type", "")

        group_occs = group_index.get(nco_group, [])

        if not group_occs:
            # No matching occupations -- record as unallocated
            records.append({
                "occupation_id": None,
                "archetype_id": archetype_id,
                "nco_group": nco_group,
                "phase": phase,
                "demand": round(raw_demand),
                "allocation_weight": 0.0,
                "source": source,
                "source_type": source_type,
            })
            continue

        # Compute allocation weights
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
                # Equal distribution when all weights are zero
                norm_weight = 1.0 / len(group_occs)

            occ_demand = raw_demand * norm_weight
            records.append({
                "occupation_id": occ["id"],
                "archetype_id": archetype_id,
                "nco_group": nco_group,
                "phase": phase,
                "demand": round(occ_demand),
                "allocation_weight": round(norm_weight, 6),
                "source": source,
                "source_type": source_type,
            })

    return records


def compute_demand(target_mt: float, archetype: dict, occupations: list) -> list:
    """Compute occupation-level workforce demand for a given MT target.

    Public API for single-archetype scenarios. Delegates to
    compute_demand_for_units() after deriving units from target_mt.

    Returns list of dicts (same schema as compute_demand_for_units).
    """
    if target_mt <= 0:
        return []

    h2_output = archetype.get("h2_output_mt_per_year", 0)
    if not h2_output:
        return []
    units = target_mt / h2_output

    return compute_demand_for_units(units, archetype, occupations)


def compute_multi_archetype_demand(
    scenario: dict, archetypes: list, occupations: list
) -> list:
    """Compute demand across a multi-archetype scenario.

    Detects scenario format (single vs. multi-archetype) and dispatches
    accordingly. Single-archetype scenarios (with 'archetype_id' at top level)
    fall back to compute_demand().

    Computation chain for multi-archetype:
      1. Production: units = (target_mt * share) / archetype.h2_output_mt_per_year
      2. Downstream: units = (target_mt * conversion_share) / archetype.h2_input_mt_per_unit
      3. Upstream: units = (sum_production_mw / 1000 * re_ratio) / (archetype.capacity_mw / 1000)

    Returns list of demand records with 'archetype_id' field.
    """
    target_mt = scenario.get("target_mt", 0)
    if target_mt <= 0:
        return []

    # Build archetype lookup
    arch_lookup = {a["id"]: a for a in archetypes}

    # Single-archetype fallback
    if "archetype_id" in scenario and "production" not in scenario:
        arch = arch_lookup.get(scenario["archetype_id"])
        if not arch:
            return []
        return compute_demand(target_mt, arch, occupations)

    all_records = []

    # Track total production capacity in MW for upstream calculation
    total_production_mw = 0

    # 1. Production archetypes
    for prod in scenario.get("production", []):
        arch = arch_lookup.get(prod["archetype_id"])
        if not arch:
            continue
        h2_output = arch.get("h2_output_mt_per_year", 0)
        if not h2_output:
            continue
        mt_share = target_mt * prod.get("share", 0)
        units = mt_share / h2_output
        total_production_mw += (arch.get("capacity_mw") or 0) * units
        all_records.extend(compute_demand_for_units(units, arch, occupations))

    # 2. Downstream archetypes
    for down in scenario.get("downstream", []):
        arch = arch_lookup.get(down["archetype_id"])
        if not arch:
            continue
        h2_input = arch.get("h2_input_mt_per_unit", 0)
        if not h2_input:
            continue
        h2_consumed = target_mt * down.get("conversion_share", 0)
        units = h2_consumed / h2_input
        all_records.extend(compute_demand_for_units(units, arch, occupations))

    # 3. Upstream archetypes
    for up in scenario.get("upstream", []):
        arch = arch_lookup.get(up["archetype_id"])
        if not arch:
            continue
        arch_capacity_mw = arch.get("capacity_mw") or 0
        if not arch_capacity_mw:
            continue
        re_ratio = up.get("re_ratio_gw_per_gw_electrolyser", 0)
        # Convert production MW to GW, apply ratio, convert back to MW
        re_mw = (total_production_mw / 1000) * re_ratio * 1000
        units = re_mw / arch_capacity_mw
        all_records.extend(compute_demand_for_units(units, arch, occupations))

    return all_records


def compute_gap(demand_by_occupation: dict, supply_data: dict) -> list:
    """Compute supply-demand gap per occupation.

    Sign convention: gap = supply - demand
      Positive = surplus (more workers available than needed)
      Negative = shortage (more workers needed than available)

    Args:
        demand_by_occupation: dict {occupation_id: int} from aggregate_demand()
        supply_data: dict {occupation_id: int or None} supply estimates

    Returns: List of dicts:
        {occupation_id, supply, demand, gap, gap_pct, gap_status}
    """
    # Collect all occupation IDs from both sides
    all_ids = set(demand_by_occupation.keys()) | set(supply_data.keys())
    results = []

    for occ_id in sorted(all_ids):
        demand = demand_by_occupation.get(occ_id, 0)
        supply = supply_data.get(occ_id)

        if supply is None:
            results.append({
                "occupation_id": occ_id,
                "supply": None,
                "demand": demand,
                "gap": None,
                "gap_pct": None,
                "gap_status": "no_data",
            })
            continue

        gap = supply - demand

        if demand > 0:
            gap_pct = round((supply - demand) / demand * 100, 1)
        else:
            gap_pct = None

        if gap > 0:
            gap_status = "surplus"
        elif gap < 0:
            gap_status = "shortage"
        else:
            gap_status = "balanced"

        results.append({
            "occupation_id": occ_id,
            "supply": supply,
            "demand": demand,
            "gap": gap,
            "gap_pct": gap_pct,
            "gap_status": gap_status,
        })

    return results


def aggregate_demand(demand_records: list) -> dict:
    """Aggregate demand records into summary.

    Returns dict with:
      - total_demand: int
      - by_phase: dict[str, int]
      - by_nco_group: dict[str, int]
      - by_occupation: dict[str, int]
    """
    total = 0
    by_phase = {}
    by_nco_group = {}
    by_occupation = {}

    for rec in demand_records:
        demand = rec["demand"]
        total += demand

        phase = rec["phase"]
        by_phase[phase] = by_phase.get(phase, 0) + demand

        nco_group = rec["nco_group"]
        by_nco_group[nco_group] = by_nco_group.get(nco_group, 0) + demand

        occ_id = rec["occupation_id"]
        if occ_id is not None:
            by_occupation[occ_id] = by_occupation.get(occ_id, 0) + demand

    return {
        "total_demand": total,
        "by_phase": by_phase,
        "by_nco_group": by_nco_group,
        "by_occupation": by_occupation,
    }


def export_demand_csv(demand_records: list, occupations: list, output_path: str):
    """Export demand to CSV with occupation details."""
    # Build occupation lookup
    occ_lookup = {occ["id"]: occ for occ in occupations}

    fieldnames = [
        "occupation_id",
        "title",
        "sector",
        "nco_group",
        "nco_code",
        "phase",
        "demand",
        "allocation_weight",
        "h2_adjacency",
        "transition_demand",
        "source",
        "source_type",
    ]

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rec in demand_records:
            occ_id = rec["occupation_id"]
            occ = occ_lookup.get(occ_id, {}) if occ_id else {}
            scores = occ.get("scores") or {}

            writer.writerow({
                "occupation_id": occ_id or "(unallocated)",
                "title": occ.get("title", ""),
                "sector": occ.get("sector", ""),
                "nco_group": rec["nco_group"],
                "nco_code": occ.get("nco_code", ""),
                "phase": rec["phase"],
                "demand": rec["demand"],
                "allocation_weight": rec["allocation_weight"],
                "h2_adjacency": scores.get("h2_adjacency", ""),
                "transition_demand": scores.get("transition_demand", ""),
                "source": rec["source"],
                "source_type": rec["source_type"],
            })
