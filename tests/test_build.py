"""Tests for build/build.py pipeline functions."""

import json
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build.build import (
    pct,
    count_present,
    count_true,
    merge_scores,
    compute_upskill_paths,
    compute_workforce_gap,
    compute_summary_metrics,
    compute_data_quality,
    sync_model_data,
    H2_ADJACENCY_THRESHOLD,
)


# --- pct ---

def test_pct_normal():
    assert pct(1, 4) == 25.0


def test_pct_zero_total():
    assert pct(5, 0) == 0.0


def test_pct_full_coverage():
    assert pct(10, 10) == 100.0


# --- count_present / count_true ---

def test_count_present_ignores_none():
    occs = [{"employment": 100}, {"employment": None}, {"employment": 200}]
    assert count_present(occs, "employment") == 2


def test_count_true_counts_only_true():
    occs = [{"source_ncs": True}, {"source_ncs": False}, {"source_ncs": True}]
    assert count_true(occs, "source_ncs") == 2


# --- merge_scores ---

def _make_occ(occ_id, **kwargs):
    defaults = {
        "id": occ_id,
        "sector": "Power",
        "employment": None,
        "scores": {},
        "score_details": {},
    }
    defaults.update(kwargs)
    return defaults


def test_merge_scores_attaches_score_and_rationale():
    occs = [_make_occ("OCC001")]
    scores = {
        "OCC001": {
            "h2_adjacency": {"score": 8.0, "rationale": "Core role"},
        }
    }
    result = merge_scores(occs, scores)
    assert result[0]["scores"]["h2_adjacency"] == 8.0
    assert result[0]["score_details"]["h2_adjacency"]["rationale"] == "Core role"


def test_merge_scores_handles_raw_value_without_dict():
    occs = [_make_occ("OCC002")]
    scores = {"OCC002": {"h2_adjacency": 7.5}}
    result = merge_scores(occs, scores)
    assert result[0]["scores"]["h2_adjacency"] == 7.5
    assert result[0]["score_details"]["h2_adjacency"]["rationale"] is None


def test_merge_scores_missing_occupation_gets_empty_scores():
    occs = [_make_occ("OCC999")]
    scores = {}
    result = merge_scores(occs, scores)
    assert result[0]["scores"] == {}


# --- compute_upskill_paths ---

def _make_scored_occ(occ_id, sector="Power", h2=8.0, td=7.0):
    return {
        "id": occ_id,
        "sector": sector,
        "scores": {"h2_adjacency": h2, "transition_demand": td},
        "upskill_paths": [],
    }


def test_compute_upskill_paths_top_5_by_score():
    occs = [_make_scored_occ(f"OCC{i:03d}", h2=float(i), td=float(i)) for i in range(1, 9)]
    result = compute_upskill_paths(occs)
    # OCC001 should have paths to higher-scored occupations, capped at 5
    assert len(result[0]["upskill_paths"]) == 5


def test_compute_upskill_paths_excludes_self():
    occs = [_make_scored_occ("A"), _make_scored_occ("B")]
    result = compute_upskill_paths(occs)
    assert "A" not in result[0]["upskill_paths"]


def test_compute_upskill_paths_skips_occupations_missing_scores():
    occs = [
        {"id": "A", "sector": "Power", "scores": {"h2_adjacency": 8.0, "transition_demand": 7.0}, "upskill_paths": []},
        {"id": "B", "sector": "Power", "scores": {}, "upskill_paths": []},  # missing scores
    ]
    result = compute_upskill_paths(occs)
    assert result[0]["upskill_paths"] == []  # B is ineligible


def test_compute_upskill_paths_isolated_to_sector():
    occs = [
        _make_scored_occ("A", sector="Power"),
        _make_scored_occ("B", sector="Mining"),
    ]
    result = compute_upskill_paths(occs)
    # A should not get B as an upskill path (different sector)
    assert "B" not in result[0]["upskill_paths"]


# --- compute_workforce_gap ---

def _make_employed_occ(occ_id, employment, h2_adjacency):
    return {
        "id": occ_id,
        "employment": employment,
        "scores": {"h2_adjacency": h2_adjacency},
    }


def test_compute_workforce_gap_returns_none_when_employment_missing():
    occs = [_make_employed_occ("A", None, 8.0)]
    assert compute_workforce_gap(occs) is None


def test_compute_workforce_gap_returns_full_target_when_no_eligible_occupations():
    # No occupations meet the h2_adjacency threshold — eligible is empty.
    # any(...for occ in []) is vacuously False, so None is NOT returned.
    # The function returns the full 5MMT target as if the gap is 100%.
    # NOTE: this is a known edge-case behavior. A dataset with zero H2-ready
    # occupations would surface 2,500,000 in the UI as a real metric. In
    # practice the production data always has scored H2-ready occupations,
    # but this warrants a design review if the threshold changes.
    occs = [_make_employed_occ("A", 1000, 5.0)]
    result = compute_workforce_gap(occs)
    assert result == 2_500_000


def test_compute_workforce_gap_positive():
    occs = [_make_employed_occ("A", 100_000, 8.0)]
    gap = compute_workforce_gap(occs)
    assert gap == 2_500_000 - 100_000


def test_compute_workforce_gap_clamps_to_zero():
    # If workforce exceeds target, gap should be 0, not negative
    occs = [_make_employed_occ("A", 10_000_000, 8.0)]
    assert compute_workforce_gap(occs) == 0


# --- compute_summary_metrics ---

def test_compute_summary_metrics_counts_h2_ready():
    occs = [
        {"scores": {"h2_adjacency": 8.0, "transition_demand": 7.0, "skill_transferability": 7.0}},
        {"scores": {"h2_adjacency": 5.0, "transition_demand": 7.0, "skill_transferability": 7.0}},
        {"scores": {}},
    ]
    # Need employment for gap calculation — set to None so gap is None
    for occ in occs:
        occ["employment"] = None
    metrics = compute_summary_metrics(occs)
    assert metrics["h2_ready_occupations"] == 1


def test_compute_summary_metrics_counts_fast_upskill():
    occs = [
        {"scores": {"h2_adjacency": 8.0, "transition_demand": 8.0, "skill_transferability": 8.0}, "employment": None},
        {"scores": {"h2_adjacency": 8.0, "transition_demand": 6.0, "skill_transferability": 8.0}, "employment": None},
    ]
    metrics = compute_summary_metrics(occs)
    # Only first occ qualifies (both st >= 7 and td >= 7)
    assert metrics["fast_upskill_paths"] == 1


# --- compute_data_quality ---

def test_compute_data_quality_labour_market_status_pending():
    occs = [{"employment": None, "median_wage_inr": None, "formal_sector_pct": None,
              "source_ncs": True, "source_plfs": False, "source_ncvet": False,
              "scores": {}}]
    result = compute_data_quality(occs)
    assert result["labour_market_status"] == "pending"


def test_compute_data_quality_labour_market_status_complete():
    occs = [{"employment": 1000, "median_wage_inr": 50000, "formal_sector_pct": 60,
              "source_ncs": True, "source_plfs": False, "source_ncvet": False,
              "scores": {}}]
    result = compute_data_quality(occs)
    assert result["labour_market_status"] == "complete"


def test_compute_data_quality_notes_when_incomplete():
    occs = [{"employment": None, "median_wage_inr": None, "formal_sector_pct": None,
              "source_ncs": True, "source_plfs": False, "source_ncvet": False,
              "scores": {}}]
    result = compute_data_quality(occs)
    assert len(result["notes"]) > 0


# --- sync_model_data ---

def test_sync_model_data_copies_files_to_docs_and_web(monkeypatch, tmp_path):
    """sync_model_data copies each MODEL_JSON_FILES entry from MODEL_DIR to DOCS_DIR and WEB_DIR."""
    import build.build as build_module

    model_dir = tmp_path / "model"
    docs_dir = tmp_path / "docs"
    web_dir = tmp_path / "web"
    model_dir.mkdir()
    docs_dir.mkdir()
    web_dir.mkdir()

    # Write fake model JSON files
    sample_data = {"test": True}
    for filename in ["archetypes.json", "scenarios.json"]:
        (model_dir / filename).write_text(json.dumps(sample_data), encoding="utf-8")

    # Patch module-level constants
    monkeypatch.setattr(build_module, "MODEL_DIR", str(model_dir))
    monkeypatch.setattr(build_module, "DOCS_DIR", str(docs_dir))
    monkeypatch.setattr(build_module, "WEB_DIR", str(web_dir))

    sync_model_data()

    for filename in ["archetypes.json", "scenarios.json"]:
        docs_file = docs_dir / filename
        web_file = web_dir / filename
        assert docs_file.exists(), f"Expected {docs_file} to exist in docs/"
        assert web_file.exists(), f"Expected {web_file} to exist in web/"
        assert json.loads(docs_file.read_text()) == sample_data
        assert json.loads(web_file.read_text()) == sample_data


def test_sync_model_data_warns_on_missing_file(monkeypatch, tmp_path, capsys):
    """sync_model_data prints a WARN and skips files that don't exist in MODEL_DIR."""
    import build.build as build_module

    model_dir = tmp_path / "model"
    docs_dir = tmp_path / "docs"
    web_dir = tmp_path / "web"
    model_dir.mkdir()
    docs_dir.mkdir()
    web_dir.mkdir()

    # Only write archetypes.json — scenarios.json is absent
    (model_dir / "archetypes.json").write_text(json.dumps({}), encoding="utf-8")

    monkeypatch.setattr(build_module, "MODEL_DIR", str(model_dir))
    monkeypatch.setattr(build_module, "DOCS_DIR", str(docs_dir))
    monkeypatch.setattr(build_module, "WEB_DIR", str(web_dir))

    sync_model_data()

    captured = capsys.readouterr()
    assert "WARN" in captured.out
    assert "scenarios.json" in captured.out
    # archetypes.json should still be copied
    assert (docs_dir / "archetypes.json").exists()
    assert not (docs_dir / "scenarios.json").exists()
