"""Tests for RUNBOOK.md — verifies all required sections are present."""

import os
import re

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
RUNBOOK_FILE = os.path.join(PROJECT_ROOT, "RUNBOOK.md")

REQUIRED_SECTIONS = [
    "clone",
    "build",
    "deploy",
    "rollback",
    "domain",
    "troubleshooting",
]


def _parse_h2_headers():
    with open(RUNBOOK_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    return set(
        match.strip().lower()
        for match in re.findall(r'^## \d*\.?\s*(.+)$', content, re.MULTILINE)
    )


def test_runbook_file_exists():
    assert os.path.exists(RUNBOOK_FILE), f"RUNBOOK.md must exist at {RUNBOOK_FILE}"


def test_runbook_required_sections_present():
    headers = _parse_h2_headers()
    for section in REQUIRED_SECTIONS:
        found = any(section in h or h.startswith(section) for h in headers)
        assert found, (
            f"RUNBOOK.md is missing required section: '{section}'. "
            f"Found sections: {sorted(headers)}"
        )
