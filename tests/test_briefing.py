"""Tests for the pure Runtime.buildBriefingModel briefing-pack model builder."""

import json
import os
import subprocess

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
BRIEFING_SCRIPT = os.path.join(PROJECT_ROOT, "tests", "briefing_check.js")

MODEL_FIELDS = [
    "title",
    "subtitle",
    "generatedLine",
    "citationLine",
    "demandRows",
    "demandOmittedCount",
    "phaseTotals",
    "gapSummary",
    "pathwayHighlights",
    "methodologyUrl",
]


def _run_briefing(input_payload):
    result = subprocess.run(
        ["node", BRIEFING_SCRIPT, json.dumps(input_payload)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    assert result.returncode == 0, f"JS engine failed: {result.stderr}"
    return json.loads(result.stdout)


def _base_input(mode="scenario", gap_summary=None):
    return {
        "scenario": {"id": "core", "label": "Core Scenario"},
        "datasetVersion": "1.4.3.2",
        "datasetUpdatedLabel": "July 2026",
        "regionLabel": "All India (National)",
        "year": 2030,
        "mode": mode,
        "pageBaseUri": "https://hygoat.in/workforce-atlas/",
        "demandRows": [
            {"title": "Occupation A", "nco_code": "1001", "demand": 500,
             "construction": 500, "commissioning": 0, "operations": 0},
            {"title": "Occupation B", "nco_code": "1002", "demand": 400,
             "construction": 0, "commissioning": 400, "operations": 0},
            {"title": "Occupation C", "nco_code": "1003", "demand": 300,
             "construction": 0, "commissioning": 0, "operations": 300},
            {"title": "Occupation D", "nco_code": "1004", "demand": 200,
             "construction": 100, "commissioning": 100, "operations": 0},
            {"title": "Occupation E", "nco_code": "1005", "demand": 100,
             "construction": 0, "commissioning": 0, "operations": 100},
        ],
        "phaseTotals": {"construction": 600, "commissioning": 500, "operations": 400},
        "gapSummary": gap_summary,
        "pathways": [
            {"source_title": "Source A", "target_title": "Target A", "reskill_months": 6,
             "skill_overlap": 0.8, "source_nco": "2001", "target_nco": "1001"},
            {"source_title": "Source B", "target_title": "Target B", "reskill_months": 3,
             "skill_overlap": 0.9, "source_nco": "2002", "target_nco": "1002"},
        ],
    }


def test_briefing_model_has_all_fields_and_no_undefined():
    model = _run_briefing(_base_input())
    for field in MODEL_FIELDS:
        assert field in model, f"missing field (undefined is dropped by JSON.stringify): {field}"


def test_briefing_demand_rows_capped_at_15_and_omitted_count_correct():
    many_rows = [
        {
            "title": f"Occupation {i}",
            "nco_code": str(1000 + i),
            "demand": 1000 - i,
            "construction": 1000 - i,
            "commissioning": 0,
            "operations": 0,
        }
        for i in range(20)
    ]
    payload = _base_input()
    payload["demandRows"] = many_rows
    model = _run_briefing(payload)
    assert len(model["demandRows"]) <= 15
    assert len(model["demandRows"]) == 15
    assert model["demandOmittedCount"] == 5


def test_briefing_demand_rows_not_truncated_under_limit():
    model = _run_briefing(_base_input())
    assert len(model["demandRows"]) == 5
    assert model["demandOmittedCount"] == 0


def test_briefing_gap_summary_null_when_mode_is_not_gap():
    payload = _base_input(
        mode="scenario",
        gap_summary={"supply_total": 100, "demand_total": 200, "gap_total": -100},
    )
    model = _run_briefing(payload)
    assert model["gapSummary"] is None


def test_briefing_gap_summary_present_in_gap_mode():
    payload = _base_input(
        mode="gap",
        gap_summary={"supply_total": 100, "demand_total": 200, "gap_total": -100},
    )
    model = _run_briefing(payload)
    assert model["gapSummary"] is not None
    assert model["gapSummary"]["supply_total"] == 100
    assert model["gapSummary"]["demand_total"] == 200
    assert model["gapSummary"]["gap_total"] == -100
    assert model["gapSummary"]["caveat"]


def test_briefing_citation_line_contains_dataset_version():
    model = _run_briefing(_base_input())
    assert "1.4.3.2" in model["citationLine"]


def test_briefing_pathway_highlights_capped_at_5():
    many_pathways = [
        {
            "source_title": f"Source {i}",
            "target_title": f"Target {i}",
            "reskill_months": i + 1,
            "skill_overlap": 0.5,
            "source_nco": str(3000 + i),
            "target_nco": str(4000 + i),
        }
        for i in range(8)
    ]
    payload = _base_input()
    payload["pathways"] = many_pathways
    model = _run_briefing(payload)
    assert len(model["pathwayHighlights"]) <= 5
