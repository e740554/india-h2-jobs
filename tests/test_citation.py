"""Tests for CITATION.cff staying in sync with VERSION and CHANGELOG.md."""

import os
import re

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
VERSION_FILE = os.path.join(PROJECT_ROOT, "VERSION")
CHANGELOG_FILE = os.path.join(PROJECT_ROOT, "CHANGELOG.md")
CITATION_FILE = os.path.join(PROJECT_ROOT, "CITATION.cff")


def _read_version():
    with open(VERSION_FILE, encoding="utf-8") as f:
        return f.read().strip()


def _read_citation():
    with open(CITATION_FILE, encoding="utf-8") as f:
        return f.read()


def test_citation_version_matches_version_file():
    version = _read_version()
    citation = _read_citation()
    match = re.search(r"^version:\s*(\S+)$", citation, flags=re.MULTILINE)
    assert match, "CITATION.cff must have a top-level version: field"
    assert match.group(1) == version, (
        f"CITATION.cff version ({match.group(1)}) does not match VERSION ({version})"
    )


def test_citation_date_released_matches_changelog():
    version = _read_version()
    with open(CHANGELOG_FILE, encoding="utf-8") as f:
        changelog = f.read()
    changelog_match = re.search(
        rf"^## \[{re.escape(version)}\] - (\d{{4}}-\d{{2}}-\d{{2}})$",
        changelog,
        flags=re.MULTILINE,
    )
    assert changelog_match, f"No release date found for VERSION {version} in CHANGELOG.md"

    citation = _read_citation()
    citation_match = re.search(r"^date-released:\s*(\S+)$", citation, flags=re.MULTILINE)
    assert citation_match, "CITATION.cff must have a top-level date-released: field"
    assert citation_match.group(1) == changelog_match.group(1), (
        f"CITATION.cff date-released ({citation_match.group(1)}) does not match "
        f"CHANGELOG.md ({changelog_match.group(1)}) for version {version}"
    )
