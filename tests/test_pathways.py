"""Tests for model/pathways.py."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model.pathways import (
    compute_reskillable_supply,
    get_pathways_for_occupation,
    validate_pathways,
)


def _make_pathways():
    return {
        "pathways": [
            {
                "source_nco": "3134.0100",
                "source_title": "Continuous Still Operator, Petroleum",
                "target_nco": "8131.2100",
                "target_title": "Ammonia Operator",
                "reskill_months": 6,
                "reskill_cost_inr": 85000,
                "training_type": "certification",
                "training_provider": "NSDC",
                "skill_overlap": 0.78,
                "bridging_skills": ["Hydrogen safety"],
                "source": "Test",
                "source_type": "modeled_estimate",
                "confidence": "medium",
            },
            {
                "source_nco": "2145.0500",
                "source_title": "Chemical Engineer, Petroleum",
                "target_nco": "8131.2100",
                "target_title": "Ammonia Operator",
                "reskill_months": 8,
                "reskill_cost_inr": 120000,
                "training_type": "degree",
                "training_provider": "University",
                "skill_overlap": 0.58,
                "bridging_skills": ["Ammonia loop"],
                "source": "Test",
                "source_type": "literature",
                "confidence": "high",
            },
            {
                "source_nco": "3134.0100",
                "source_title": "Continuous Still Operator, Petroleum",
                "target_nco": "2145.0100",
                "target_title": "Chemical Engineer, General",
                "reskill_months": 10,
                "reskill_cost_inr": 130000,
                "training_type": "degree",
                "training_provider": "University",
                "skill_overlap": 0.40,
                "bridging_skills": ["Process design"],
                "source": "Test",
                "source_type": "modeled_estimate",
                "confidence": "low",
            },
        ]
    }


def _make_occupations():
    return [
        {"nco_code": "3134.0100"},
        {"nco_code": "2145.0500"},
        {"nco_code": "8131.2100"},
        {"nco_code": "2145.0100"},
    ]


def test_validate_pathways_accepts_valid_payload():
    validate_pathways(_make_pathways(), _make_occupations())


def test_validate_pathways_rejects_invalid_overlap():
    pathways = _make_pathways()
    pathways["pathways"][0]["skill_overlap"] = 1.2
    with pytest.raises(ValueError, match="skill_overlap"):
        validate_pathways(pathways, _make_occupations())


def test_validate_pathways_rejects_unknown_nco_code():
    pathways = _make_pathways()
    pathways["pathways"][0]["target_nco"] = "9999.9999"
    with pytest.raises(ValueError, match="Unknown target_nco"):
        validate_pathways(pathways, _make_occupations())


def test_get_pathways_for_occupation_filters_inbound_sorted_by_overlap():
    pathways = get_pathways_for_occupation("8131.2100", _make_pathways(), direction="in")
    assert [pathway["skill_overlap"] for pathway in pathways] == [0.78, 0.58]


def test_get_pathways_for_occupation_filters_outbound():
    pathways = get_pathways_for_occupation("3134.0100", _make_pathways(), direction="out")
    assert len(pathways) == 2
    assert all(pathway["source_nco"] == "3134.0100" for pathway in pathways)


def test_compute_reskillable_supply_caps_to_shortage():
    result = compute_reskillable_supply(
        {"nco_code": "8131.2100"},
        100,
        _make_pathways(),
        {
            "3134.0100": 100,
            "2145.0500": 50,
        },
    )
    assert result["reskillable_count"] == 100
    assert result["top_source_occupations"][0]["source_nco"] == "3134.0100"


def test_compute_reskillable_supply_skips_missing_supply_data():
    result = compute_reskillable_supply(
        {"nco_code": "8131.2100"},
        100,
        _make_pathways(),
        {},
    )
    assert result["reskillable_count"] == 0
    assert result["avg_months"] is None
    assert result["sources_with_supply"] == 0
