"""Tests for model/timeline.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.timeline import compute_timeline


def _make_archetypes():
    return [
        {"id": "alkaline_1gw", "construction_years": 3},
        {"id": "ammonia_1mtpa", "construction_years": 5},
    ]


def _make_record(archetype_id="alkaline_1gw", occupation_id="OCC-1", phase="construction", demand=100, **extra):
    return {
        "occupation_id": occupation_id,
        "archetype_id": archetype_id,
        "phase": phase,
        "demand": demand,
        **extra,
    }


def test_compute_timeline_rejects_inverted_years():
    with pytest.raises(ValueError, match="start_year"):
        compute_timeline([], 2030, 2029, _make_archetypes())


def test_compute_timeline_builds_string_year_keys():
    timeline = compute_timeline(
        [_make_record(phase="operations", demand=40)],
        2026,
        2030,
        _make_archetypes(),
        end_year=2031,
    )
    assert set(timeline.keys()) == {"2026", "2027", "2028", "2029", "2030", "2031"}


def test_compute_timeline_operations_reaches_steady_state_at_target_year():
    timeline = compute_timeline(
        [_make_record(phase="operations", demand=40)],
        2026,
        2030,
        _make_archetypes(),
        end_year=2032,
    )
    assert timeline["2029"].get("OCC-1", {}).get("operations", 0) == 0
    assert timeline["2030"]["OCC-1"]["operations"] == 40
    assert timeline["2032"]["OCC-1"]["operations"] == 40


def test_compute_timeline_construction_tapers_to_zero_by_target_year():
    timeline = compute_timeline(
        [_make_record(phase="construction", demand=100)],
        2026,
        2030,
        _make_archetypes(),
        end_year=2030,
    )
    assert timeline["2028"]["OCC-1"]["construction"] == 100
    assert timeline["2029"]["OCC-1"]["construction"] == 50
    assert timeline["2030"].get("OCC-1", {}).get("construction", 0) == 0


def test_compute_timeline_commissioning_peaks_near_target_year():
    timeline = compute_timeline(
        [_make_record(phase="commissioning", demand=80)],
        2026,
        2030,
        _make_archetypes(),
        end_year=2031,
    )
    assert timeline["2028"].get("OCC-1", {}).get("commissioning", 0) == 0
    assert timeline["2029"]["OCC-1"]["commissioning"] == 80
    assert timeline["2030"]["OCC-1"]["commissioning"] == 40
    assert timeline["2031"].get("OCC-1", {}).get("commissioning", 0) == 0


def test_compute_timeline_short_span_clamps_all_phases_into_same_year():
    records = [
        _make_record(phase="construction", demand=10),
        _make_record(phase="commissioning", demand=20),
        _make_record(phase="operations", demand=30),
    ]
    timeline = compute_timeline(records, 2030, 2030, _make_archetypes(), end_year=2030)
    snapshot = timeline["2030"]["OCC-1"]
    assert snapshot["construction"] == 10
    assert snapshot["commissioning"] == 20
    assert snapshot["operations"] == 30
    assert snapshot["total"] == 60


def test_compute_timeline_preserves_cluster_dimension_when_present():
    timeline = compute_timeline(
        [
            _make_record(phase="operations", demand=25, cluster_id="kutch"),
            _make_record(phase="operations", demand=15, cluster_id="vizag"),
        ],
        2026,
        2030,
        _make_archetypes(),
        end_year=2030,
    )
    assert timeline["2030"]["kutch"]["OCC-1"]["operations"] == 25
    assert timeline["2030"]["vizag"]["OCC-1"]["operations"] == 15
