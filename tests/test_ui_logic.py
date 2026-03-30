"""Tests for browser-side Phase 3 helper logic."""

import json
import os
import subprocess

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


def test_dominant_phase_identifies_construction_majority():
    result = _run_js("dominant-phase", json.dumps({
        "construction": 60,
        "commissioning": 20,
        "operations": 20,
        "total": 100,
    }))
    assert result == "construction"


def test_dominant_phase_identifies_commissioning_from_nested_bucket():
    result = _run_js("dominant-phase", json.dumps({
        "phases": {
            "construction": 10,
            "commissioning": 70,
            "operations": 20,
        },
        "total": 100,
    }))
    assert result == "commissioning"


def test_dominant_phase_identifies_operations_using_total_fallback():
    result = _run_js("dominant-phase", json.dumps({
        "construction": 0,
        "commissioning": 20,
        "operations": 40,
    }))
    assert result == "operations"


def test_dominant_phase_requires_strict_majority():
    result = _run_js("dominant-phase", json.dumps({
        "construction": 50,
        "commissioning": 50,
        "operations": 0,
        "total": 100,
    }))
    assert result == "mixed"


def test_dominant_phase_respects_explicit_total():
    result = _run_js("dominant-phase", json.dumps({
        "construction": 60,
        "commissioning": 20,
        "operations": 20,
        "total": 200,
    }))
    assert result == "mixed"


def test_dominant_phase_returns_mixed_for_empty_snapshot():
    result = _run_js("dominant-phase", json.dumps({
        "construction": 0,
        "commissioning": 0,
        "operations": 0,
        "total": 0,
    }))
    assert result == "mixed"


def test_get_suggested_cluster_returns_null_without_archetype():
    clusters = {"clusters": [{"id": "alpha", "archetype_affinity": {"alk": 1.0}}]}
    result = _run_js("suggested-cluster", "", json.dumps(clusters))
    assert result is None


def test_get_suggested_cluster_picks_highest_affinity_cluster():
    clusters = {
        "clusters": [
            {"id": "alpha", "archetype_affinity": {"alk": 0.2}},
            {"id": "beta", "archetype_affinity": {"alk": 0.6}},
            {"id": "gamma", "archetype_affinity": {"alk": 0.2}},
        ]
    }
    result = _run_js("suggested-cluster", "alk", json.dumps(clusters))
    assert result == "beta"


def test_get_suggested_cluster_breaks_ties_by_first_cluster():
    clusters = {
        "clusters": [
            {"id": "alpha", "archetype_affinity": {"alk": 0.5}},
            {"id": "beta", "archetype_affinity": {"alk": 0.5}},
        ]
    }
    result = _run_js("suggested-cluster", "alk", json.dumps(clusters))
    assert result == "alpha"
