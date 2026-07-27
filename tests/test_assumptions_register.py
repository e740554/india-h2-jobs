"""Tests for build/build.py's write_assumptions_register()."""

import csv
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from build.build import write_assumptions_register, ASSUMPTIONS_CSV_FIELDS
from model.compute import load_archetypes
from model.pathways import load_pathways


def _read_register(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_header_matches_column_list(tmp_path):
    output_path = write_assumptions_register(str(tmp_path))

    with open(output_path, encoding="utf-8", newline="") as f:
        header = next(csv.reader(f))

    assert header == ASSUMPTIONS_CSV_FIELDS


def test_every_staffing_coefficient_appears_exactly_once(tmp_path):
    output_path = write_assumptions_register(str(tmp_path))
    rows = _read_register(output_path)

    staffing_rows = [r for r in rows if r["component"] == "staffing_coefficient"]
    csv_keys = {(r["item_id"], r["phase"]): float(r["value"]) for r in staffing_rows}

    archetypes = load_archetypes()
    expected_keys = {}
    for arch in archetypes:
        for coeff in arch["coefficients"]:
            key = (f"{arch['id']}:{coeff['nco_group']}", coeff["phase"])
            expected_keys[key] = float(coeff["headcount_per_unit"])

    assert len(staffing_rows) == len(expected_keys)
    assert set(csv_keys.keys()) == set(expected_keys.keys())
    for key, value in expected_keys.items():
        assert csv_keys[key] == value


def test_every_pathway_contributes_exactly_three_rows(tmp_path):
    output_path = write_assumptions_register(str(tmp_path))
    rows = _read_register(output_path)

    pathway_rows = [r for r in rows if r["component"] == "pathway"]
    counts = {}
    for row in pathway_rows:
        counts[row["item_id"]] = counts.get(row["item_id"], 0) + 1

    pathways = load_pathways()["pathways"]
    assert len(counts) == len(pathways)
    assert all(count == 3 for count in counts.values())


def test_no_empty_source_type_cells(tmp_path):
    output_path = write_assumptions_register(str(tmp_path))
    rows = _read_register(output_path)

    assert len(rows) > 100
    assert all(row["source_type"] for row in rows)


def test_component_item_id_parameter_phase_is_unique(tmp_path):
    output_path = write_assumptions_register(str(tmp_path))
    rows = _read_register(output_path)

    keys = [(r["component"], r["item_id"], r["parameter"], r["phase"]) for r in rows]
    assert len(keys) == len(set(keys))


def test_writer_is_deterministic(tmp_path):
    first = write_assumptions_register(str(tmp_path / "first"))
    second = write_assumptions_register(str(tmp_path / "second"))

    with open(first, "rb") as f:
        first_bytes = f.read()
    with open(second, "rb") as f:
        second_bytes = f.read()

    assert first_bytes == second_bytes
