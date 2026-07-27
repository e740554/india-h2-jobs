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
import re
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from model.clusters import load_clusters, validate_cluster_affinities
from model.compute import load_archetypes, sanitize_csv_value
from model.pathways import load_pathways, validate_pathways
from model.supply import allocate_supply, load_supply

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
VERSION_FILE = os.path.join(PROJECT_ROOT, "VERSION")
CHANGELOG_FILE = os.path.join(PROJECT_ROOT, "CHANGELOG.md")


def load_release_metadata(version_file: str, changelog_file: str) -> tuple[str, str]:
    """Load the canonical version and its published date from release sources."""
    with open(version_file, encoding="utf-8") as f:
        version = f.read().strip()
    with open(changelog_file, encoding="utf-8") as f:
        changelog = f.read()
    match = re.search(
        rf"^## \[{re.escape(version)}\] - (\d{{4}}-\d{{2}}-\d{{2}})$",
        changelog,
        flags=re.MULTILINE,
    )
    if not match:
        raise ValueError(f"No release date found for VERSION {version} in {changelog_file}")
    return version, match.group(1)


DATASET_VERSION, DATASET_UPDATED = load_release_metadata(VERSION_FILE, CHANGELOG_FILE)
DATASET_UPDATED_LABEL = datetime.strptime(DATASET_UPDATED, "%Y-%m-%d").strftime("%B %Y")
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
MODEL_JSON_FILES = [
    "archetypes.json",
    "scenarios.json",
    "clusters.json",
    "pathways.json",
    "plfs_supply.json",
]
OCCUPATIONS_CSV = os.path.join(PROJECT_ROOT, "occupations.csv")
SCORES_FILE = os.path.join(PROJECT_ROOT, "scores.json")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
WEB_DIR = os.path.join(PROJECT_ROOT, "web")
CHUNKS_DIR = os.path.join(WEB_DIR, "_chunks")
OUTPUT_JSON = os.path.join(DOCS_DIR, "occupations.json")
OUTPUT_JSON_ALL = os.path.join(DOCS_DIR, "occupations-all.json")
OUTPUT_SCORE_DETAILS = os.path.join(DOCS_DIR, "score-details.json")
OUTPUT_CSV_H2 = os.path.join(DOCS_DIR, "h2-ready-occupations.csv")
TEMPLATE_FILE = os.path.join(WEB_DIR, "main.js.template")
STATIC_PUBLIC_FILES = [
    ".nojekyll",
    "style.css",
    "hygoat-logo.svg",
    "vendor/d3.v7.9.0.min.js",
]
# Pre-expanded blocks used as variable values in page templates.
# Kept as module-level constants so they are written once, not copy-pasted.
_MODE_TOGGLE_BLOCK = """\
      <div class="mode-toggle" id="modeToggle">
        <button class="mode-btn active" data-mode="atlas">Atlas</button>
        <button class="mode-btn" data-mode="scenario">Scenario</button>
        <button class="mode-btn" data-mode="gap">Gap</button>
      </div>"""

_DOWNLOAD_BLOCK = """\
      <div class="download-dropdown">
        <button class="btn-download" id="downloadBtn">&#x2B07; Download CSV &#x25BE;</button>
        <div class="dropdown-menu" id="downloadMenu">
          <a href="#" id="dlView">Current View Snapshot (CSV)</a>
          <a href="#" id="dlSnapshot">Full Scenario Snapshot (CSV)</a>
          <a href="#" id="dlFull">All Scored Occupations (CSV)</a>
          <a href="#" id="dlH2">H2-Ready Occupations (CSV)</a>
          <a href="#" id="dlBriefing">Briefing (print)</a>
        </div>
      </div>"""

_FOOTER_SECONDARY_ATLAS = f"""\
    <div class="footer-row footer-row-secondary"><span id="footerVersion">Dataset v{DATASET_VERSION}</span> &middot; <span id="footerDate">Last updated {DATASET_UPDATED_LABEL}</span> &middot; <a href="https://github.com/e740554/india-h2-jobs" title="View source on GitHub">GitHub</a> &middot; MIT Licence</div>"""

_FOOTER_SECONDARY_STATIC = f"""\
    <div class="footer-row footer-row-secondary">Dataset v{DATASET_VERSION} &middot; Last updated {DATASET_UPDATED_LABEL} &middot; <a href="https://github.com/e740554/india-h2-jobs" title="View source on GitHub">GitHub</a> &middot; MIT Licence</div>"""

PAGE_VARS = {
    "index.html": {
        "rel_root": ".",
        "aria_atlas": 'aria-current="page"',
        "aria_methodology": "",
        "aria_about": "",
        "mode_toggle_block": _MODE_TOGGLE_BLOCK,
        "download_block": _DOWNLOAD_BLOCK,
        "footer_secondary": _FOOTER_SECONDARY_ATLAS,
        "dataset_version": DATASET_VERSION,
        "dataset_updated_label": DATASET_UPDATED_LABEL,
    },
    "methodology/index.html": {
        "rel_root": "..",
        "aria_atlas": "",
        "aria_methodology": 'aria-current="page"',
        "aria_about": "",
        "mode_toggle_block": "",
        "download_block": "",
        "footer_secondary": _FOOTER_SECONDARY_STATIC,
        "dataset_version": DATASET_VERSION,
        "dataset_updated_label": DATASET_UPDATED_LABEL,
    },
    "about/index.html": {
        "rel_root": "..",
        "aria_atlas": "",
        "aria_methodology": "",
        "aria_about": 'aria-current="page"',
        "mode_toggle_block": "",
        "download_block": "",
        "footer_secondary": _FOOTER_SECONDARY_STATIC,
    },
}

# H2-relevant NCS sectors (12 of 49)
H2_SECTORS = [
    "Hydrocarbon",
    "Chemical and Petrochemicals",
    "Power",
    "Iron and Steel",
    "Mining",
    "Capital Goods and Manufacturing",
    "Construction",
    "Plumbing",
    "Environmental Science",
    "Electronics and HW",
    "Logistics",
    "Shipping",
]

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


def pct(count: int, total: int) -> float:
    """Return percentage with one decimal place."""
    if total == 0:
        return 0.0
    return round((count / total) * 100, 1)


def count_present(occupations: list[dict], field: str) -> int:
    """Count non-null values for a field."""
    return sum(1 for occ in occupations if occ.get(field) is not None)


def count_true(occupations: list[dict], field: str) -> int:
    """Count truthy boolean source flags."""
    return sum(1 for occ in occupations if occ.get(field) is True)


def merge_scores(occupations: list[dict], scores: dict) -> list[dict]:
    """Merge score data into occupation records, preserving rationales."""
    for occ in occupations:
        occ_id = occ["id"]
        occ_scores = {}
        occ_score_details = {}
        if occ_id in scores:
            for dim, data in scores[occ_id].items():
                if isinstance(data, dict) and "score" in data:
                    occ_scores[dim] = data["score"]
                    occ_score_details[dim] = {
                        "score": data.get("score"),
                        "rationale": data.get("rationale"),
                    }
                else:
                    occ_scores[dim] = data
                    occ_score_details[dim] = {
                        "score": data,
                        "rationale": None,
                    }
        occ["scores"] = occ_scores
        occ["score_details"] = occ_score_details
    return occupations


def extract_score_details(occupations: list[dict]) -> dict[str, dict]:
    """Detach score rationales that are only needed after a user selects a card."""
    details_by_occupation = {}
    for occupation in occupations:
        details = occupation.pop("score_details", {})
        if details:
            details_by_occupation[occupation["id"]] = details
    return details_by_occupation


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


def compute_workforce_gap(occupations: list[dict]) -> int | None:
    """Compute indicative workforce gap from PLFS subdivision-allocated supply."""
    eligible = [
        occ for occ in occupations
        if occ.get("scores", {}).get("h2_adjacency") is not None
        and occ["scores"]["h2_adjacency"] >= H2_ADJACENCY_THRESHOLD
    ]

    if not eligible:
        return None

    if any(occ.get("supply_estimate") is None for occ in eligible):
        return None

    h2_workforce = sum((occ.get("supply_estimate") or 0) for occ in eligible)
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

    workforce_gap = compute_workforce_gap(occupations)
    return {
        "h2_ready_occupations": h2_ready,
        "workforce_gap_2030": workforce_gap,
        "workforce_gap_supported": workforce_gap is not None,
        "fast_upskill_paths": fast_upskill,
    }


def compute_data_quality(occupations: list[dict]) -> dict:
    """Compute data coverage and source status for the current dataset view."""
    total = len(occupations)
    coverage = {}
    for field in ["employment", "median_wage_inr", "formal_sector_pct"]:
        count = count_present(occupations, field)
        coverage[field] = {
            "count": count,
            "total": total,
            "pct": pct(count, total),
        }

    source_counts = {}
    for source_key, source_name in [
        ("source_ncs", "ncs"),
        ("source_plfs", "plfs"),
        ("source_ncvet", "ncvet"),
    ]:
        count = count_true(occupations, source_key)
        source_counts[source_name] = {
            "count": count,
            "total": total,
            "pct": pct(count, total),
        }

    labour_market_fields = [coverage[field]["count"] for field in ["employment", "median_wage_inr", "formal_sector_pct"]]
    if all(count == 0 for count in labour_market_fields):
        labour_market_status = "pending"
    elif all(count == total for count in labour_market_fields):
        labour_market_status = "complete"
    else:
        labour_market_status = "partial"

    h2_ready = [
        occ for occ in occupations
        if occ.get("scores", {}).get("h2_adjacency") is not None
        and occ["scores"]["h2_adjacency"] >= H2_ADJACENCY_THRESHOLD
    ]
    h2_ready_employment_count = count_present(h2_ready, "employment")
    h2_ready_supply_count = count_present(h2_ready, "supply_estimate")
    workforce_gap_supported = compute_workforce_gap(occupations) is not None

    notes = []
    if labour_market_status != "complete":
        notes.append("Current build is a scored occupation atlas; labour-market joins are still incomplete.")
    if not workforce_gap_supported:
        notes.append("Workforce gap by 2030 is hidden until H2-ready occupations have PLFS subdivision supply coverage.")
    else:
        notes.append("Workforce gap uses PLFS subdivision-allocated supply estimates; indicative, not occupation-observed.")

    return {
        "labour_market_status": labour_market_status,
        "workforce_gap_supported": workforce_gap_supported,
        "coverage": coverage,
        "source_counts": source_counts,
        "h2_ready_employment_coverage": {
            "count": h2_ready_employment_count,
            "total": len(h2_ready),
            "pct": pct(h2_ready_employment_count, len(h2_ready)),
        },
        "h2_ready_supply_coverage": {
            "count": h2_ready_supply_count,
            "total": len(h2_ready),
            "pct": pct(h2_ready_supply_count, len(h2_ready)),
        },
        "notes": notes,
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
              "supply_estimate", "supply_source", "supply_nco_subdivision",
              "supply_sample_count",
              "h2_adjacency", "transition_demand", "skill_transferability",
              "digital_automation_exposure", "formalization_rate", "scarcity_risk"]

    with open(OUTPUT_CSV_H2, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for occ in h2_occs:
            row = {k: occ.get(k) for k in fields[:13]}
            for dim in fields[13:]:
                row[dim] = occ.get("scores", {}).get(dim)
            writer.writerow({key: sanitize_csv_value(value) for key, value in row.items()})

    print(f"H2-ready CSV: {len(h2_occs)} occupations -> {OUTPUT_CSV_H2}")


def inject_base_url(base_url: str):
    """Generate web/dev and docs/public JS assets from template with BASE_URL injected."""
    if not os.path.exists(TEMPLATE_FILE):
        print(f"WARN: Template not found at {TEMPLATE_FILE}, skipping JS generation")
        return
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = f.read()
    os.makedirs(WEB_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    web_js = template.replace("__BASE_URL__", "")
    web_output_js = os.path.join(WEB_DIR, "main.js")
    with open(web_output_js, "w", encoding="utf-8") as f:
        f.write(web_js)
    print(f"Generated: {web_output_js} (base_url='')")

    docs_js = template.replace("__BASE_URL__", base_url)
    docs_output_js = os.path.join(DOCS_DIR, "main.js")
    with open(docs_output_js, "w", encoding="utf-8") as f:
        f.write(docs_js)
    print(f"Generated: {docs_output_js} (base_url={base_url!r})")


def sync_model_data():
    """Copy model JSON files to docs/ and web/ for frontend access."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(WEB_DIR, exist_ok=True)
    for filename in MODEL_JSON_FILES:
        source = os.path.join(MODEL_DIR, filename)
        if not os.path.exists(source):
            print(f"WARN: Model file not found: {source}")
            continue
        for target_dir in [DOCS_DIR, WEB_DIR]:
            target = os.path.join(target_dir, filename)
            shutil.copy2(source, target)
            print(f"Copied model data: {target}")


def load_chunks():
    """Load shared HTML chunks from web/_chunks/ into a dict of {name: content}."""
    chunks = {}
    if not os.path.isdir(CHUNKS_DIR):
        return chunks
    for filename in os.listdir(CHUNKS_DIR):
        if filename.endswith(".html"):
            chunk_name = filename.rsplit(".", 1)[0]
            chunk_path = os.path.join(CHUNKS_DIR, filename)
            with open(chunk_path, "r", encoding="utf-8") as f:
                chunks[chunk_name] = f.read()
            print(f"Loaded chunk: {chunk_name}")
    return chunks


def resolve_page_template(page_path, output_path, chunks, page_vars):
    """Resolve <!-- #include X --> and {{var}} placeholders in an HTML page template.

    Each include marker references a key in *chunks.  Variables in the chunk
    content are resolved first, then the resolved chunk replaces the include
    marker.  Any remaining {{var}} markers in the page are resolved afterwards.
    """
    with open(page_path, "r", encoding="utf-8") as f:
        content = f.read()

    for chunk_name, chunk_content in sorted(chunks.items(), key=lambda x: -len(x[0])):
        marker = f"<!-- #include {chunk_name} -->"
        if marker not in content:
            continue
        resolved = chunk_content
        for var_name, var_value in page_vars.items():
            resolved = resolved.replace(f"{{{{{var_name}}}}}", var_value)
        content = content.replace(marker, resolved)

    for var_name, var_value in page_vars.items():
        content = content.replace(f"{{{{{var_name}}}}}", var_value)

    parent = os.path.dirname(output_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Resolved template -> {output_path}")


def resolve_all_pages(chunks):
    """Resolve every page in PAGE_VARS from its web/ template to docs/."""
    for page_rel, page_vars in PAGE_VARS.items():
        source = os.path.join(WEB_DIR, page_rel)
        target = os.path.join(DOCS_DIR, page_rel)
        if not os.path.exists(source):
            print(f"WARN: page template missing: {source}")
            continue
        resolve_page_template(source, target, chunks, page_vars)


def sync_public_artifacts():
    """Mirror source shell/assets into docs/ and docs data into ignored web/ dev copies.

    web/ is canonical for all page templates.  Templates are resolved through
    resolve_all_pages() (chunk includes + variable substitution) before landing
    in docs/.  No Jinja2 — all template expansion is plain str.replace()."""
    os.makedirs(WEB_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    # Load shared chunks and resolve page templates from web/ -> docs/
    chunks = load_chunks()
    if chunks:
        resolve_all_pages(chunks)

    # Copy static (non-template) assets verbatim
    for filename in STATIC_PUBLIC_FILES:
        source_path = os.path.join(WEB_DIR, filename)
        output_path = os.path.join(DOCS_DIR, filename)
        if os.path.exists(source_path):
            parent = os.path.dirname(output_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            shutil.copy2(source_path, output_path)
            print(f"Copied static asset: {output_path}")

    for docs_artifact in [OUTPUT_JSON, OUTPUT_JSON_ALL, OUTPUT_SCORE_DETAILS, OUTPUT_CSV_H2]:
        web_output = os.path.join(WEB_DIR, os.path.basename(docs_artifact))
        shutil.copy2(docs_artifact, web_output)
        print(f"Copied dev data: {web_output}")


def main():
    parser = argparse.ArgumentParser(description="Build occupations.json and web assets")
    parser.add_argument("--base-url", type=str, default="", help="Base URL for asset paths")
    args = parser.parse_args()

    # Load data
    occupations = load_occupations()
    scores = load_scores()
    print(f"Loaded {len(occupations)} occupations, {len(scores)} scored")

    # Merge scores
    occupations = merge_scores(occupations, scores)

    # Validate Phase 3 model sidecars
    validate_cluster_affinities(load_clusters(), load_archetypes())
    validate_pathways(load_pathways(), occupations)

    # Merge PLFS supply data (if available)
    supply_data = load_supply()
    occupations = allocate_supply(supply_data, occupations)
    if supply_data:
        supply_count = sum(1 for occ in occupations if occ.get("supply_estimate") is not None)
        print(f"PLFS supply merged: {supply_count} occupations with supply estimates")
    else:
        print("No PLFS supply data found (model/plfs_supply.json) — supply fields set to null")

    # Compute derived fields
    occupations = compute_upskill_paths(occupations)
    metrics = compute_summary_metrics(occupations)
    data_quality = compute_data_quality(occupations)

    # Count scored
    scored_count = sum(1 for occ in occupations if occ.get("scores"))

    # Filter to H2-relevant sectors
    h2_occupations = [
        occ for occ in occupations
        if occ.get("sector", "") in H2_SECTORS
    ]
    h2_metrics = compute_summary_metrics(h2_occupations)
    h2_data_quality = compute_data_quality(h2_occupations)
    h2_scored = sum(1 for occ in h2_occupations if occ.get("scores"))
    score_details = extract_score_details(occupations)

    # Build filtered output JSON (default view)
    output = {
        "dataset_version": DATASET_VERSION,
        "last_updated": DATASET_UPDATED,
        "total_occupations": len(h2_occupations),
        "total_all_occupations": len(occupations),
        "total_sectors": len(set(occ.get("sector", "Other") for occ in h2_occupations)),
        "total_all_sectors": len(set(occ.get("sector", "Other") for occ in occupations)),
        "scored_occupations": h2_scored,
        "summary": h2_metrics,
        "data_quality": h2_data_quality,
        "occupations": h2_occupations,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"Written: {OUTPUT_JSON} ({len(h2_occupations)} H2-relevant occupations)")

    # Build full output JSON (for "Show All" toggle)
    output_all = {
        "dataset_version": DATASET_VERSION,
        "last_updated": DATASET_UPDATED,
        "total_occupations": len(occupations),
        "total_all_occupations": len(occupations),
        "total_sectors": len(set(occ.get("sector", "Other") for occ in occupations)),
        "total_all_sectors": len(set(occ.get("sector", "Other") for occ in occupations)),
        "scored_occupations": scored_count,
        "summary": metrics,
        "data_quality": data_quality,
        "occupations": occupations,
    }

    with open(OUTPUT_JSON_ALL, "w", encoding="utf-8") as f:
        json.dump(output_all, f, indent=2, ensure_ascii=False)
    print(f"Written: {OUTPUT_JSON_ALL} ({len(occupations)} all occupations)")

    with open(OUTPUT_SCORE_DETAILS, "w", encoding="utf-8") as f:
        json.dump(score_details, f, indent=2, ensure_ascii=False)
    print(f"Written: {OUTPUT_SCORE_DETAILS} ({len(score_details)} score-detail records)")

    # Summary
    print(f"\nSummary metrics:")
    print(f"  H2-Ready Occupations: {metrics['h2_ready_occupations']}")
    if metrics["workforce_gap_2030"] is None:
        print("  Workforce Gap by 2030: N/A (PLFS subdivision supply incomplete)")
    else:
        print(f"  Workforce Gap by 2030: {metrics['workforce_gap_2030']:,}")
    print(f"  Fast Upskill Paths: {metrics['fast_upskill_paths']}")

    # Write H2 CSV
    write_h2_csv(occupations)

    # Generate JS
    inject_base_url(args.base_url)

    # Sync static shell/assets and ignored dev data copies
    sync_public_artifacts()

    # Copy model JSON files to docs/ and web/
    sync_model_data()


if __name__ == "__main__":
    main()
