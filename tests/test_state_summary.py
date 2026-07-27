"""Tests for Runtime.buildStateSummaryRows (plan 012)."""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
PARITY_SCRIPT = os.path.join(PROJECT_ROOT, "tests", "parity_check.js")


def _run_js(command, *args):
    result = subprocess.run(
        ["node", PARITY_SCRIPT, command, *[str(arg) for arg in args]],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"JS helper failed: {result.stderr}"
    return json.loads(result.stdout)


def test_state_summary_row_count_includes_note_row():
    result = _run_js("state-summary-fixture")
    # 2 states (Gujarat, Odisha) with >= 1 cluster each, plus 1 traveling note row.
    assert len(result["rows"]) == 3


def test_state_summary_gujarat_aggregates_its_two_clusters():
    result = _run_js("state-summary-fixture")
    gujarat = next(row for row in result["rows"] if row["state"] == "Gujarat")
    assert gujarat["clusters_counted"] == 2
    assert gujarat["cluster_ids"] == "c1; c2"
    # OCC-1 (20 + 5) + OCC-2 (3); __unallocated__ (100) must be excluded.
    assert gujarat["demand_total"] == 28
    assert gujarat["demand_construction"] == 16
    assert gujarat["demand_commissioning"] == 6
    assert gujarat["demand_operations"] == 6
    assert gujarat["top_occupation_title"] == "Electrician"
    assert gujarat["top_occupation_demand"] == 25


def test_state_summary_odisha_single_cluster():
    result = _run_js("state-summary-fixture")
    odisha = next(row for row in result["rows"] if row["state"] == "Odisha")
    assert odisha["clusters_counted"] == 1
    assert odisha["cluster_ids"] == "c3"
    assert odisha["demand_total"] == 6
    assert odisha["top_occupation_title"] == "Technician"


def test_state_summary_ordering_is_deterministic_by_demand_desc():
    result = _run_js("state-summary-fixture")
    state_rows = [row for row in result["rows"] if row["state"] != "_note"]
    assert [row["state"] for row in state_rows] == ["Gujarat", "Odisha"]


def test_state_summary_note_row_present_and_travels_caveat():
    result = _run_js("state-summary-fixture")
    note_row = result["rows"][-1]
    assert note_row["state"] == "_note"
    assert "not statewide employment estimates" in note_row["top_occupation_demand"]


def test_state_summary_matches_region_aggregate_for_gujarat():
    # Discriminating check: what the CSV reports for a state must match what
    # selecting that state in the UI (aggregateRegionSnapshot + summariseSnapshot)
    # would show on screen.
    result = _run_js("state-summary-fixture")
    assert result["gujaratRowTotal"] == result["gujaratRegionTotal"]


def test_state_summary_matches_region_aggregate_for_all_states_real_scenario():
    # The fixture-based cross-check above can't catch a rounding/reconciliation
    # divergence between buildStateSummaryRows and aggregateRegionSnapshot
    # because its totals are hand-consistent by construction. This runs the
    # same cross-check against the real cluster data and a real scenario
    # timeline, for every state, not just Gujarat.
    result = _run_js("state-summary-real-check", "nghm_5mt_2030_mix")
    assert result["stateCount"] > 0
    assert result["mismatches"] == []


def test_state_summary_headers_shape():
    result = _run_js("state-summary-fixture")
    assert result["headers"] == [
        "state",
        "clusters_counted",
        "cluster_ids",
        "demand_total",
        "demand_construction",
        "demand_commissioning",
        "demand_operations",
        "top_occupation_title",
        "top_occupation_demand",
    ]
