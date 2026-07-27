"""Generate QR-code assets for WHS Rotterdam 2026.

Reads the canonical atlas root URL from URL_FREEZE.md (so QR and freeze file
cannot drift). Produces:
  - assets/qr-workforce-atlas.svg    (vector, preferred)
  - assets/qr-workforce-atlas-1024.png (1024x1024, 300dpi-equivalent)

QR parameters:
  - Error correction: level Q (25%)
  - Quiet zone: 4 modules minimum
"""

import argparse
import os
import re
import sys

import qrcode
from qrcode.image.svg import SvgPathImage
from qrcode.image.styledpil import StyledPilImage


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
FREEZE_FILE = os.path.join(PROJECT_ROOT, "URL_FREEZE.md")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
SVG_NAME = "qr-workforce-atlas.svg"
PNG_NAME = "qr-workforce-atlas-1024.png"
SVG_OUT = os.path.join(ASSETS_DIR, SVG_NAME)
PNG_OUT = os.path.join(ASSETS_DIR, PNG_NAME)

ATLAS_HOST = "https://hygoat.in/workforce-atlas"


def read_canonical_url():
    with open(FREEZE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for match in re.finditer(r'^\| (https://[^\s|]+\S) \| Atlas root \|', content, re.MULTILINE):
        return match.group(1).strip()
    raise SystemExit("ERROR: Could not find Atlas root URL in URL_FREEZE.md")


def generate(output_dir=ASSETS_DIR):
    """Write both QR assets into output_dir. Returns (svg_path, png_path)."""
    url = read_canonical_url()
    print(f"Canonical URL from URL_FREEZE.md: {url}")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    os.makedirs(output_dir, exist_ok=True)
    svg_out = os.path.join(output_dir, SVG_NAME)
    png_out = os.path.join(output_dir, PNG_NAME)

    img_svg = qr.make_image(image_factory=SvgPathImage)
    img_svg.save(svg_out)
    print(f"Written: {svg_out}")

    img_png = qr.make_image(
        image_factory=StyledPilImage,
        fill_color="black",
        back_color="white",
    )
    img_png = img_png.resize((1024, 1024))
    img_png.save(png_out, "PNG")
    print(f"Written: {png_out}")

    return svg_out, png_out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=ASSETS_DIR,
        help=(
            "Directory to write the QR assets into. Defaults to assets/. "
            "Tests pass a temporary directory so a test run never rewrites "
            "the checked-in assets."
        ),
    )
    args = parser.parse_args()
    generate(args.output_dir)
