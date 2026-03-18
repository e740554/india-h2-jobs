"""Convert parsed occupations JSON to occupations.csv.

Reads parsed_occupations.json and writes a flat CSV with all fields.

Usage:
    python tabulate/tabulate.py
"""

import csv
import json
import os

PARSED_FILE = os.path.join(os.path.dirname(__file__), "..", "parse", "parsed_occupations.json")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "occupations.csv")

CSV_FIELDS = [
    "id", "slug", "title", "sector", "nco_code",
    "employment", "median_wage_inr", "education_req", "formal_sector_pct",
    "source_ncs", "source_plfs", "source_ncvet",
]


def main():
    if not os.path.exists(PARSED_FILE):
        print(f"ERROR: Parsed data not found at {PARSED_FILE}")
        print("Run 'python parse/parse_occupations.py' first.")
        return

    with open(PARSED_FILE, "r", encoding="utf-8") as f:
        occupations = json.load(f)

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for occ in occupations:
            writer.writerow(occ)

    print(f"Written {len(occupations)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
