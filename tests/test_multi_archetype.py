"""Tests for multi-archetype scenario computation in model/compute.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.compute import (
    compute_demand,
    compute_demand_for_units,
    compute_multi_archetype_demand,
)


# ---------------------------------------------------------------------------
# Helper factories (following _make_* convention from test_compute.py)
# ---------------------------------------------------------------------------

def _make_production_archetype(
    archetype_id="alkaline_1gw",
    capacity_mw=1000,
    h2_output=1.0,
    coefficients=None,
):
    """Create a minimal production archetype dict for testing."""
    return {
        "id": archetype_id,
        "name": f"Test Production {archetype_id}",
        "type": "production",
        "capacity_mw": capacity_mw,
        "h2_output_mt_per_year": h2_output,
        "description": "",
        "caveats": "",
        "coefficients": coefficients or [],
    }


def _make_downstream_archetype(
    archetype_id="ammonia_1mtpa",
    h2_input=1.0,
    coefficients=None,
):
    """Create a minimal downstream archetype dict for testing."""
    return {
        "id": archetype_id,
        "name": f"Test Downstream {archetype_id}",
        "type": "downstream",
        "h2_input_mt_per_unit": h2_input,
        "description": "",
        "caveats": "",
        "coefficients": coefficients or [],
    }


def _make_upstream_archetype(
    archetype_id="solar_wind_hybrid_2gw",
    capacity_mw=2000,
    coefficients=None,
):
    """Create a minimal upstream archetype dict for testing."""
    return {
        "id": archetype_id,
        "name": f"Test Upstream {archetype_id}",
        "type": "upstream",
        "capacity_mw": capacity_mw,
        "energy_output_twh_per_year": 4.0,
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


# ---------------------------------------------------------------------------
# compute_demand_for_units — basic
# ---------------------------------------------------------------------------

def test_compute_demand_for_units_basic():
    """Units-based computation produces correct demand."""
    arch = _make_production_archetype(
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    # 2 units * 100 headcount = 200 demand
    result = compute_demand_for_units(2.0, arch, occs)
    assert len(result) == 1
    assert result[0]["demand"] == 200
    assert result[0]["occupation_id"] == "A"


def test_compute_demand_for_units_zero_returns_empty():
    """Zero units produces an empty result list."""
    arch = _make_production_archetype(
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result = compute_demand_for_units(0, arch, occs)
    assert result == []


def test_compute_demand_for_units_has_archetype_id():
    """Each demand record includes the archetype_id field."""
    arch = _make_production_archetype(
        archetype_id="alk_test",
        coefficients=[_make_coefficient(nco_group="7212", headcount=50)],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result = compute_demand_for_units(1.0, arch, occs)
    assert len(result) == 1
    assert result[0]["archetype_id"] == "alk_test"


# ---------------------------------------------------------------------------
# compute_demand delegates to compute_demand_for_units correctly
# ---------------------------------------------------------------------------

def test_compute_demand_delegates_correctly():
    """compute_demand still works and produces archetype_id in records."""
    arch = _make_production_archetype(
        archetype_id="delegate_test",
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]
    result = compute_demand(1.0, arch, occs)
    assert len(result) == 1
    assert result[0]["demand"] == 100
    assert result[0]["archetype_id"] == "delegate_test"


# ---------------------------------------------------------------------------
# compute_multi_archetype_demand — single-archetype fallback
# ---------------------------------------------------------------------------

def test_multi_archetype_single_archetype_fallback():
    """Old scenario format with top-level archetype_id still works."""
    arch = _make_production_archetype(
        archetype_id="alk_1gw",
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    scenario = {"id": "old_format", "target_mt": 2.0, "archetype_id": "alk_1gw"}
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]

    result = compute_multi_archetype_demand(scenario, [arch], occs)
    # 2 MT / 1.0 h2_output = 2 units * 100 headcount = 200
    assert len(result) == 1
    assert result[0]["demand"] == 200
    assert result[0]["archetype_id"] == "alk_1gw"


def test_multi_archetype_single_archetype_fallback_missing_archetype():
    """Single-archetype fallback returns empty when archetype_id not found."""
    scenario = {"id": "missing", "target_mt": 5.0, "archetype_id": "nonexistent"}
    result = compute_multi_archetype_demand(scenario, [], [])
    assert result == []


# ---------------------------------------------------------------------------
# compute_multi_archetype_demand — production only
# ---------------------------------------------------------------------------

def test_multi_archetype_production_only():
    """Single production archetype with 100% share."""
    arch = _make_production_archetype(
        archetype_id="alk_1gw",
        capacity_mw=1000,
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    scenario = {
        "id": "prod_only",
        "target_mt": 5.0,
        "production": [{"archetype_id": "alk_1gw", "share": 1.0}],
    }
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]

    result = compute_multi_archetype_demand(scenario, [arch], occs)
    # units = (5.0 * 1.0) / 1.0 = 5; demand = 5 * 100 = 500
    assert len(result) == 1
    assert result[0]["demand"] == 500


def test_multi_archetype_production_split():
    """60/40 split between two production archetypes."""
    arch_alk = _make_production_archetype(
        archetype_id="alk_1gw",
        capacity_mw=1000,
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    arch_pem = _make_production_archetype(
        archetype_id="pem_500mw",
        capacity_mw=500,
        h2_output=0.5,
        coefficients=[_make_coefficient(nco_group="3113", headcount=80)],
    )
    scenario = {
        "id": "split_60_40",
        "target_mt": 10.0,
        "production": [
            {"archetype_id": "alk_1gw", "share": 0.60},
            {"archetype_id": "pem_500mw", "share": 0.40},
        ],
    }
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100"),
        _make_occupation(occ_id="B", nco_code="3113.0100"),
    ]

    result = compute_multi_archetype_demand(scenario, [arch_alk, arch_pem], occs)

    # Alkaline: units = (10 * 0.60) / 1.0 = 6; demand = 6 * 100 = 600
    alk_records = [r for r in result if r["archetype_id"] == "alk_1gw"]
    assert len(alk_records) == 1
    assert alk_records[0]["demand"] == 600
    assert alk_records[0]["occupation_id"] == "A"

    # PEM: units = (10 * 0.40) / 0.5 = 8; demand = 8 * 80 = 640
    pem_records = [r for r in result if r["archetype_id"] == "pem_500mw"]
    assert len(pem_records) == 1
    assert pem_records[0]["demand"] == 640
    assert pem_records[0]["occupation_id"] == "B"


# ---------------------------------------------------------------------------
# compute_multi_archetype_demand — with downstream
# ---------------------------------------------------------------------------

def test_multi_archetype_with_downstream():
    """Downstream (ammonia) conversion computes units from h2_input_mt_per_unit."""
    arch_prod = _make_production_archetype(
        archetype_id="alk_1gw",
        capacity_mw=1000,
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    arch_down = _make_downstream_archetype(
        archetype_id="ammonia_1mtpa",
        h2_input=0.5,
        coefficients=[_make_coefficient(nco_group="8131", headcount=40)],
    )
    scenario = {
        "id": "with_downstream",
        "target_mt": 10.0,
        "production": [{"archetype_id": "alk_1gw", "share": 1.0}],
        "downstream": [{"archetype_id": "ammonia_1mtpa", "conversion_share": 0.70}],
    }
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100"),
        _make_occupation(occ_id="B", nco_code="8131.0100"),
    ]

    result = compute_multi_archetype_demand(
        scenario, [arch_prod, arch_down], occs
    )

    # Production: units = (10 * 1.0) / 1.0 = 10; demand = 10 * 100 = 1000
    prod_records = [r for r in result if r["archetype_id"] == "alk_1gw"]
    assert len(prod_records) == 1
    assert prod_records[0]["demand"] == 1000

    # Downstream: h2_consumed = 10 * 0.70 = 7.0; units = 7.0 / 0.5 = 14; demand = 14 * 40 = 560
    down_records = [r for r in result if r["archetype_id"] == "ammonia_1mtpa"]
    assert len(down_records) == 1
    assert down_records[0]["demand"] == 560


# ---------------------------------------------------------------------------
# compute_multi_archetype_demand — with upstream
# ---------------------------------------------------------------------------

def test_multi_archetype_with_upstream():
    """Upstream RE capacity is derived from total production MW and ratio."""
    arch_prod = _make_production_archetype(
        archetype_id="alk_1gw",
        capacity_mw=1000,
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    arch_up = _make_upstream_archetype(
        archetype_id="solar_2gw",
        capacity_mw=2000,
        coefficients=[_make_coefficient(nco_group="7411", headcount=60)],
    )
    scenario = {
        "id": "with_upstream",
        "target_mt": 2.0,
        "production": [{"archetype_id": "alk_1gw", "share": 1.0}],
        "upstream": [
            {"archetype_id": "solar_2gw", "re_ratio_gw_per_gw_electrolyser": 2.5},
        ],
    }
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100"),
        _make_occupation(occ_id="B", nco_code="7411.0100"),
    ]

    result = compute_multi_archetype_demand(
        scenario, [arch_prod, arch_up], occs
    )

    # Production: units = (2.0 * 1.0) / 1.0 = 2; total_production_mw = 1000 * 2 = 2000
    prod_records = [r for r in result if r["archetype_id"] == "alk_1gw"]
    assert len(prod_records) == 1
    assert prod_records[0]["demand"] == 200  # 2 * 100

    # Upstream: re_mw = (2000 / 1000) * 2.5 * 1000 = 5000; units = 5000 / 2000 = 2.5
    # demand = 2.5 * 60 = 150
    up_records = [r for r in result if r["archetype_id"] == "solar_2gw"]
    assert len(up_records) == 1
    assert up_records[0]["demand"] == 150


# ---------------------------------------------------------------------------
# compute_multi_archetype_demand — full chain
# ---------------------------------------------------------------------------

def test_multi_archetype_full_chain():
    """Full chain: production + downstream + upstream all contribute demand."""
    arch_alk = _make_production_archetype(
        archetype_id="alk_1gw",
        capacity_mw=1000,
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    arch_pem = _make_production_archetype(
        archetype_id="pem_500mw",
        capacity_mw=500,
        h2_output=0.5,
        coefficients=[_make_coefficient(nco_group="3113", headcount=80)],
    )
    arch_ammonia = _make_downstream_archetype(
        archetype_id="ammonia_1mtpa",
        h2_input=1.0,
        coefficients=[_make_coefficient(nco_group="8131", headcount=40)],
    )
    arch_solar = _make_upstream_archetype(
        archetype_id="solar_2gw",
        capacity_mw=2000,
        coefficients=[_make_coefficient(nco_group="7411", headcount=60)],
    )

    scenario = {
        "id": "full_chain",
        "target_mt": 10.0,
        "production": [
            {"archetype_id": "alk_1gw", "share": 0.60},
            {"archetype_id": "pem_500mw", "share": 0.40},
        ],
        "downstream": [
            {"archetype_id": "ammonia_1mtpa", "conversion_share": 0.50},
        ],
        "upstream": [
            {"archetype_id": "solar_2gw", "re_ratio_gw_per_gw_electrolyser": 2.0},
        ],
    }

    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100"),
        _make_occupation(occ_id="B", nco_code="3113.0100"),
        _make_occupation(occ_id="C", nco_code="8131.0100"),
        _make_occupation(occ_id="D", nco_code="7411.0100"),
    ]

    archetypes = [arch_alk, arch_pem, arch_ammonia, arch_solar]
    result = compute_multi_archetype_demand(scenario, archetypes, occs)

    # --- Production ---
    # Alkaline: units = (10 * 0.60) / 1.0 = 6; mw = 1000 * 6 = 6000
    alk_records = [r for r in result if r["archetype_id"] == "alk_1gw"]
    assert alk_records[0]["demand"] == 600  # 6 * 100

    # PEM: units = (10 * 0.40) / 0.5 = 8; mw = 500 * 8 = 4000
    pem_records = [r for r in result if r["archetype_id"] == "pem_500mw"]
    assert pem_records[0]["demand"] == 640  # 8 * 80

    # total_production_mw = 6000 + 4000 = 10000

    # --- Downstream ---
    # h2_consumed = 10 * 0.50 = 5.0; units = 5.0 / 1.0 = 5
    ammonia_records = [r for r in result if r["archetype_id"] == "ammonia_1mtpa"]
    assert ammonia_records[0]["demand"] == 200  # 5 * 40

    # --- Upstream ---
    # re_mw = (10000 / 1000) * 2.0 * 1000 = 20000; units = 20000 / 2000 = 10
    solar_records = [r for r in result if r["archetype_id"] == "solar_2gw"]
    assert solar_records[0]["demand"] == 600  # 10 * 60

    # Total records: 4 (one per archetype, each with one coefficient matching one occupation)
    assert len(result) == 4


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_multi_archetype_zero_target_returns_empty():
    """Zero target_mt produces an empty result regardless of scenario format."""
    arch = _make_production_archetype(
        archetype_id="alk_1gw",
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    scenario = {
        "id": "zero_target",
        "target_mt": 0,
        "production": [{"archetype_id": "alk_1gw", "share": 1.0}],
    }
    result = compute_multi_archetype_demand(scenario, [arch], [_make_occupation()])
    assert result == []


def test_multi_archetype_missing_archetype_skipped():
    """A production entry referencing a missing archetype_id is gracefully skipped."""
    arch_alk = _make_production_archetype(
        archetype_id="alk_1gw",
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    scenario = {
        "id": "missing_ref",
        "target_mt": 10.0,
        "production": [
            {"archetype_id": "alk_1gw", "share": 0.60},
            {"archetype_id": "nonexistent_arch", "share": 0.40},
        ],
    }
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]

    # Should not raise -- the nonexistent archetype is silently skipped
    result = compute_multi_archetype_demand(scenario, [arch_alk], occs)

    # Only alkaline records produced
    assert len(result) == 1
    assert result[0]["archetype_id"] == "alk_1gw"
    # units = (10 * 0.60) / 1.0 = 6; demand = 6 * 100 = 600
    assert result[0]["demand"] == 600


def test_multi_archetype_missing_downstream_skipped():
    """A downstream entry referencing a missing archetype is gracefully skipped."""
    arch_prod = _make_production_archetype(
        archetype_id="alk_1gw",
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    scenario = {
        "id": "missing_downstream",
        "target_mt": 5.0,
        "production": [{"archetype_id": "alk_1gw", "share": 1.0}],
        "downstream": [{"archetype_id": "nonexistent_down", "conversion_share": 0.50}],
    }
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]

    result = compute_multi_archetype_demand(scenario, [arch_prod], occs)
    # Only production records, downstream skipped
    assert all(r["archetype_id"] == "alk_1gw" for r in result)


def test_multi_archetype_missing_upstream_skipped():
    """An upstream entry referencing a missing archetype is gracefully skipped."""
    arch_prod = _make_production_archetype(
        archetype_id="alk_1gw",
        capacity_mw=1000,
        h2_output=1.0,
        coefficients=[_make_coefficient(nco_group="7212", headcount=100)],
    )
    scenario = {
        "id": "missing_upstream",
        "target_mt": 5.0,
        "production": [{"archetype_id": "alk_1gw", "share": 1.0}],
        "upstream": [
            {"archetype_id": "nonexistent_up", "re_ratio_gw_per_gw_electrolyser": 2.0},
        ],
    }
    occs = [_make_occupation(occ_id="A", nco_code="7212.0100")]

    result = compute_multi_archetype_demand(scenario, [arch_prod], occs)
    assert all(r["archetype_id"] == "alk_1gw" for r in result)


def test_multi_archetype_records_have_archetype_id():
    """Every record from multi-archetype computation carries an archetype_id."""
    arch_alk = _make_production_archetype(
        archetype_id="alk_1gw",
        capacity_mw=1000,
        h2_output=1.0,
        coefficients=[
            _make_coefficient(nco_group="7212", phase="construction", headcount=100),
            _make_coefficient(nco_group="7212", phase="operations", headcount=20),
        ],
    )
    arch_pem = _make_production_archetype(
        archetype_id="pem_500mw",
        capacity_mw=500,
        h2_output=0.5,
        coefficients=[_make_coefficient(nco_group="3113", headcount=80)],
    )
    scenario = {
        "id": "check_ids",
        "target_mt": 4.0,
        "production": [
            {"archetype_id": "alk_1gw", "share": 0.50},
            {"archetype_id": "pem_500mw", "share": 0.50},
        ],
    }
    occs = [
        _make_occupation(occ_id="A", nco_code="7212.0100"),
        _make_occupation(occ_id="B", nco_code="3113.0100"),
    ]

    result = compute_multi_archetype_demand(
        scenario, [arch_alk, arch_pem], occs
    )

    # Every record must have an archetype_id
    for rec in result:
        assert "archetype_id" in rec
        assert rec["archetype_id"] in ("alk_1gw", "pem_500mw")

    # Alkaline has 2 coefficients (construction + operations), PEM has 1
    alk_recs = [r for r in result if r["archetype_id"] == "alk_1gw"]
    pem_recs = [r for r in result if r["archetype_id"] == "pem_500mw"]
    assert len(alk_recs) == 2
    assert len(pem_recs) == 1


def test_multi_archetype_no_production_key_still_processes_downstream():
    """Scenario with no production key but downstream still computes downstream demand."""
    arch_down = _make_downstream_archetype(
        archetype_id="ammonia_1mtpa",
        h2_input=1.0,
        coefficients=[_make_coefficient(nco_group="8131", headcount=40)],
    )
    scenario = {
        "id": "downstream_only",
        "target_mt": 10.0,
        "production": [],
        "downstream": [{"archetype_id": "ammonia_1mtpa", "conversion_share": 0.50}],
    }
    occs = [_make_occupation(occ_id="C", nco_code="8131.0100")]

    result = compute_multi_archetype_demand(scenario, [arch_down], occs)
    # h2_consumed = 10 * 0.50 = 5.0; units = 5.0 / 1.0 = 5; demand = 5 * 40 = 200
    assert len(result) == 1
    assert result[0]["demand"] == 200


def test_multi_archetype_upstream_zero_when_no_production():
    """Upstream with no production MW results in zero RE MW and empty records."""
    arch_up = _make_upstream_archetype(
        archetype_id="solar_2gw",
        capacity_mw=2000,
        coefficients=[_make_coefficient(nco_group="7411", headcount=60)],
    )
    scenario = {
        "id": "upstream_no_prod",
        "target_mt": 10.0,
        "production": [],
        "upstream": [
            {"archetype_id": "solar_2gw", "re_ratio_gw_per_gw_electrolyser": 2.5},
        ],
    }
    occs = [_make_occupation(occ_id="D", nco_code="7411.0100")]

    result = compute_multi_archetype_demand(scenario, [arch_up], occs)
    # total_production_mw = 0, so re_mw = 0, units = 0 -> empty from compute_demand_for_units
    assert result == []
