"""Tests for model/supply.py — supply loading and allocation."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.supply import allocate_supply, load_supply


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _make_occupation(occ_id, nco_code, h2_adjacency, transition_demand):
    """Create a minimal occupation dict for testing supply allocation."""
    return {
        "id": occ_id,
        "nco_code": nco_code,
        "scores": {
            "h2_adjacency": h2_adjacency,
            "transition_demand": transition_demand,
        },
    }


# ---------------------------------------------------------------------------
# load_supply tests
# ---------------------------------------------------------------------------

class TestLoadSupply:
    """Tests for load_supply()."""

    def test_load_supply_missing_file_returns_empty(self):
        """Nonexistent path returns empty dict."""
        result = load_supply("/nonexistent/path/plfs_supply.json")
        assert result == {}

    def test_load_supply_reads_json(self, tmp_path):
        """Reads valid JSON file and returns correct structure."""
        supply = {
            "72": {"pct": 2.3, "headcount": 11500000},
            "31": {"pct": 1.1, "headcount": 5500000},
        }
        path = tmp_path / "plfs_supply.json"
        path.write_text(json.dumps(supply), encoding="utf-8")

        result = load_supply(str(path))

        assert result == supply
        assert result["72"]["headcount"] == 11500000
        assert result["31"]["pct"] == 1.1


# ---------------------------------------------------------------------------
# allocate_supply tests
# ---------------------------------------------------------------------------

class TestAllocateSupply:
    """Tests for allocate_supply()."""

    def test_allocate_supply_empty_supply_sets_none(self):
        """Empty supply_data sets all supply fields to None."""
        occs = [
            _make_occupation("occ1", "7212", 3, 4),
            _make_occupation("occ2", "3112", 2, 5),
        ]
        result = allocate_supply({}, occs)

        for occ in result:
            assert occ["supply_estimate"] is None
            assert occ["supply_source"] is None
            assert occ["supply_nco_subdivision"] is None

    def test_allocate_supply_single_occupation(self):
        """Single occupation gets full subdivision headcount."""
        supply = {"72": {"pct": 2.3, "headcount": 10000}}
        occs = [_make_occupation("occ1", "7212", 3, 4)]

        result = allocate_supply(supply, occs)

        assert result[0]["supply_estimate"] == 10000

    def test_allocate_supply_weighted_distribution(self):
        """Two occupations in same subdivision split by weight."""
        supply = {"72": {"pct": 2.0, "headcount": 10000}}
        occs = [
            _make_occupation("occ1", "7212", 6, 4),  # weight = 10
            _make_occupation("occ2", "7215", 2, 3),  # weight = 5
        ]

        result = allocate_supply(supply, occs)

        # occ1 should get 10/15 = 2/3 of 10000 ~ 6667
        # occ2 should get 5/15 = 1/3 of 10000 ~ 3333
        assert result[0]["supply_estimate"] == round(10000 * 10 / 15)
        assert result[1]["supply_estimate"] == round(10000 * 5 / 15)

    def test_allocate_supply_equal_split_zero_weights(self):
        """All zero weights gives equal split across occupations."""
        supply = {"72": {"pct": 2.0, "headcount": 9000}}
        occs = [
            _make_occupation("occ1", "7212", 0, 0),
            _make_occupation("occ2", "7215", 0, 0),
            _make_occupation("occ3", "7218", 0, 0),
        ]

        result = allocate_supply(supply, occs)

        # Equal split: 9000 / 3 = 3000 each
        assert result[0]["supply_estimate"] == 3000
        assert result[1]["supply_estimate"] == 3000
        assert result[2]["supply_estimate"] == 3000

    def test_allocate_supply_missing_subdivision(self):
        """Subdivision not in supply_data gives None for supply_estimate."""
        supply = {"72": {"pct": 2.0, "headcount": 10000}}
        occs = [_make_occupation("occ1", "3112", 3, 4)]  # subdivision 31 not in supply

        result = allocate_supply(supply, occs)

        assert result[0]["supply_estimate"] is None
        assert result[0]["supply_source"] is None
        # supply_nco_subdivision should still be set to the derived subdivision
        assert result[0]["supply_nco_subdivision"] == "31"

    def test_allocate_supply_no_nco_code_gives_none(self):
        """Occupation without nco_code gets None for all supply fields."""
        supply = {"72": {"pct": 2.0, "headcount": 10000}}
        # Test with empty nco_code
        occ_empty = _make_occupation("occ1", "", 3, 4)
        # Test with single character nco_code (too short for subdivision)
        occ_short = _make_occupation("occ2", "7", 3, 4)

        result = allocate_supply(supply, [occ_empty, occ_short])

        for occ in result:
            assert occ["supply_estimate"] is None
            assert occ["supply_source"] is None
            assert occ["supply_nco_subdivision"] is None

    def test_allocate_supply_conservation(self):
        """Sum of per-occ supply within subdivision equals total (rounding tolerance of +/-1)."""
        supply = {"72": {"pct": 2.0, "headcount": 10000}}
        occs = [
            _make_occupation("occ1", "7212", 3, 4),  # weight = 7
            _make_occupation("occ2", "7215", 2, 1),  # weight = 3
            _make_occupation("occ3", "7218", 5, 2),  # weight = 7
        ]

        result = allocate_supply(supply, occs)

        total_allocated = sum(occ["supply_estimate"] for occ in result)
        assert abs(total_allocated - 10000) <= 1

    def test_allocate_supply_sets_source_fields(self):
        """supply_source and supply_nco_subdivision set correctly on allocated occupations."""
        supply = {"72": {"pct": 2.3, "headcount": 5000}}
        occs = [_make_occupation("occ1", "7212", 3, 4)]

        result = allocate_supply(supply, occs)

        assert result[0]["supply_source"] == "PLFS 2023-24"
        assert result[0]["supply_nco_subdivision"] == "72"

    def test_allocate_supply_multiple_subdivisions(self):
        """Occupations from different subdivisions are allocated independently."""
        supply = {
            "72": {"pct": 2.0, "headcount": 10000},
            "31": {"pct": 1.5, "headcount": 6000},
        }
        occs = [
            _make_occupation("occ1", "7212", 5, 5),  # subdiv 72, weight = 10
            _make_occupation("occ2", "7215", 3, 2),  # subdiv 72, weight = 5
            _make_occupation("occ3", "3112", 4, 6),  # subdiv 31, weight = 10
            _make_occupation("occ4", "3115", 2, 3),  # subdiv 31, weight = 5
        ]

        result = allocate_supply(supply, occs)

        # Subdivision 72: occ1 gets 10/15 of 10000, occ2 gets 5/15 of 10000
        assert result[0]["supply_estimate"] == round(10000 * 10 / 15)
        assert result[1]["supply_estimate"] == round(10000 * 5 / 15)
        assert result[0]["supply_nco_subdivision"] == "72"
        assert result[1]["supply_nco_subdivision"] == "72"

        # Subdivision 31: occ3 gets 10/15 of 6000, occ4 gets 5/15 of 6000
        assert result[2]["supply_estimate"] == round(6000 * 10 / 15)
        assert result[3]["supply_estimate"] == round(6000 * 5 / 15)
        assert result[2]["supply_nco_subdivision"] == "31"
        assert result[3]["supply_nco_subdivision"] == "31"

        # Check independence: subdivision 72 total and 31 total
        total_72 = result[0]["supply_estimate"] + result[1]["supply_estimate"]
        total_31 = result[2]["supply_estimate"] + result[3]["supply_estimate"]
        assert abs(total_72 - 10000) <= 1
        assert abs(total_31 - 6000) <= 1
