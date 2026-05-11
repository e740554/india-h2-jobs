"""Tests for QR-code asset generation (DR-4)."""

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
GENERATE_SCRIPT = os.path.join(SCRIPTS_DIR, "generate_qr.py")
SVG_PATH = os.path.join(ASSETS_DIR, "qr-workforce-atlas.svg")
PNG_PATH = os.path.join(ASSETS_DIR, "qr-workforce-atlas-1024.png")


def test_qr_script_exists():
    assert os.path.exists(GENERATE_SCRIPT), f"Expected {GENERATE_SCRIPT} to exist"


def test_qr_generation_produces_svg():
    subprocess.run(
        [sys.executable, GENERATE_SCRIPT],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    ).check_returncode()
    assert os.path.exists(SVG_PATH), f"Expected {SVG_PATH} after generation"


def test_qr_generation_produces_png():
    assert os.path.exists(PNG_PATH), f"Expected {PNG_PATH} after generation"


def test_qr_png_minimum_size():
    assert os.path.exists(PNG_PATH), f"PNG not found at {PNG_PATH}"
    from PIL import Image
    img = Image.open(PNG_PATH)
    w, h = img.size
    assert w >= 1024, f"PNG width {w} < 1024"
    assert h >= 1024, f"PNG height {h} < 1024"


def test_qr_svg_viewbox_is_square():
    assert os.path.exists(SVG_PATH), f"SVG not found at {SVG_PATH}"
    with open(SVG_PATH, "r", encoding="utf-8") as f:
        svg = f.read()
    ns = {"svg": "http://www.w3.org/2000/svg"}
    root = ET.fromstring(svg)
    viewbox = root.attrib.get("viewBox") or root.attrib.get("viewbox")
    assert viewbox is not None, "SVG must have a viewBox attribute"
    parts = viewbox.split()
    assert len(parts) == 4, f"viewBox must have 4 parts, got {viewbox}"
    vb_w = int(float(parts[2]))
    vb_h = int(float(parts[3]))
    assert vb_w == vb_h, f"SVG viewBox must be square, got {vb_w}x{vb_h}"
