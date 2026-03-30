"""Parity tests for Python engines and the browser runtime helpers."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.clusters import distribute_demand_by_cluster, load_clusters
from model.compute import (
    compute_demand,
    compute_multi_archetype_demand,
    load_archetype,
    load_archetypes,
    load_scenarios,
)
from model.timeline import compute_timeline

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
PARITY_SCRIPT = os.path.join(PROJECT_ROOT, "tests", "parity_check.js")


def _load_real_occupations():
    occ_path = os.path.join(PROJECT_ROOT, "docs", "occupations.json")
    with open(occ_path, "r", encoding="utf-8") as f:
        return json.load(f)["occupations"]


def _load_scenario(scenario_id):
    for scenario in load_scenarios():
        if scenario["id"] == scenario_id:
            return scenario
    raise KeyError(f"Unknown scenario '{scenario_id}'")


def _run_js(command, *args):
    result = subprocess.run(
        ["node", PARITY_SCRIPT, command, *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"JS engine failed: {result.stderr}"
    return json.loads(result.stdout)


def _run_python_single_archetype(target_mt):
    archetype = load_archetype("alkaline_1gw")
    occupations = _load_real_occupations()
    demand = compute_demand(target_mt, archetype, occupations)
    result = {}
    for record in demand:
        occ_id = record["occupation_id"]
        if occ_id is None:
            continue
        if occ_id not in result:
            result[occ_id] = {"demand": 0, "phases": {}}
        result[occ_id]["demand"] += record["demand"]
        phase = record["phase"]
        result[occ_id]["phases"][phase] = (
            result[occ_id]["phases"].get(phase, 0) + record["demand"]
        )
    return result


def _normalize_cluster_records(records):
    return sorted(
        [
            {
                "occupation_id": record["occupation_id"],
                "archetype_id": record["archetype_id"],
                "nco_group": record["nco_group"],
                "phase": record["phase"],
                "demand": int(record["demand"]),
                "allocation_weight": float(record["allocation_weight"]),
                "source": record.get("source", ""),
                "source_type": record.get("source_type", ""),
                "cluster_id": record["cluster_id"],
                "cluster_name": record["cluster_name"],
                "state": record["state"],
            }
            for record in records
        ],
        key=lambda record: (
            record["cluster_id"],
            record["occupation_id"] or "",
            record["archetype_id"] or "",
            record["nco_group"] or "",
            record["phase"] or "",
        ),
    )


def _run_python_cluster_engine(scenario_id):
    scenario = _load_scenario(scenario_id)
    occupations = _load_real_occupations()
    archetypes = load_archetypes()
    cluster_records = distribute_demand_by_cluster(
        compute_multi_archetype_demand(scenario, archetypes, occupations),
        load_clusters(),
    )
    return _normalize_cluster_records(cluster_records)


def _run_python_timeline_engine(scenario_id):
    scenario = _load_scenario(scenario_id)
    occupations = _load_real_occupations()
    archetypes = load_archetypes()
    cluster_records = distribute_demand_by_cluster(
        compute_multi_archetype_demand(scenario, archetypes, occupations),
        load_clusters(),
    )
    return compute_timeline(
        cluster_records,
        int(scenario["start_year"]),
        int(scenario["target_year"]),
        archetypes,
        end_year=int(scenario["target_year"]) + 5,
    )


def test_parity_5mt():
    py = _run_python_single_archetype(5)
    js = _run_js("demand", 5)

    assert set(py.keys()) == set(js.keys()), (
        f"Occupation ID mismatch: Python has {len(py)}, JS has {len(js)}. "
        f"Only in Python: {set(py.keys()) - set(js.keys())}. "
        f"Only in JS: {set(js.keys()) - set(py.keys())}"
    )

    mismatches = []
    for occ_id in py:
        if py[occ_id]["demand"] != js[occ_id]["demand"]:
            mismatches.append(
                f"{occ_id}: Python={py[occ_id]['demand']}, JS={js[occ_id]['demand']}"
            )
    assert not mismatches, "Demand mismatches:\n" + "\n".join(mismatches)

    phase_mismatches = []
    for occ_id in py:
        if py[occ_id]["phases"] != js[occ_id]["phases"]:
            phase_mismatches.append(
                f"{occ_id}: Python phases={py[occ_id]['phases']}, "
                f"JS phases={js[occ_id]['phases']}"
            )
    assert not phase_mismatches, "Phase mismatches:\n" + "\n".join(phase_mismatches)


def test_parity_1mt():
    py = _run_python_single_archetype(1)
    js = _run_js("demand", 1)

    assert set(py.keys()) == set(js.keys()), (
        f"Occupation ID mismatch: Python has {len(py)}, JS has {len(js)}."
    )
    for occ_id in py:
        assert py[occ_id]["demand"] == js[occ_id]["demand"], (
            f"{occ_id}: Python={py[occ_id]['demand']}, JS={js[occ_id]['demand']}"
        )


def test_parity_total_demand_matches():
    py = _run_python_single_archetype(5)
    js = _run_js("demand", 5)
    py_total = sum(record["demand"] for record in py.values())
    js_total = sum(record["demand"] for record in js.values())
    assert py_total == js_total, (
        f"Total demand mismatch: Python={py_total}, JS={js_total}"
    )


def test_cluster_distribution_parity_for_mixed_scenario():
    scenario_id = "nghm_5mt_2030_mix"
    py = _run_python_cluster_engine(scenario_id)
    js = _run_js("cluster", scenario_id)
    assert py == js


def test_timeline_parity_for_mixed_scenario():
    scenario_id = "nghm_5mt_2030_mix"
    py = _run_python_timeline_engine(scenario_id)
    js = _run_js("timeline", scenario_id)
    assert py == js
