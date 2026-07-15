"""Regression tests for fail-closed NCS sector pagination."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrape import scrape_ncs


def _full_page_html():
    rows = [
        {
            "Title": f"Occupation {index}",
            "NCO_x0020_Code": f"7212.{index:04d}",
            "Industry_x002F_Sector_x0028_s_x0": "Power",
            "ID": str(index),
        }
        for index in range(scrape_ncs.SHAREPOINT_PAGE_SIZE)
    ]
    return "var WPQ2ListData = " + json.dumps({"Row": rows}) + ";var WPQ2SchemaData"


def test_fetch_sector_discards_partial_results_when_a_later_page_fails(monkeypatch):
    responses = iter([_full_page_html(), None])
    monkeypatch.setattr(scrape_ncs, "fetch_html", lambda url, ssl_ctx: next(responses))

    result = scrape_ncs.fetch_sector("Power", object())

    assert result == ([], False)
