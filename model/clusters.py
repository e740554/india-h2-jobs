"""Cluster distribution helpers for Phase 3 geography support."""

from __future__ import annotations

import json
import os

from model.compute import load_archetypes


def load_clusters(path: str | None = None) -> dict:
    """Load cluster definitions from model/clusters.json."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "clusters.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_cluster_affinities(
    clusters_data: dict,
    archetypes: list[dict] | None = None,
    tolerance: float = 1e-9,
) -> None:
    """Validate that every cluster defines every archetype and totals sum to 1.0."""
    cluster_list = clusters_data.get("clusters", [])
    if archetypes is None:
        archetypes = load_archetypes()
    archetype_ids = [archetype["id"] for archetype in archetypes]

    for cluster in cluster_list:
        affinity = cluster.get("archetype_affinity", {})
        missing = [arch_id for arch_id in archetype_ids if arch_id not in affinity]
        if missing:
            raise ValueError(
                f"Cluster '{cluster.get('id')}' missing affinity entries for {missing}"
            )

    for arch_id in archetype_ids:
        total = sum(
            float(cluster.get("archetype_affinity", {}).get(arch_id, 0.0))
            for cluster in cluster_list
        )
        if abs(total - 1.0) > tolerance:
            raise ValueError(
                f"Archetype '{arch_id}' cluster affinities sum to {total}, expected 1.0"
            )


def _largest_remainder_allocation(total: int, weights: dict[str, float]) -> dict[str, int]:
    """Allocate an integer total proportionally while preserving the exact sum."""
    if total <= 0:
        return {key: 0 for key in weights}

    raw = {key: total * max(0.0, weight) for key, weight in weights.items()}
    floors = {key: int(value) for key, value in raw.items()}
    remainder = total - sum(floors.values())
    ranked = sorted(
        raw.keys(),
        key=lambda key: (raw[key] - floors[key], weights[key], key),
        reverse=True,
    )
    for key in ranked[:remainder]:
        floors[key] += 1
    return floors


def distribute_demand_by_cluster(demand_records: list[dict], clusters_data: dict) -> list[dict]:
    """Distribute national demand records into cluster-level demand records."""
    cluster_list = clusters_data.get("clusters", [])
    cluster_lookup = {cluster["id"]: cluster for cluster in cluster_list}
    cluster_ids = [cluster["id"] for cluster in cluster_list]
    distributed = []

    for record in demand_records:
        archetype_id = record.get("archetype_id")
        weights = {
            cluster_id: float(
                cluster_lookup[cluster_id]
                .get("archetype_affinity", {})
                .get(archetype_id, 0.0)
            )
            for cluster_id in cluster_ids
        }
        allocation = _largest_remainder_allocation(int(record.get("demand", 0)), weights)
        for cluster_id in cluster_ids:
            allocated = allocation.get(cluster_id, 0)
            if allocated <= 0:
                continue
            cluster = cluster_lookup[cluster_id]
            distributed.append({
                **record,
                "cluster_id": cluster_id,
                "cluster_name": cluster["name"],
                "state": cluster["state"],
                "demand": allocated,
            })

    return distributed


def aggregate_cluster_demand(cluster_records: list[dict]) -> dict:
    """Aggregate cluster demand into cluster -> occupation -> phase totals."""
    result = {}
    for record in cluster_records:
        cluster_bucket = result.setdefault(record["cluster_id"], {})
        occ_key = record["occupation_id"] or "__unallocated__"
        occ_bucket = cluster_bucket.setdefault(
            occ_key,
            {
                "construction": 0,
                "commissioning": 0,
                "operations": 0,
                "total": 0,
            },
        )
        phase = record["phase"]
        demand = int(record["demand"])
        occ_bucket[phase] = occ_bucket.get(phase, 0) + demand
        occ_bucket["total"] += demand
    return result


def aggregate_cluster_demand_by_state(cluster_records: list[dict]) -> dict:
    """Aggregate cluster demand into state -> occupation -> phase totals."""
    result = {}
    for record in cluster_records:
        state_bucket = result.setdefault(record["state"], {})
        occ_key = record["occupation_id"] or "__unallocated__"
        occ_bucket = state_bucket.setdefault(
            occ_key,
            {
                "construction": 0,
                "commissioning": 0,
                "operations": 0,
                "total": 0,
            },
        )
        phase = record["phase"]
        demand = int(record["demand"])
        occ_bucket[phase] = occ_bucket.get(phase, 0) + demand
        occ_bucket["total"] += demand
    return result
