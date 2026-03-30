"""Reskilling pathway helpers for Phase 3."""

from __future__ import annotations

import json
import os


VALID_TRAINING_TYPES = {"on_the_job", "certification", "diploma", "degree"}
VALID_CONFIDENCE = {"high", "medium", "low"}
VALID_SOURCE_TYPES = {"modeled_estimate", "literature"}


def load_pathways(path: str | None = None) -> dict:
    """Load pathways from model/pathways.json."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "pathways.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_pathways(pathways_data: dict, occupations: list[dict] | None = None) -> None:
    """Validate pathway field bounds and occupation references."""
    known_nco_codes = set()
    if occupations is not None:
        known_nco_codes = {occ.get("nco_code") for occ in occupations if occ.get("nco_code")}

    for pathway in pathways_data.get("pathways", []):
        months = int(pathway["reskill_months"])
        cost = int(pathway["reskill_cost_inr"])
        overlap = float(pathway["skill_overlap"])

        if months < 1 or months > 36:
            raise ValueError(f"Pathway {pathway['source_nco']}->{pathway['target_nco']} has invalid reskill_months")
        if cost < 10_000 or cost > 500_000:
            raise ValueError(f"Pathway {pathway['source_nco']}->{pathway['target_nco']} has invalid reskill_cost_inr")
        if overlap < 0 or overlap > 1:
            raise ValueError(f"Pathway {pathway['source_nco']}->{pathway['target_nco']} has invalid skill_overlap")
        if pathway["training_type"] not in VALID_TRAINING_TYPES:
            raise ValueError(f"Pathway has invalid training_type '{pathway['training_type']}'")
        if pathway["confidence"] not in VALID_CONFIDENCE:
            raise ValueError(f"Pathway has invalid confidence '{pathway['confidence']}'")
        if pathway["source_type"] not in VALID_SOURCE_TYPES:
            raise ValueError(f"Pathway has invalid source_type '{pathway['source_type']}'")
        if occupations is not None:
            if pathway["source_nco"] not in known_nco_codes:
                raise ValueError(f"Unknown source_nco '{pathway['source_nco']}'")
            if pathway["target_nco"] not in known_nco_codes:
                raise ValueError(f"Unknown target_nco '{pathway['target_nco']}'")


def _pathway_list(pathways: dict | list[dict]) -> list[dict]:
    if isinstance(pathways, dict):
        return pathways.get("pathways", [])
    return pathways


def get_pathways_for_occupation(
    nco_code: str,
    pathways: dict | list[dict],
    direction: str = "both",
) -> list[dict]:
    """Return pathways into or out of an occupation sorted by highest overlap."""
    items = _pathway_list(pathways)
    if direction not in {"in", "out", "both"}:
        raise ValueError("direction must be 'in', 'out', or 'both'")

    results = []
    for pathway in items:
        matches_in = direction in {"in", "both"} and pathway["target_nco"] == nco_code
        matches_out = direction in {"out", "both"} and pathway["source_nco"] == nco_code
        if matches_in or matches_out:
            results.append(pathway)

    return sorted(
        results,
        key=lambda item: (-item["skill_overlap"], item["reskill_months"], item["source_title"], item["target_title"]),
    )


def _lookup_supply(source_pathway: dict, supply_data: dict) -> int | None:
    source_nco = source_pathway["source_nco"]
    if source_nco in supply_data:
        value = supply_data[source_nco]
    else:
        value = supply_data.get(source_pathway.get("source_id"))

    if value is None:
        return None
    if isinstance(value, dict):
        if value.get("headcount") is not None:
            return int(value["headcount"])
        if value.get("supply_estimate") is not None:
            return int(value["supply_estimate"])
        return None
    return int(value)


def compute_reskillable_supply(
    occupation: dict | str,
    demand_gap: int,
    pathways: dict | list[dict],
    supply_data: dict,
) -> dict:
    """Estimate inbound reskillable supply for an occupation shortage."""
    target_nco = occupation if isinstance(occupation, str) else occupation.get("nco_code")
    if not target_nco:
        return {
            "reskillable_count": 0,
            "avg_months": None,
            "avg_cost_inr": None,
            "top_source_occupations": [],
            "sources_with_supply": 0,
            "sources_total": 0,
        }

    shortage = abs(int(demand_gap)) if demand_gap < 0 else max(0, int(demand_gap))
    inbound = get_pathways_for_occupation(target_nco, pathways, direction="in")
    usable_sources = []

    remaining = shortage
    for pathway in inbound:
        supply = _lookup_supply(pathway, supply_data)
        if supply is None:
            continue
        candidate = int(round(supply * float(pathway["skill_overlap"])))
        if candidate <= 0:
            continue
        used = candidate if shortage == 0 else min(candidate, remaining)
        usable_sources.append({
            "source_nco": pathway["source_nco"],
            "source_title": pathway["source_title"],
            "reskillable_count": used,
            "reskill_months": pathway["reskill_months"],
            "reskill_cost_inr": pathway["reskill_cost_inr"],
            "skill_overlap": pathway["skill_overlap"],
        })
        if shortage > 0:
            remaining -= used
            if remaining <= 0:
                break

    total = sum(item["reskillable_count"] for item in usable_sources)
    if total > 0:
        avg_months = round(
            sum(item["reskill_months"] * item["reskillable_count"] for item in usable_sources) / total,
            1,
        )
        avg_cost = round(
            sum(item["reskill_cost_inr"] * item["reskillable_count"] for item in usable_sources) / total
        )
    else:
        avg_months = None
        avg_cost = None

    return {
        "reskillable_count": total,
        "avg_months": avg_months,
        "avg_cost_inr": avg_cost,
        "top_source_occupations": usable_sources,
        "sources_with_supply": len(usable_sources),
        "sources_total": len(inbound),
    }
