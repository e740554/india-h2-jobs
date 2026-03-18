"""Parse scraped NCS data into a clean occupation dataset.

Reads the raw NCS JSON (from scrape_ncs.py) and produces a normalized
list of occupations with consistent fields.

PLFS data integration is deferred until PDF table extraction is implemented.

Usage:
    python parse/parse_occupations.py
"""

import json
import os
import re

RAW_NCS = os.path.join(os.path.dirname(__file__), "..", "scrape", "raw", "ncs", "ncs_occupations.json")
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "parse", "parsed_occupations.json")


def slugify(title: str) -> str:
    """Convert occupation title to URL-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


def make_ncs_id(nco_code: str, sp_id: int | str) -> str:
    """Generate a canonical NCS ID from NCO code.

    Uses the NCO-2015 code as-is (e.g., '3113.0202' → 'NCS-3113.0202').
    Falls back to SharePoint ID if no NCO code available.
    """
    if nco_code and nco_code.strip():
        return f"NCS-{nco_code.strip()}"
    return f"NCS-SP-{sp_id}"


def parse_ncs(raw_path: str) -> list[dict]:
    """Parse raw NCS JSON into normalized occupation records."""
    with open(raw_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    occupations = []
    seen_ids = set()

    for record in raw:
        title = record.get("title", "").strip()
        nco_code = record.get("nco_code", "")
        sector = record.get("sector", "Unknown")
        sp_id = record.get("sp_id", "")

        if not title:
            continue

        ncs_id = make_ncs_id(nco_code, sp_id)

        # Deduplicate by ID
        if ncs_id in seen_ids:
            continue
        seen_ids.add(ncs_id)

        occupations.append({
            "id": ncs_id,
            "slug": slugify(title),
            "title": title,
            "sector": sector,
            "nco_code": nco_code,
            "employment": None,       # PLFS — to be filled
            "median_wage_inr": None,   # PLFS — to be filled
            "education_req": None,     # Not available from list view
            "formal_sector_pct": None, # PLFS — to be filled
            "source_ncs": True,
            "source_plfs": False,
            "source_ncvet": False,
        })

    return occupations


def main():
    if not os.path.exists(RAW_NCS):
        print(f"ERROR: Raw NCS data not found at {RAW_NCS}")
        print("Run 'python scrape/scrape_ncs.py' first.")
        return

    print(f"Parsing NCS data from: {RAW_NCS}")
    occupations = parse_ncs(RAW_NCS)
    print(f"Parsed {len(occupations)} unique occupations")

    # Sector breakdown
    sectors = {}
    for occ in occupations:
        s = occ["sector"]
        sectors[s] = sectors.get(s, 0) + 1
    print(f"\nSectors: {len(sectors)}")
    for s, count in sorted(sectors.items(), key=lambda x: -x[1])[:10]:
        print(f"  {s}: {count}")

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(occupations, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {OUTPUT}")


if __name__ == "__main__":
    main()
