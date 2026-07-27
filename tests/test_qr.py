"""Tests for QR-code asset generation (DR-4).

Generation tests write into a pytest tmp_path. They must never rewrite the
checked-in assets: a `pytest` run that dirties the working tree produces
spurious diffs, and the `qrcode` SVG writer emits slightly different attribute
spacing across library versions, so the noise is not even a real change.

Asset tests read `assets/` read-only and assert that what is committed is valid
and still encodes the frozen canonical URL.
"""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
GENERATE_SCRIPT = os.path.join(SCRIPTS_DIR, "generate_qr.py")
SVG_NAME = "qr-workforce-atlas.svg"
PNG_NAME = "qr-workforce-atlas-1024.png"
SVG_PATH = os.path.join(ASSETS_DIR, SVG_NAME)
PNG_PATH = os.path.join(ASSETS_DIR, PNG_NAME)

SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def _run_generator(output_dir):
    """Run the generator into output_dir and return (svg_path, png_path)."""
    subprocess.run(
        [sys.executable, GENERATE_SCRIPT, "--output-dir", str(output_dir)],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    ).check_returncode()
    return os.path.join(str(output_dir), SVG_NAME), os.path.join(str(output_dir), PNG_NAME)


def _svg_path_geometry(svg_text):
    """Return the QR module path data.

    The `d` attribute is the encoded payload as geometry. Comparing it ignores
    attribute-formatting differences between `qrcode` versions, which are
    cosmetic and would otherwise make any comparison flaky.
    """
    root = ET.fromstring(svg_text)
    path = root.find(".//svg:path", SVG_NS)
    assert path is not None, "SVG must contain a <path> element"
    return path.attrib["d"]


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_qr_script_exists():
    assert os.path.exists(GENERATE_SCRIPT), f"Expected {GENERATE_SCRIPT} to exist"


def test_generator_writes_both_assets(tmp_path):
    svg_out, png_out = _run_generator(tmp_path)
    assert os.path.exists(svg_out), f"Generator did not write {svg_out}"
    assert os.path.exists(png_out), f"Generator did not write {png_out}"


def test_generator_does_not_touch_checked_in_assets(tmp_path):
    """Regression guard: generating elsewhere must leave assets/ untouched."""
    before = (_read(SVG_PATH), os.path.getsize(PNG_PATH))
    _run_generator(tmp_path)
    after = (_read(SVG_PATH), os.path.getsize(PNG_PATH))
    assert before == after, (
        "Running the generator modified the checked-in QR assets. It must only "
        "write into the directory given by --output-dir."
    )


def test_committed_svg_viewbox_is_square():
    root = ET.fromstring(_read(SVG_PATH))
    viewbox = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    assert viewbox is not None, "SVG must have a viewBox attribute"
    parts = viewbox.split()
    assert len(parts) == 4, f"viewBox must have 4 parts, got {viewbox}"
    vb_w = int(float(parts[2]))
    vb_h = int(float(parts[3]))
    assert vb_w == vb_h, f"SVG viewBox must be square, got {vb_w}x{vb_h}"


def test_committed_png_minimum_size():
    assert os.path.exists(PNG_PATH), f"PNG not found at {PNG_PATH}"
    from PIL import Image
    with Image.open(PNG_PATH) as img:
        w, h = img.size
    assert w >= 1024, f"PNG width {w} < 1024"
    assert h >= 1024, f"PNG height {h} < 1024"


def test_committed_svg_still_encodes_the_frozen_url(tmp_path):
    """Catch a stale QR after URL_FREEZE.md changes.

    Print materials and the conference QR depend on the committed asset, not on
    whatever a local run would produce, so drift has to fail the build.
    """
    fresh_svg, _ = _run_generator(tmp_path)
    assert _svg_path_geometry(_read(SVG_PATH)) == _svg_path_geometry(_read(fresh_svg)), (
        "The committed QR no longer matches the Atlas root URL in URL_FREEZE.md. "
        "Regenerate with: python scripts/generate_qr.py"
    )
