"""Merge occupations + scores into final occupations.json and web assets.

Reads occupations.csv and scores.json, computes upskill paths and workforce gap,
writes occupations.json, CSV exports, and generates web/main.js from template.

Usage:
    python build/build.py                          # Default (empty base URL)
    python build/build.py --base-url "/india-h2-jobs"  # GitHub Pages
    python build/build.py --base-url "/workforce-atlas" # HyGOAT
"""

import argparse
import csv
import json
import os
from datetime import date

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
OCCUPATIONS_CSV = os.path.join(PROJECT_ROOT, "occupations.csv")
SCORES_FILE = os.path.join(PROJECT_ROOT, "scores.json")
OUTPUT_JSON = os.path.join(PROJECT_ROOT, "occupations.json")
OUTPUT_CSV_FULL = os.path.join(PROJECT_ROOT, "occupations.csv")
OUTPUT_CSV_H2 = os.path.join(PROJECT_ROOT, "h2-ready-occupations.csv")
TEMPLATE_FILE = os.path.join(PROJECT_ROOT, "web", "main.js.template")
OUTPUT_JS = os.path.join(PROJECT_ROOT, "web", "main.js")

# Workforce gap formula inputs (spec section 3)
NGHM_TARGET_MMT = 5
LABOUR_INTENSITY = 500_000  # jobs per MMT (IEA Global Hydrogen Review 2023)
H2_ADJACENCY_THRESHOLD = 7.0


def load_occupations() -> list[dict]:
    """Load occupations from CSV."""
    occs = []
    with open(OCCUPATIONS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            for field in ["employment", "median_wage_inr", "formal_sector_pct"]:
                val = row.get(field, "")
                row[field] = int(float(val)) if val and val not in ("", "None") else None
            # Convert boolean fields
            for field in ["source_ncs", "source_plfs", "source_ncvet"]:
                row[field] = row.get(field, "False") == "True"
            occs.append(row)
    return occs


def load_scores() -> dict:
    """Load scores from JSON."""
    if not os.path.exists(SCORES_FILE):
        return {}
    with open(SCORES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_scores(occupations: list[dict], scores: dict) -> list[dict]:
    """Merge score data into occupation records."""
    for occ in occupations:
        occ_id = occ["id"]
        occ_scores = {}
        if occ_id in scores:
            for dim, data in scores[occ_id].items():
                if isinstance(data, dict) and "score" in data:
                    occ_scores[dim] = data["score"]
                else:
                    occ_scores[dim] = None
        occ["scores"] = occ_scores
    return occupations


def compute_upskill_paths(occupations: list[dict]) -> list[dict]:
    """Derive top 5 upskill paths per occupation (same sector, ranked by h2_adjacency + transition_demand)."""
    by_sector = {}
    for occ in occupations:
        s = occ.get("sector", "Unknown")
        by_sector.setdefault(s, []).append(occ)

    for occ in occupations:
        sector = occ.get("sector", "Unknown")
        candidates = by_sector.get(sector, [])
        scored = []
        for c in candidates:
            if c["id"] == occ["id"]:
                continue
            h2 = c.get("scores", {}).get("h2_adjacency")
            td = c.get("scores", {}).get("transition_demand")
            if h2 is not None and td is not None:
                scored.append((c["id"], h2 + td))
        scored.sort(key=lambda x: -x[1])
        occ["upskill_paths"] = [s[0] for s in scored[:5]]

    return occupations


def compute_workforce_gap(occupations: list[dict]) -> int:
    """Compute workforce gap per spec section 3 formula."""
    h2_workforce = 0
    for occ in occupations:
        h2_score = occ.get("scores", {}).get("h2_adjacency")
        emp = occ.get("employment")
        if h2_score is not None and h2_score >= H2_ADJACENCY_THRESHOLD and emp:
            h2_workforce += emp
    gap = (NGHM_TARGET_MMT * LABOUR_INTENSITY) - h2_workforce
    return max(0, gap)


def compute_summary_metrics(occupations: list[dict]) -> dict:
    """Compute 3 headline metrics for summary bar."""
    h2_ready = 0
    fast_upskill = 0
    for occ in occupations:
        scores = occ.get("scores", {})
        h2 = scores.get("h2_adjacency")
        td = scores.get("transition_demand")
        st = scores.get("skill_transferability")

        if h2 is not None and h2 >= H2_ADJACENCY_THRESHOLD:
            h2_ready += 1
        if st is not None and td is not None and st >= 7.0 and td >= 7.0:
            fast_upskill += 1

    return {
        "h2_ready_occupations": h2_ready,
        "workforce_gap_2030": compute_workforce_gap(occupations),
        "fast_upskill_paths": fast_upskill,
    }


def write_h2_csv(occupations: list[dict]):
    """Write filtered CSV of H2-ready occupations."""
    h2_occs = [
        occ for occ in occupations
        if occ.get("scores", {}).get("h2_adjacency") is not None
        and occ["scores"]["h2_adjacency"] >= H2_ADJACENCY_THRESHOLD
    ]

    fields = ["id", "slug", "title", "sector", "nco_code", "employment",
              "median_wage_inr", "education_req", "formal_sector_pct",
              "h2_adjacency", "transition_demand", "skill_transferability",
              "digital_automation_exposure", "formalization_rate", "scarcity_risk"]

    with open(OUTPUT_CSV_H2, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for occ in h2_occs:
            row = {k: occ.get(k) for k in fields[:9]}
            for dim in fields[9:]:
                row[dim] = occ.get("scores", {}).get(dim)
            writer.writerow(row)

    print(f"H2-ready CSV: {len(h2_occs)} occupations -> {OUTPUT_CSV_H2}")


def inject_base_url(base_url: str):
    """Generate web/main.js from template with BASE_URL injected."""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"WARN: Template not found at {TEMPLATE_FILE}, skipping JS generation")
        return
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    main_js = template.replace("__BASE_URL__", base_url)
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(main_js)
    print(f"Generated: {OUTPUT_JS} (base_url={base_url!r})")


def main():
    parser = argparse.ArgumentParser(description="Build occupations.json and web assets")
    parser.add_argument("--base-url", type=str, default="", help="Base URL for asset paths")
    args = parser.parse_args()

    # Load data
    occupations = load_occupations()
    scores = load_scores()
    print(f"Loaded {len(occupations)} occupations, {len(scores)} scored")

    # Merge
    occupations = merge_scores(occupations, scores)

    # Compute derived fields
    occupations = compute_upskill_paths(occupations)
    metrics = compute_summary_metrics(occupations)

    # Count scored
    scored_count = sum(1 for occ in occupations if occ.get("scores"))

    # Build output JSON
    output = {
        "dataset_version": "1.0",
        "last_updated": date.today().isoformat(),
        "total_occupations": len(occupations),
        "scored_occupations": scored_count,
        "summary": metrics,
        "occupations": occupations,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Written: {OUTPUT_JSON} ({len(occupations)} occupations)")

    # Summary
    print(f"\nSummary metrics:")
    print(f"  H2-Ready Occupations: {metrics['h2_ready_occupations']}")
    print(f"  Workforce Gap by 2030: {metrics['workforce_gap_2030']:,}")
    print(f"  Fast Upskill Paths: {metrics['fast_upskill_paths']}")

    # Write H2 CSV
    write_h2_csv(occupations)

    # Copy occupations.json to web/ for serving
    import shutil
    web_json = os.path.join(PROJECT_ROOT, "web", "occupations.json")
    shutil.copy2(OUTPUT_JSON, web_json)
    print(f"Copied: {web_json}")

    # Copy CSV exports to web/ for download
    for csv_file in [OUTPUT_CSV_H2]:
        web_csv = os.path.join(PROJECT_ROOT, "web", os.path.basename(csv_file))
        shutil.copy2(csv_file, web_csv)

    # Generate JS
    inject_base_url(args.base_url)


if __name__ == "__main__":
    main()
