"""Parity tests: Python compute.py and JS engine must produce identical results."""

import json
import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.compute import load_archetype, compute_demand

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _load_real_occupations():
    occ_path = os.path.join(PROJECT_ROOT, "docs", "occupations.json")
    with open(occ_path, "r") as f:
        return json.load(f)["occupations"]


def _run_js_engine(target_mt):
    parity_script = os.path.join(PROJECT_ROOT, "tests", "parity_check.js")
    result = subprocess.run(
        ["node", parity_script, str(target_mt)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"JS engine failed: {result.stderr}"
    return json.loads(result.stdout)


def _run_python_engine(target_mt):
    archetype = load_archetype("alkaline_1gw")
    occupations = _load_real_occupations()
    demand = compute_demand(target_mt, archetype, occupations)
    # Convert to same format as JS: {occ_id: {demand: N, phases: {phase: N}}}
    result = {}
    for record in demand:
        occ_id = record["occupation_id"]
        if occ_id is None:
            continue  # skip unallocated
        if occ_id not in result:
            result[occ_id] = {"demand": 0, "phases": {}}
        result[occ_id]["demand"] += record["demand"]
        phase = record["phase"]
        result[occ_id]["phases"][phase] = (
            result[occ_id]["phases"].get(phase, 0) + record["demand"]
        )
    return result


def test_parity_5mt():
    """Python and JS engines produce identical demand for 5 MT target."""
    py = _run_python_engine(5)
    js = _run_js_engine(5)

    # Same set of occupation IDs
    assert set(py.keys()) == set(js.keys()), (
        f"Occupation ID mismatch: Python has {len(py)}, JS has {len(js)}. "
        f"Only in Python: {set(py.keys()) - set(js.keys())}. "
        f"Only in JS: {set(js.keys()) - set(py.keys())}"
    )

    # Same demand per occupation
    mismatches = []
    for occ_id in py:
        if py[occ_id]["demand"] != js[occ_id]["demand"]:
            mismatches.append(
                f"{occ_id}: Python={py[occ_id]['demand']}, JS={js[occ_id]['demand']}"
            )
    assert not mismatches, "Demand mismatches:\n" + "\n".join(mismatches)

    # Same phase breakdown
    phase_mismatches = []
    for occ_id in py:
        if py[occ_id]["phases"] != js[occ_id]["phases"]:
            phase_mismatches.append(
                f"{occ_id}: Python phases={py[occ_id]['phases']}, "
                f"JS phases={js[occ_id]['phases']}"
            )
    assert not phase_mismatches, "Phase mismatches:\n" + "\n".join(phase_mismatches)


def test_parity_1mt():
    """Python and JS engines produce identical demand for 1 MT target."""
    py = _run_python_engine(1)
    js = _run_js_engine(1)
    assert set(py.keys()) == set(js.keys()), (
        f"Occupation ID mismatch: Python has {len(py)}, JS has {len(js)}."
    )
    for occ_id in py:
        assert py[occ_id]["demand"] == js[occ_id]["demand"], (
            f"{occ_id}: Python={py[occ_id]['demand']}, JS={js[occ_id]['demand']}"
        )


def test_parity_total_demand_matches():
    """Total demand across all occupations matches between Python and JS."""
    py = _run_python_engine(5)
    js = _run_js_engine(5)
    py_total = sum(r["demand"] for r in py.values())
    js_total = sum(r["demand"] for r in js.values())
    assert py_total == js_total, (
        f"Total demand mismatch: Python={py_total}, JS={js_total}"
    )
