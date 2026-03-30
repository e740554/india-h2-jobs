"""Tests for model/compute.py scenario demand engine."""

import csv
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.compute import (
    aggregate_demand,
    compute_demand,
    compute_demand_for_units,
    export_demand_csv,
    load_archetypes,
    load_archetype,
    load_scenarios,
)


# ---------------------------------------------------------------------------
# Helper factories (following _make_* convention from test_build.py)
# ---------------------------------------------------------------------------

def _make_archetype(
    archetype_id="test_arch",
    h2_output=0.14,
    coefficients=None,
):
    """Create a minimal archetype dict for testing."""
    return {
        "id": archetype_id,
        "name": "Test Archetype",
        "capacity_mw": 1000,
        "h2_output_mt_per_year": h2_output,
        "description": "",
        "caveats": "",
        "coefficients": coefficients or [],
    }


def _make_coefficient(
    nco_group="7212",
    phase="construction",
    headcount=100,
    source="Test Source",
    source_type="modeled_estimate",
):
    """Create a minimal coefficient dict for testing."""
    return {
        "nco_group": nco_group,
        "nco_group_title": f"Group {nco_group}",
        "phase": phase,
        "headcount_per_unit": headcount,
        "source": source,
        "source_type": source_type,
        "notes": "",
    }


def _make_occupation(
    occ_id="NCS-7212.0100",
    nco_code="7212.0100",
    h2_adjacency=5.0,
    transition_demand=5.0,
    title="Test Occupation",
    sector="Power",
):
    """Create a minimal occupation dict for testing."""
    return {
        "id": occ_id,
        "title": title,
        "sector": sector,
        "nco_code": nco_code,
        "scores": {
            "h2_adjacency": h2_adjacency,
            "transition_demand": transition_demand,
        },
    }


def _make_demand_record(
    occupation_id="NCS-7212.0100",
    nco_group="7212",
    phase="construction",
    demand=100,
    allocation_weight=1.0,
    source="Test",
    source_type="modeled_estimate",
):
    """Create a minimal demand record for testing."""
    return {
        "occupation_id": occupation_id,
        "nco_group": nco_group,
        "phase": phase,
        "demand": demand,
        "allocation_weight": allocation_weight,
        "source": source,
        "source_type": source_type,
    }


# ---------------------------------------------------------------------------
# load_archetype
# ---------------------------------------------------------------------------

def test_load_archetype_returns_known_archetype():
    arch = load_archetype("alkaline_1gw")
    assert arch["id"] == "alkaline_1gw"
    assert arch["construction_years"] == 3
    assert arch["h2_output_mt_per_year"] == 0.14
    assert len(arch["coefficients"]) > 0


def test_load_archetype_raises_on_missing_id():
    with pytest.raises(KeyError, match="not_real"):
        load_archetype("not_real")


# ---------------------------------------------------------------------------
# load_scenarios
# ---------------------------------------------------------------------------

def test_load_scenarios_returns_list():
    scenarios = load_scenarios()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 3


def test_load_scenarios_contain_required_fields():
    scenarios = load_scenarios()
    for s in scenarios:
        assert "id" in s
        assert "start_year" in s
        assert "target_year" in s
        assert "target_mt" in s
        assert "year" not in s
        # Single-archetype scenarios have archetype_id; multi-archetype have production
        assert "archetype_id" in s or "production" in s


def test_load_archetypes_include_construction_years():
    archetypes = load_archetypes()
    construction_years = {arch["id"]: arch["construction_years"] for arch in archetypes}
    assert construction_years["alkaline_1gw"] == 3
    assert construction_years["pem_500mw"] == 3
    assert construction_years["ammonia_1mtpa"] == 5
    assert construction_years["solar_wind_hybrid_2gw"] == 2


# ---------------------------------------------------------------------------
# compute_demand — basic
# ---------------------------------------------------------------------------

def test_compute_demand_zero_target_returns_empty():
    arch = _make_archetype(coefficients=[_make_coefficient()])
    occs = [_make_occupation()]
    result = compute_demand(0, arch, occs)
    assert result == []


def test_compute_demand_single_occupation_gets_full_demand():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result = compute_demand(1.0, arch, occs)
    assert len(result) == 1
    # units = 1.0 / 1.0 = 1, demand = 1 * 100 = 100
    assert result[0]["demand"] == 100
    assert result[0]["allocation_weight"] == 1.0
    assert result[0]["occupation_id"] == "A"


def test_compute_demand_distributes_by_weight():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    # Two occupations in same group with different scores
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100", h2_adjacency=8.0, transition_demand=2.0),
        _make_occupation(occ_id="B", nco_code="7212.0200", h2_adjacency=6.0, transition_demand=4.0),
    ]
    result = compute_demand(1.0, arch, occs)
    assert len(result) == 2
    # Both have weight 10 (8+2 and 6+4), so equal split
    assert result[0]["demand"] == 50
    assert result[1]["demand"] == 50


def test_compute_demand_unequal_weight_distribution():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=1000)],
    )
    # occ A: weight 9 (6+3), occ B: weight 1 (1+0)
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100", h2_adjacency=6.0, transition_demand=3.0),
        _make_occupation(occ_id="B", nco_code="7212.0200", h2_adjacency=1.0, transition_demand=0.0),
    ]
    result = compute_demand(1.0, arch, occs)
    # A gets 9/10 * 1000 = 900, B gets 1/10 * 1000 = 100
    assert result[0]["demand"] == 900
    assert result[1]["demand"] == 100


def test_compute_demand_scales_with_target():
    # Use a clean h2_output that divides evenly to avoid rounding noise
    arch = _make_archetype(
        h2_output=0.5,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result_1mt = compute_demand(1.0, arch, occs)
    result_5mt = compute_demand(5.0, arch, occs)
    # 1 MT: units=2, demand=200. 5 MT: units=10, demand=1000. Exact 5x.
    assert result_5mt[0]["demand"] == result_1mt[0]["demand"] * 5


# ---------------------------------------------------------------------------
# compute_demand — edge cases
# ---------------------------------------------------------------------------

def test_compute_demand_empty_occupations_records_unallocated():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    result = compute_demand(1.0, arch, [])
    assert len(result) == 1
    assert result[0]["occupation_id"] is None
    assert result[0]["demand"] == 100
    assert result[0]["allocation_weight"] == 0.0


def test_compute_demand_no_matching_group_records_unallocated():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="9999", headcount=200)],
    )
    # Occupation has a different NCO group
    occs = [_make_occupation(occ_id="A", nco_code="1111.0100")]
    result = compute_demand(1.0, arch, occs)
    assert len(result) == 1
    assert result[0]["occupation_id"] is None
    assert result[0]["nco_group"] == "9999"
    assert result[0]["demand"] == 200


def test_compute_demand_missing_scores_uses_zero_weight():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    # One occupation with scores, one without
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100", h2_adjacency=10.0, transition_demand=0.0),
        {"id": "B", "nco_code": "7212.0200", "scores": {}},
    ]
    result = compute_demand(1.0, arch, occs)
    # A has weight 10, B has weight 0. A gets 100%, B gets 0%
    assert result[0]["occupation_id"] == "A"
    assert result[0]["demand"] == 100
    assert result[1]["occupation_id"] == "B"
    assert result[1]["demand"] == 0


def test_compute_demand_all_zero_scores_equal_split():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=300)],
    )
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100", h2_adjacency=0, transition_demand=0),
        _make_occupation(occ_id="B", nco_code="7212.0200", h2_adjacency=0, transition_demand=0),
        _make_occupation(occ_id="C", nco_code="7212.0300", h2_adjacency=0, transition_demand=0),
    ]
    result = compute_demand(1.0, arch, occs)
    # Equal split: 300/3 = 100 each
    for rec in result:
        assert rec["demand"] == 100


def test_compute_demand_none_scores_treated_as_zero():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    occs = [
        {"id": "A", "nco_code": "7212.0100", "scores": {"h2_adjacency": None, "transition_demand": None}},
        {"id": "B", "nco_code": "7212.0200", "scores": {"h2_adjacency": None, "transition_demand": None}},
    ]
    result = compute_demand(1.0, arch, occs)
    # Both have weight 0, so equal split
    assert result[0]["demand"] == 50
    assert result[1]["demand"] == 50


def test_compute_demand_multiple_coefficients_same_group():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[
            _make_coefficient(nco_group="7212", phase="construction", headcount=100),
            _make_coefficient(nco_group="7212", phase="operations", headcount=50),
        ],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result = compute_demand(1.0, arch, occs)
    assert len(result) == 2
    assert result[0]["phase"] == "construction"
    assert result[0]["demand"] == 100
    assert result[1]["phase"] == "operations"
    assert result[1]["demand"] == 50


def test_compute_demand_preserves_source_fields():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(
            nco_group="7212",
            source="IRENA 2024",
            source_type="modeled_estimate",
        )],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result = compute_demand(1.0, arch, occs)
    assert result[0]["source"] == "IRENA 2024"
    assert result[0]["source_type"] == "modeled_estimate"


def test_compute_demand_rounds_to_integers():
    arch = _make_archetype(
        h2_output=0.14,
        coefficients=[_make_coefficient(nco_group="7212", headcount=1)],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result = compute_demand(1.0, arch, occs)
    # 1.0 / 0.14 * 1 = 7.142857... -> rounds to 7
    assert result[0]["demand"] == 7
    assert isinstance(result[0]["demand"], int)


def test_compute_demand_occupation_without_nco_code_ignored():
    arch = _make_archetype(
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100"),
        {"id": "B", "scores": {}},  # no nco_code at all
    ]
    result = compute_demand(1.0, arch, occs)
    assert len(result) == 1
    assert result[0]["occupation_id"] == "A"


# ---------------------------------------------------------------------------
# aggregate_demand
# ---------------------------------------------------------------------------

def test_aggregate_demand_empty_records():
    agg = aggregate_demand([])
    assert agg["total_demand"] == 0
    assert agg["by_phase"] == {}
    assert agg["by_nco_group"] == {}
    assert agg["by_occupation"] == {}


def test_aggregate_demand_sums_correctly():
    records = [
        _make_demand_record(occupation_id="A", nco_group="7212", phase="construction", demand=100),
        _make_demand_record(occupation_id="B", nco_group="7212", phase="construction", demand=200),
        _make_demand_record(occupation_id="A", nco_group="7212", phase="operations", demand=50),
    ]
    agg = aggregate_demand(records)
    assert agg["total_demand"] == 350
    assert agg["by_phase"] == {"construction": 300, "operations": 50}
    assert agg["by_nco_group"] == {"7212": 350}
    assert agg["by_occupation"] == {"A": 150, "B": 200}


def test_aggregate_demand_excludes_unallocated_from_by_occupation():
    records = [
        _make_demand_record(occupation_id=None, nco_group="9999", demand=500),
        _make_demand_record(occupation_id="A", nco_group="7212", demand=100),
    ]
    agg = aggregate_demand(records)
    assert agg["total_demand"] == 600
    # Unallocated should NOT appear in by_occupation
    assert None not in agg["by_occupation"]
    assert agg["by_occupation"] == {"A": 100}
    # But should appear in by_nco_group
    assert agg["by_nco_group"]["9999"] == 500


def test_aggregate_demand_sum_by_occupation_equals_total_minus_unallocated():
    records = [
        _make_demand_record(occupation_id="A", demand=100),
        _make_demand_record(occupation_id="B", demand=200),
        _make_demand_record(occupation_id=None, demand=50),
    ]
    agg = aggregate_demand(records)
    allocated_sum = sum(agg["by_occupation"].values())
    unallocated = agg["total_demand"] - allocated_sum
    assert unallocated == 50


def test_aggregate_demand_sum_by_phase_equals_total():
    records = [
        _make_demand_record(phase="construction", demand=100),
        _make_demand_record(phase="commissioning", demand=200),
        _make_demand_record(phase="operations", demand=300),
    ]
    agg = aggregate_demand(records)
    assert sum(agg["by_phase"].values()) == agg["total_demand"]


# ---------------------------------------------------------------------------
# Full pipeline: load -> compute -> aggregate
# ---------------------------------------------------------------------------

def test_full_pipeline_with_real_archetype():
    arch = load_archetype("alkaline_1gw")
    # Create one occupation per NCO group so nothing is unallocated
    nco_groups = {c["nco_group"] for c in arch["coefficients"]}
    occs = [
        _make_occupation(
            occ_id=f"NCS-{g}.0100",
            nco_code=f"{g}.0100",
            h2_adjacency=7.0,
            transition_demand=5.0,
        )
        for g in nco_groups
    ]
    records = compute_demand(1.0, arch, occs)
    agg = aggregate_demand(records)

    # Total demand should be positive
    assert agg["total_demand"] > 0
    # Sum of phase values should equal total
    assert sum(agg["by_phase"].values()) == agg["total_demand"]
    # Sum of by_occupation values should equal total (nothing unallocated)
    assert sum(agg["by_occupation"].values()) == agg["total_demand"]
    # All three phases present
    assert set(agg["by_phase"].keys()) == {"construction", "commissioning", "operations"}


def test_full_pipeline_demand_scales_linearly():
    arch = load_archetype("alkaline_1gw")
    nco_groups = {c["nco_group"] for c in arch["coefficients"]}
    occs = [
        _make_occupation(occ_id=f"NCS-{g}.0100", nco_code=f"{g}.0100")
        for g in nco_groups
    ]
    agg_1mt = aggregate_demand(compute_demand(1.0, arch, occs))
    agg_5mt = aggregate_demand(compute_demand(5.0, arch, occs))
    # Due to rounding, allow a small tolerance
    ratio = agg_5mt["total_demand"] / agg_1mt["total_demand"]
    assert 4.95 <= ratio <= 5.05


# ---------------------------------------------------------------------------
# export_demand_csv
# ---------------------------------------------------------------------------

def test_export_demand_csv_writes_file():
    records = [
        _make_demand_record(occupation_id="NCS-7212.0100", demand=100),
    ]
    occs = [_make_occupation(occ_id="NCS-7212.0100", title="Welder")]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    try:
        export_demand_csv(records, occs, path)
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["occupation_id"] == "NCS-7212.0100"
        assert rows[0]["title"] == "Welder"
        assert rows[0]["demand"] == "100"
    finally:
        os.unlink(path)


def test_export_demand_csv_unallocated_row():
    records = [
        _make_demand_record(occupation_id=None, demand=500),
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    try:
        export_demand_csv(records, [], path)
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["occupation_id"] == "(unallocated)"
        assert rows[0]["title"] == ""
    finally:
        os.unlink(path)


def test_export_demand_csv_includes_scores():
    records = [
        _make_demand_record(occupation_id="NCS-7212.0100"),
    ]
    occs = [_make_occupation(occ_id="NCS-7212.0100", h2_adjacency=8.0, transition_demand=6.0)]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    try:
        export_demand_csv(records, occs, path)
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert rows[0]["h2_adjacency"] == "8.0"
        assert rows[0]["transition_demand"] == "6.0"
    finally:
        os.unlink(path)


def test_export_demand_csv_has_correct_columns():
    records = [_make_demand_record()]
    occs = [_make_occupation()]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name
    try:
        export_demand_csv(records, occs, path)
        with open(path) as f:
            reader = csv.DictReader(f)
            _ = list(reader)
            expected = {
                "occupation_id", "title", "sector", "nco_group", "nco_code",
                "phase", "demand", "allocation_weight", "h2_adjacency",
                "transition_demand", "source", "source_type",
            }
            assert set(reader.fieldnames) == expected
    finally:
        os.unlink(path)
