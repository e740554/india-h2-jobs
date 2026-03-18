"""Merge all batch result files into the master scores.json.

Reads mega_batch_*_results.json and batch_*_results.json files,
merges them into scores.json (preserving existing scores).

Usage:
    python score/merge_results.py
"""

import glob
import json
import os

BATCHES_DIR = os.path.join(os.path.dirname(__file__), "batches")
SCORES_FILE = os.path.join(os.path.dirname(__file__), "..", "scores.json")


def main():
    # Load existing scores
    scores = {}
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            scores = json.load(f)
    print(f"Existing scores: {len(scores)} occupations")

    # Find all result files
    patterns = [
        os.path.join(BATCHES_DIR, "mega_batch_*_results.json"),
        os.path.join(BATCHES_DIR, "batch_*_results.json"),
    ]
    result_files = []
    for pattern in patterns:
        result_files.extend(glob.glob(pattern))

    if not result_files:
        print("No result files found.")
        return

    total_new = 0
    for filepath in sorted(result_files):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                batch_scores = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  [ERROR] Failed to read {filename}: {e}")
            continue

        new_in_batch = 0
        for occ_id, dims in batch_scores.items():
            if occ_id not in scores:
                scores[occ_id] = {}
                new_in_batch += 1
            # Merge dimensions (new scores overwrite)
            for dim, data in dims.items():
                scores[occ_id][dim] = data

        total_new += new_in_batch
        print(f"  {filename}: {len(batch_scores)} occupations ({new_in_batch} new)")

    # Save merged scores
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2, ensure_ascii=False)

    print(f"\nTotal: {len(scores)} scored occupations ({total_new} new)")
    print(f"Saved to: {SCORES_FILE}")


if __name__ == "__main__":
    main()
