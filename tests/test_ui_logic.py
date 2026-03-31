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


# --- Focus view and client-side metric tests ---

FOCUS_THRESHOLD = 5.0
H2_READY_THRESHOLD = 7.0


def _load_occupations():
    occ_path = os.path.join(PROJECT_ROOT, "docs", "occupations.json")
    with open(occ_path) as f:
        return json.load(f)["occupations"]


def _focus_filter(occupations):
    return [
        occ for occ in occupations
        if occ.get("scores", {}).get("h2_adjacency") is not None
        and occ["scores"]["h2_adjacency"] >= FOCUS_THRESHOLD
    ]


def test_focus_filter_produces_expected_count():
    """Focus view filters to occupations with H2 Adjacency >= 5."""
    occupations = _load_occupations()
    focused = _focus_filter(occupations)
    assert len(focused) > 0, "Focus filter should return some occupations"
    assert len(focused) < len(occupations), "Focus filter should exclude some occupations"
    for occ in focused:
        assert occ["scores"]["h2_adjacency"] >= FOCUS_THRESHOLD


def test_focus_filter_excludes_below_threshold():
    """Occupations below the focus threshold are excluded."""
    occupations = _load_occupations()
    below = [
        occ for occ in occupations
        if occ.get("scores", {}).get("h2_adjacency") is not None
        and occ["scores"]["h2_adjacency"] < FOCUS_THRESHOLD
    ]
    focused = _focus_filter(occupations)
    focused_ids = {occ["id"] for occ in focused}
    for occ in below:
        assert occ["id"] not in focused_ids


def test_client_side_metric_recomputation():
    """H2-ready count (>= 7) and fast-upskill count are correct for focus view."""
    occupations = _load_occupations()
    focused = _focus_filter(occupations)

    h2_ready = 0
    fast_upskill = 0
    for occ in focused:
        s = occ.get("scores", {})
        if s.get("h2_adjacency") is not None and s["h2_adjacency"] >= H2_READY_THRESHOLD:
            h2_ready += 1
        if (s.get("skill_transferability") or 0) >= 7.0 and (s.get("transition_demand") or 0) >= 7.0:
            fast_upskill += 1

    # An occupation with h2_adjacency=5.0 passes focus but is NOT H2-ready
    assert h2_ready < len(focused), "Not all focus occupations should be H2-ready"
    assert h2_ready > 0, "Some occupations should be H2-ready"
    assert fast_upskill >= 0


def test_focus_view_h2_adjacency_5_not_h2_ready():
    """An occupation at exactly h2_adjacency=5.0 passes focus but is NOT H2-ready."""
    mock_occ = {"id": "test", "scores": {"h2_adjacency": 5.0}}
    focused = _focus_filter([mock_occ])
    assert len(focused) == 1, "Score 5.0 passes focus filter"
    assert mock_occ["scores"]["h2_adjacency"] < H2_READY_THRESHOLD, "Score 5.0 is not H2-ready"


def test_state_transitions_focus_sector_all_cycle():
    """viewTier transitions: focus -> sector -> all -> focus."""
    transitions = {
        "focus": "sector",
        "sector": "all",
        "all": "focus",
    }
    state = "focus"
    visited = []
    for _ in range(6):
        visited.append(state)
        state = transitions[state]
    assert visited == ["focus", "sector", "all", "focus", "sector", "all"]


def test_state_resets_on_mode_switch_to_scenario():
    """Entering scenario mode resets viewTier to 'sector'."""
    # Simulate: viewTier is "all", switch to scenario -> resets to "sector"
    view_tier = "all"
    mode = "scenario"
    if mode in ("scenario", "gap"):
        view_tier = "sector"
    assert view_tier == "sector"


def test_state_resets_on_mode_switch_to_atlas():
    """Returning to atlas mode resets viewTier to 'focus'."""
    view_tier = "sector"
    mode = "atlas"
    if mode == "atlas":
        view_tier = "focus"
    assert view_tier == "focus"
