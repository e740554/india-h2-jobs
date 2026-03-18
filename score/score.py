"""Score occupations across 6 H2-specific dimensions.

This script is designed to be run interactively via Claude Code, which handles
the actual LLM scoring. It prepares batches and writes results to scores.json.

Usage (via Claude Code):
    python score/score.py                    # Score all unscored occupations
    python score/score.py --dry-run          # Print stats without scoring
    python score/score.py --batch-size 20    # Custom batch size
    python score/score.py --sector Power     # Score only one sector

The scoring itself happens when Claude Code reads the batch files and
processes them through its own context. See score/README.md for workflow.
"""

import argparse
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from score.config import DIMENSIONS, BATCH_SIZE

OCCUPATIONS_CSV = os.path.join(os.path.dirname(__file__), "..", "occupations.csv")
PARSED_JSON = os.path.join(os.path.dirname(__file__), "..", "parse", "parsed_occupations.json")
SCORES_FILE = os.path.join(os.path.dirname(__file__), "..", "scores.json")
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
BATCHES_DIR = os.path.join(os.path.dirname(__file__), "batches")


def load_occupations() -> list[dict]:
    """Load parsed occupations."""
    with open(PARSED_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def load_scores() -> dict:
    """Load existing scores (idempotency)."""
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_scores(scores: dict):
    """Save scores to JSON."""
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)


def needs_scoring(occ_id: str, scores: dict) -> list[str]:
    """Return list of dimensions that still need scoring for this occupation."""
    if occ_id not in scores:
        return list(DIMENSIONS)
    existing = scores[occ_id]
    return [d for d in DIMENSIONS if d not in existing or existing[d].get("score") is None]


def load_prompt(dimension: str) -> str:
    """Load scoring prompt template."""
    path = os.path.join(PROMPTS_DIR, f"{dimension}.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_prompt(template: str, occupation: dict) -> str:
    """Fill prompt template with occupation data using simple replacement."""
    result = template
    result = result.replace("{title}", occupation.get("title", "Unknown"))
    result = result.replace("{sector}", occupation.get("sector", "Unknown"))
    result = result.replace("{education_req}", str(occupation.get("education_req") or "Not specified"))
    result = result.replace("{formal_sector_pct}", str(occupation.get("formal_sector_pct") or "Not available"))
    return result


def prepare_batch(occupations: list[dict], scores: dict, batch_size: int, sector: str | None = None) -> list[dict]:
    """Prepare a batch of occupations that need scoring."""
    batch = []
    for occ in occupations:
        if sector and occ.get("sector") != sector:
            continue
        missing = needs_scoring(occ["id"], scores)
        if missing:
            batch.append({"occupation": occ, "missing_dimensions": missing})
        if len(batch) >= batch_size:
            break
    return batch


def write_batch_file(batch: list[dict], batch_num: int):
    """Write a batch file for Claude Code to process."""
    os.makedirs(BATCHES_DIR, exist_ok=True)
    filepath = os.path.join(BATCHES_DIR, f"batch_{batch_num:04d}.json")

    # Prepare scoring requests
    requests = []
    for item in batch:
        occ = item["occupation"]
        for dim in item["missing_dimensions"]:
            template = load_prompt(dim)
            prompt = format_prompt(template, occ)
            requests.append({
                "id": occ["id"],
                "title": occ["title"],
                "sector": occ["sector"],
                "dimension": dim,
                "prompt": prompt,
            })

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=2, ensure_ascii=False)

    return filepath, len(requests)


def main():
    parser = argparse.ArgumentParser(description="Prepare occupation scoring batches")
    parser.add_argument("--dry-run", action="store_true", help="Print stats without creating batches")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"Occupations per batch (default: {BATCH_SIZE})")
    parser.add_argument("--sector", type=str, default=None, help="Score only this sector")
    args = parser.parse_args()

    occupations = load_occupations()
    scores = load_scores()

    print(f"Occupations: {len(occupations)}")
    print(f"Already scored: {len(scores)}")
    print(f"Dimensions: {len(DIMENSIONS)}")

    # Count what needs scoring
    total_missing = 0
    occs_needing_scoring = 0
    for occ in occupations:
        if args.sector and occ.get("sector") != args.sector:
            continue
        missing = needs_scoring(occ["id"], scores)
        if missing:
            occs_needing_scoring += 1
            total_missing += len(missing)

    print(f"\nOccupations needing scoring: {occs_needing_scoring}")
    print(f"Total scoring calls needed: {total_missing}")
    print(f"Estimated batches: {(occs_needing_scoring + args.batch_size - 1) // args.batch_size}")

    if args.dry_run:
        print("\n--dry-run: No batches created.")
        return

    # Create batches
    remaining = [occ for occ in occupations if needs_scoring(occ["id"], scores)]
    if args.sector:
        remaining = [occ for occ in remaining if occ.get("sector") == args.sector]

    batch_num = 0
    offset = 0
    total_requests = 0
    while offset < len(remaining):
        batch_occs = remaining[offset:offset + args.batch_size]
        batch = [{"occupation": occ, "missing_dimensions": needs_scoring(occ["id"], scores)} for occ in batch_occs]
        filepath, num_requests = write_batch_file(batch, batch_num)
        total_requests += num_requests
        print(f"Batch {batch_num}: {len(batch)} occupations, {num_requests} requests -> {filepath}")
        batch_num += 1
        offset += args.batch_size

    print(f"\nCreated {batch_num} batch files with {total_requests} total requests")
    print(f"Batch files in: {BATCHES_DIR}")
    print("\nTo score, run Claude Code and ask it to process the batches.")


if __name__ == "__main__":
    main()
