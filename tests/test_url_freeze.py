"""Tests for URL_FREEZE.md — verifies all frozen paths exist in docs/ after build."""

import os
import re

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
FREEZE_FILE = os.path.join(PROJECT_ROOT, "URL_FREEZE.md")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
CANONICAL_HOST = "https://hygoat.in/workforce-atlas"


def _parse_freeze_urls():
    with open(FREEZE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    urls = []
    table_rows = re.findall(r'^\| (https?://\S+) \| (.*?) \| (.*?) \|$', content, re.MULTILINE)
    for url, purpose, appears_in in table_rows:
        url = url.strip()
        if url.startswith(CANONICAL_HOST):
            urls.append((url, purpose.strip(), appears_in.strip()))
    return urls


def _url_to_docs_path(url):
    path = url[len(CANONICAL_HOST):]
    if "?" in path:
        path = path.split("?")[0]
    path = path.rstrip("/") or "/"
    if path == "/":
        return os.path.join(DOCS_DIR, "index.html")
    relative = path.lstrip("/")
    # A frozen URL ending in a filename (assumptions-register.csv) is a published
    # artifact, not a page directory. Only directory-style URLs get index.html.
    if os.path.splitext(relative)[1]:
        return os.path.join(DOCS_DIR, relative)
    return os.path.join(DOCS_DIR, relative, "index.html")


def test_url_freeze_file_exists():
    assert os.path.exists(FREEZE_FILE), f"URL_FREEZE.md must exist at {FREEZE_FILE}"


def test_url_freeze_table_has_entries():
    urls = _parse_freeze_urls()
    assert len(urls) > 0, "URL_FREEZE.md must contain canonical URL table entries"


def test_all_frozen_paths_exist_in_docs():
    urls = _parse_freeze_urls()
    missing = []
    for url, purpose, _ in urls:
        docs_path = _url_to_docs_path(url)
        if not os.path.exists(docs_path):
            missing.append(f"  {url} -> expected {docs_path}")
    assert len(missing) == 0, (
        f"URL_FREEZE.md paths not found in docs/ after build:\n" + "\n".join(missing)
    )


def test_atlas_root_path_exists():
    root_path = os.path.join(DOCS_DIR, "index.html")
    assert os.path.exists(root_path), f"Atlas root must exist at {root_path}"


def test_methodology_path_exists():
    meth_path = os.path.join(DOCS_DIR, "methodology", "index.html")
    assert os.path.exists(meth_path), f"Methodology page must exist at {meth_path}"


def test_about_path_exists():
    about_path = os.path.join(DOCS_DIR, "about", "index.html")
    assert os.path.exists(about_path), f"About page must exist at {about_path}"
