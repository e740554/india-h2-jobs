"""Generate QR-code assets for WHS Rotterdam 2026.

Reads the canonical atlas root URL from URL_FREEZE.md (so QR and freeze file
cannot drift). Produces:
  - assets/qr-workforce-atlas.svg    (vector, preferred)
  - assets/qr-workforce-atlas-1024.png (1024x1024, 300dpi-equivalent)

QR parameters:
  - Error correction: level Q (25%)
  - Quiet zone: 4 modules minimum
"""

import os
import re
import sys

import qrcode
from qrcode.image.svg import SvgPathImage
from qrcode.image.styledpil import StyledPilImage


PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
FREEZE_FILE = os.path.join(PROJECT_ROOT, "URL_FREEZE.md")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
SVG_OUT = os.path.join(ASSETS_DIR, "qr-workforce-atlas.svg")
PNG_OUT = os.path.join(ASSETS_DIR, "qr-workforce-atlas-1024.png")

ATLAS_HOST = "https://hygoat.in/workforce-atlas"


def read_canonical_url():
    with open(FREEZE_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    for match in re.finditer(r'^\| (https://[^\s|]+\S) \| Atlas root \|', content, re.MULTILINE):
        return match.group(1).strip()
    raise SystemExit("ERROR: Could not find Atlas root URL in URL_FREEZE.md")


def generate():
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

    os.makedirs(ASSETS_DIR, exist_ok=True)

    img_svg = qr.make_image(image_factory=SvgPathImage)
    img_svg.save(SVG_OUT)
    print(f"Written: {SVG_OUT}")

    img_png = qr.make_image(
        image_factory=StyledPilImage,
        fill_color="black",
        back_color="white",
    )
    img_png = img_png.resize((1024, 1024))
    img_png.save(PNG_OUT, "PNG")
    print(f"Written: {PNG_OUT}")


if __name__ == "__main__":
    generate()
