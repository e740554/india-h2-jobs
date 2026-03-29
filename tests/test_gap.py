"""Tests for model/compute.py compute_gap() supply-demand gap engine."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.compute import compute_gap


# ---------------------------------------------------------------------------
# 1. Surplus: supply exceeds demand
# ---------------------------------------------------------------------------

def test_gap_surplus():
    demand = {"occ_1": 100}
    supply = {"occ_1": 150}
    results = compute_gap(demand, supply)
    assert len(results) == 1
    r = results[0]
    assert r["occupation_id"] == "occ_1"
    assert r["supply"] == 150
    assert r["demand"] == 100
    assert r["gap"] == 50
    assert r["gap_status"] == "surplus"


# ---------------------------------------------------------------------------
# 2. Shortage: demand exceeds supply
# ---------------------------------------------------------------------------

def test_gap_shortage():
    demand = {"occ_1": 200}
    supply = {"occ_1": 80}
    results = compute_gap(demand, supply)
    assert len(results) == 1
    r = results[0]
    assert r["gap"] == -120
    assert r["gap_status"] == "shortage"


# ---------------------------------------------------------------------------
# 3. Balanced: supply equals demand
# ---------------------------------------------------------------------------

def test_gap_balanced():
    demand = {"occ_1": 100}
    supply = {"occ_1": 100}
    results = compute_gap(demand, supply)
    assert len(results) == 1
    r = results[0]
    assert r["gap"] == 0
    assert r["gap_status"] == "balanced"


# ---------------------------------------------------------------------------
# 4. No supply data: supply is None
# ---------------------------------------------------------------------------

def test_gap_no_supply_data():
    demand = {"occ_1": 100}
    supply = {"occ_1": None}
    results = compute_gap(demand, supply)
    assert len(results) == 1
    r = results[0]
    assert r["supply"] is None
    assert r["gap"] is None
    assert r["gap_pct"] is None
    assert r["gap_status"] == "no_data"
    # Demand is still recorded even when supply is unknown
    assert r["demand"] == 100


# ---------------------------------------------------------------------------
# 5. gap_pct formula: (supply - demand) / demand * 100
# ---------------------------------------------------------------------------

def test_gap_pct_calculation():
    demand = {"occ_1": 200}
    supply = {"occ_1": 300}
    results = compute_gap(demand, supply)
    r = results[0]
    # (300 - 200) / 200 * 100 = 50.0
    assert r["gap_pct"] == 50.0

    # Negative case
    demand2 = {"occ_1": 200}
    supply2 = {"occ_1": 50}
    results2 = compute_gap(demand2, supply2)
    r2 = results2[0]
    # (50 - 200) / 200 * 100 = -75.0
    assert r2["gap_pct"] == -75.0


# ---------------------------------------------------------------------------
# 6. gap_pct is None when demand is zero
# ---------------------------------------------------------------------------

def test_gap_pct_none_when_zero_demand():
    demand = {"occ_1": 0}
    supply = {"occ_1": 50}
    results = compute_gap(demand, supply)
    r = results[0]
    assert r["gap_pct"] is None
    # Gap value itself is still computed
    assert r["gap"] == 50
    assert r["gap_status"] == "surplus"


# ---------------------------------------------------------------------------
# 7. Empty inputs: both empty dicts return empty list
# ---------------------------------------------------------------------------

def test_gap_empty_inputs():
    results = compute_gap({}, {})
    assert results == []


# ---------------------------------------------------------------------------
# 8. Demand-only occupations: present in demand but absent from supply
# ---------------------------------------------------------------------------

def test_gap_demand_only_occupations():
    demand = {"occ_1": 100}
    supply = {}  # occ_1 not in supply at all
    results = compute_gap(demand, supply)
    assert len(results) == 1
    r = results[0]
    # Missing from supply dict entirely -> treated as None supply
    assert r["supply"] is None
    assert r["gap"] is None
    assert r["gap_pct"] is None
    assert r["gap_status"] == "no_data"


# ---------------------------------------------------------------------------
# 9. Supply-only occupations: present in supply but absent from demand
# ---------------------------------------------------------------------------

def test_gap_supply_only_occupations():
    demand = {}  # occ_1 not in demand at all
    supply = {"occ_1": 75}
    results = compute_gap(demand, supply)
    assert len(results) == 1
    r = results[0]
    assert r["demand"] == 0
    assert r["supply"] == 75
    assert r["gap"] == 75
    assert r["gap_status"] == "surplus"
    # demand is 0, so gap_pct should be None
    assert r["gap_pct"] is None


# ---------------------------------------------------------------------------
# 10. Multiple occupations: mixed surplus/shortage/balanced
# ---------------------------------------------------------------------------

def test_gap_multiple_occupations():
    demand = {
        "occ_surplus": 50,
        "occ_shortage": 200,
        "occ_balanced": 100,
    }
    supply = {
        "occ_surplus": 100,
        "occ_shortage": 80,
        "occ_balanced": 100,
    }
    results = compute_gap(demand, supply)
    assert len(results) == 3

    by_id = {r["occupation_id"]: r for r in results}

    assert by_id["occ_surplus"]["gap"] == 50
    assert by_id["occ_surplus"]["gap_status"] == "surplus"

    assert by_id["occ_shortage"]["gap"] == -120
    assert by_id["occ_shortage"]["gap_status"] == "shortage"

    assert by_id["occ_balanced"]["gap"] == 0
    assert by_id["occ_balanced"]["gap_status"] == "balanced"


# ---------------------------------------------------------------------------
# 11. Results are sorted by occupation_id
# ---------------------------------------------------------------------------

def test_gap_results_sorted_by_id():
    demand = {"z_occ": 10, "a_occ": 20, "m_occ": 30}
    supply = {"z_occ": 10, "a_occ": 20, "m_occ": 30}
    results = compute_gap(demand, supply)
    ids = [r["occupation_id"] for r in results]
    assert ids == ["a_occ", "m_occ", "z_occ"]


# ---------------------------------------------------------------------------
# 12. Zero supply with positive demand: shortage
# ---------------------------------------------------------------------------

def test_gap_zero_supply_with_demand():
    demand = {"occ_1": 150}
    supply = {"occ_1": 0}
    results = compute_gap(demand, supply)
    assert len(results) == 1
    r = results[0]
    assert r["supply"] == 0
    assert r["gap"] == -150
    assert r["gap_status"] == "shortage"
    # (0 - 150) / 150 * 100 = -100.0
    assert r["gap_pct"] == -100.0
