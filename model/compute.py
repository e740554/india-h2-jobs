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


def compute_demand(target_mt: float, archetype: dict, occupations: list) -> list:
    """Compute occupation-level workforce demand for a given MT target.

    Returns list of dicts, each containing:
      - occupation_id: str or None (None if no matching occupations)
      - nco_group: str
      - phase: str
      - demand: int (rounded to whole workers)
      - allocation_weight: float
      - source: str
      - source_type: str
    """
    if target_mt == 0:
        return []

    h2_output = archetype["h2_output_mt_per_year"]
    units = target_mt / h2_output

    # Index occupations by 4-digit NCO group
    group_index = {}
    for occ in occupations:
        nco_code = occ.get("nco_code", "")
        group = nco_code[:4] if nco_code else ""
        if group:
            group_index.setdefault(group, []).append(occ)

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
                "nco_group": nco_group,
                "phase": phase,
                "demand": round(occ_demand),
                "allocation_weight": round(norm_weight, 6),
                "source": source,
                "source_type": source_type,
            })

    return records


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
