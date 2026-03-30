"""Tests for model/clusters.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.clusters import (
    aggregate_cluster_demand,
    aggregate_cluster_demand_by_state,
    distribute_demand_by_cluster,
    validate_cluster_affinities,
)


def _make_clusters():
    return {
        "clusters": [
            {
                "id": "alpha",
                "name": "Alpha",
                "state": "Gujarat",
                "archetype_affinity": {"alkaline_1gw": 0.6, "pem_500mw": 0.25},
            },
            {
                "id": "beta",
                "name": "Beta",
                "state": "Tamil Nadu",
                "archetype_affinity": {"alkaline_1gw": 0.4, "pem_500mw": 0.75},
            },
        ]
    }


def _make_archetypes():
    return [
        {"id": "alkaline_1gw"},
        {"id": "pem_500mw"},
    ]


def _make_record(archetype_id="alkaline_1gw", occupation_id="OCC-1", phase="construction", demand=10):
    return {
        "occupation_id": occupation_id,
        "archetype_id": archetype_id,
        "nco_group": "7212",
        "phase": phase,
        "demand": demand,
    }


def test_validate_cluster_affinities_accepts_complete_distribution():
    validate_cluster_affinities(_make_clusters(), _make_archetypes())


def test_validate_cluster_affinities_raises_on_missing_affinity():
    clusters = _make_clusters()
    del clusters["clusters"][0]["archetype_affinity"]["pem_500mw"]
    with pytest.raises(ValueError, match="missing affinity entries"):
        validate_cluster_affinities(clusters, _make_archetypes())


def test_validate_cluster_affinities_raises_when_total_is_not_one():
    clusters = _make_clusters()
    clusters["clusters"][0]["archetype_affinity"]["alkaline_1gw"] = 0.7
    with pytest.raises(ValueError, match="sum to 1.1"):
        validate_cluster_affinities(clusters, _make_archetypes())


def test_distribute_demand_by_cluster_conserves_total():
    records = [_make_record(demand=11)]
    distributed = distribute_demand_by_cluster(records, _make_clusters())
    assert sum(record["demand"] for record in distributed) == 11
    assert {record["cluster_id"] for record in distributed} == {"alpha", "beta"}


def test_distribute_demand_by_cluster_uses_largest_remainder_rounding():
    records = [_make_record(demand=1)]
    distributed = distribute_demand_by_cluster(records, _make_clusters())
    allocated = {record["cluster_id"]: record["demand"] for record in distributed}
    assert allocated == {"alpha": 1}


def test_aggregate_cluster_demand_groups_by_cluster_and_phase():
    distributed = [
        {**_make_record(demand=4), "cluster_id": "alpha", "state": "Gujarat"},
        {**_make_record(demand=6, phase="operations"), "cluster_id": "alpha", "state": "Gujarat"},
        {**_make_record(demand=3), "cluster_id": "beta", "state": "Tamil Nadu"},
    ]
    result = aggregate_cluster_demand(distributed)
    assert result["alpha"]["OCC-1"]["construction"] == 4
    assert result["alpha"]["OCC-1"]["operations"] == 6
    assert result["alpha"]["OCC-1"]["total"] == 10
    assert result["beta"]["OCC-1"]["total"] == 3


def test_aggregate_cluster_demand_by_state_rolls_up_clusters():
    distributed = [
        {**_make_record(demand=4), "cluster_id": "alpha", "state": "Gujarat"},
        {**_make_record(demand=6, occupation_id="OCC-2"), "cluster_id": "gamma", "state": "Gujarat"},
        {**_make_record(demand=3), "cluster_id": "beta", "state": "Tamil Nadu"},
    ]
    result = aggregate_cluster_demand_by_state(distributed)
    assert result["Gujarat"]["OCC-1"]["total"] == 4
    assert result["Gujarat"]["OCC-2"]["total"] == 6
    assert result["Tamil Nadu"]["OCC-1"]["total"] == 3
