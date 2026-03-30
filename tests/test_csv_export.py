"""Tests for Phase 3 CSV export helpers."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.clusters import distribute_demand_by_cluster, load_clusters
from model.compute import compute_multi_archetype_demand, load_archetypes, load_scenarios
from model.timeline import compute_timeline

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
PARITY_SCRIPT = os.path.join(PROJECT_ROOT, "tests", "parity_check.js")


def _load_real_occupations():
    occ_path = os.path.join(PROJECT_ROOT, "docs", "occupations.json")
    with open(occ_path, "r", encoding="utf-8") as f:
        return json.load(f)["occupations"]


def _run_js(command, *args):
    result = subprocess.run(
        ["node", PARITY_SCRIPT, command, *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"JS helper failed: {result.stderr}"
    return json.loads(result.stdout)


def _load_scenario(scenario_id):
    for scenario in load_scenarios():
        if scenario["id"] == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario '{scenario_id}'")


def test_full_snapshot_row_count_matches_non_empty_cluster_year_occupations():
    scenario = _load_scenario("nghm_5mt_2030_mix")
    occupations = _load_real_occupations()
    occupation_ids = {occupation["id"] for occupation in occupations}
    archetypes = load_archetypes()

    cluster_records = distribute_demand_by_cluster(
        compute_multi_archetype_demand(scenario, archetypes, occupations),
        load_clusters(),
    )
    timeline = compute_timeline(
        cluster_records,
        int(scenario["start_year"]),
        int(scenario["target_year"]),
        archetypes,
        end_year=int(scenario["target_year"]) + 5,
    )

    expected_rows = sum(
        1
        for year_snapshot in timeline.values()
        for cluster_snapshot in year_snapshot.values()
        for occupation_id in cluster_snapshot.keys()
        if occupation_id != "__unallocated__" and occupation_id in occupation_ids
    )

    result = _run_js("full-snapshot-row-count", scenario["id"])
    assert result["count"] == expected_rows
    assert {
        "cluster",
        "year",
        "phase_construction",
        "phase_commissioning",
        "phase_operations",
        "reskill_pathway_count",
        "reskill_months_avg",
        "reskill_cost_avg",
        "reskillable_supply",
    }.issubset(set(result["headers"]))
