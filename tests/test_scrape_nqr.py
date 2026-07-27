"""Fixture-based tests for the NQR qualification-page parser (no live network)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrape import scrape_nqr

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def test_parse_qualification_detail_happy_path():
    html = _load("nqr_qualification_1284.html")
    record = scrape_nqr.parse_qualification_detail(html, "1284", 18)

    assert record["title"] == "Line Patrolling Man (Oil  Gas)"
    assert record["nqr_code"] == "2022/HYC/HSSCI/06782"
    assert record["sector"] == "Hydrocarbon"
    assert record["nsqf_level"] == 3
    assert record["hours_min"] == 330
    assert record["hours_max"] == 330
    assert record["theory_hours"] == 90
    assert record["practical_hours"] == 150

    assert len(record["nos"]) == 4
    first = record["nos"][0]
    assert first["nos_code"] == "HYC/N6401"
    assert first["mandatory_optional"] == "Mandatory"
    assert first["hours"] == 168
    assert first["credits"] == 5.6
    assert first["level"] == 3


def test_parse_qualification_detail_decimal_nsqf_level():
    """Regression: NSQF half-levels (5.5, 4.5, ...) are real and must not be dropped
    by an integer-only level regex -- this bit the live scrape (96/295 records)."""
    html = _load("nqr_qualification_4305.html")
    record = scrape_nqr.parse_qualification_detail(html, "4305", 18)

    assert record["nsqf_level"] == 5.5
    assert record["nos"][0]["level"] == 5.5
    assert record["nos"][0]["credits"] == 13.0


def test_parse_qualification_detail_missing_nsqf_level():
    """Fixture is nqr_qualification_1284.html with the Level <li> block removed --
    simulates a qualification page where NSQF level is genuinely absent."""
    html = _load("nqr_qualification_missing_level.html")
    record = scrape_nqr.parse_qualification_detail(html, "1284", 18)

    assert record["nsqf_level"] is None
    # The rest of the page must still parse -- a missing field must not cascade.
    assert record["title"] == "Line Patrolling Man (Oil  Gas)"
    assert record["sector"] == "Hydrocarbon"
    assert len(record["nos"]) == 4


def test_parse_qualification_detail_no_nos_table():
    """Real page (10907) that renders only the entry-criteria table, no NOS table."""
    html = _load("nqr_qualification_no_nos_table.html")
    record = scrape_nqr.parse_qualification_detail(html, "10907", 7)

    assert record["nsqf_level"] == 3.5
    assert record["nos"] == []


def test_extract_csrf_token_from_sector_page():
    html = _load("nqr_sector_page.html")
    token = scrape_nqr.extract_csrf_token(html)

    assert token == "W0LritFisi932LiP92XxMtZC0B1QiIZ2Djn68asf"


def test_extract_csrf_token_missing_returns_none():
    token = scrape_nqr.extract_csrf_token("<html><body>no meta tag here</body></html>")

    assert token is None
