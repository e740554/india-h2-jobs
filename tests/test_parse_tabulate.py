"""Focused fixtures for the NCS parse and CSV tabulation stages."""

import csv
import json

from parse.parse_occupations import parse_ncs, slugify
from tabulate import tabulate as tabulate_module


def test_parse_ncs_normalizes_records_deduplicates_and_falls_back_to_sharepoint_id(tmp_path):
    raw_path = tmp_path / "ncs_occupations.json"
    raw_path.write_text(
        json.dumps([
            {"title": "  Electrolyser Technician  ", "nco_code": "3113.0202", "sector": "Power", "sp_id": "1"},
            {"title": "Duplicate NCO", "nco_code": "3113.0202", "sector": "Power", "sp_id": "2"},
            {"title": "", "nco_code": "9999", "sector": "Power", "sp_id": "3"},
            {"title": "Hydrogen Safety", "nco_code": "", "sector": "Safety", "sp_id": "4"},
        ]),
        encoding="utf-8",
    )

    occupations = parse_ncs(str(raw_path))

    assert [occupation["id"] for occupation in occupations] == ["NCS-3113.0202", "NCS-SP-4"]
    assert occupations[0]["slug"] == "electrolyser-technician"
    assert occupations[0]["source_ncs"] is True
    assert occupations[1]["sector"] == "Safety"


def test_slugify_produces_stable_url_safe_titles():
    assert slugify("  H2 / Plant-Operator! ") == "h2-plant-operator"


def test_tabulate_writes_the_declared_csv_shape(monkeypatch, tmp_path):
    parsed_path = tmp_path / "parsed_occupations.json"
    output_path = tmp_path / "occupations.csv"
    parsed_path.write_text(
        json.dumps([{
            "id": "NCS-3113.0202",
            "slug": "electrolyser-technician",
            "title": "Electrolyser Technician",
            "sector": "Power",
            "nco_code": "3113.0202",
            "source_ncs": True,
            "unexpected": "not exported",
        }]),
        encoding="utf-8",
    )
    monkeypatch.setattr(tabulate_module, "PARSED_FILE", str(parsed_path))
    monkeypatch.setattr(tabulate_module, "OUTPUT_CSV", str(output_path))

    tabulate_module.main()

    with open(output_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert reader.fieldnames == tabulate_module.CSV_FIELDS
    assert rows == [{
        "id": "NCS-3113.0202",
        "slug": "electrolyser-technician",
        "title": "Electrolyser Technician",
        "sector": "Power",
        "nco_code": "3113.0202",
        "employment": "",
        "median_wage_inr": "",
        "education_req": "",
        "formal_sector_pct": "",
        "source_ncs": "True",
        "source_plfs": "",
        "source_ncvet": "",
    }]
