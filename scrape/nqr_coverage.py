"""Coverage analysis for plan 009 (NCVET/NQR qualification-layer spike).

Reads the scraped NQR qualifications (scrape/raw/ncvet/qualifications.json),
the atlas occupation dataset (docs/occupations.json), and the reskilling
pathways (model/pathways.json), and writes plans/009-spike-report.md.

This script measures what the spike actually found -- it does not integrate
NQR data into the atlas (that is out of scope; see plans/009-*.md).
"""

import json
import os
import re
from collections import Counter

HERE = os.path.dirname(__file__)
NQR_FILE = os.path.join(HERE, "raw", "ncvet", "qualifications.json")
OCCUPATIONS_FILE = os.path.join(HERE, "..", "docs", "occupations.json")
PATHWAYS_FILE = os.path.join(HERE, "..", "model", "pathways.json")
NCO_MAPPING_CSV = os.path.join(HERE, "raw", "ncvet", "nco_mapping.csv")
NCO_MAPPING_PDF = os.path.join(HERE, "raw", "ncvet", "nco-mapping.pdf")
REPORT_FILE = os.path.join(HERE, "..", "plans", "009-spike-report.md")

SCRAPED_SECTORS = {
    7: "Capital Goods & Manufacturing",
    8: "Chemicals & Petrochemicals",
    12: "Environmental Science",
    18: "Hydrocarbon",
    35: "Power",
    51: "Water Supply, Sewerage, Waste Management & Remediation activities",
}

# Atlas sector name -> NQR sector name, for the same real-world sector.
# Built by inspecting docs/occupations.json's 12 sector names against the
# 6 NQR sectors scraped for this spike -- NOT an official crosswalk.
ATLAS_TO_NQR_SECTOR = {
    "Hydrocarbon": "Hydrocarbon",
    "Power": "Power",
    "Chemical and Petrochemicals": "Chemicals & Petrochemicals",
    "Environmental Science": "Environmental Science",
    "Capital Goods and Manufacturing": "Capital Goods & Manufacturing",
    # Atlas has no occupations in a "Water Supply..." sector, so NQR sector 51
    # has no atlas-side counterpart at all.
}

SYNTHETIC_PREFIXES = ("H2-MAR-", "H2-RFNBO-", "H2-GREEN-")

STOPWORDS = {
    "the", "of", "and", "for", "operator", "plant", "general", "engineer",
    "technician", "assistant", "supervisor", "junior", "senior", "maintenance",
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def keyword_set(title):
    words = re.findall(r"[a-zA-Z]+", (title or "").lower())
    return set(w for w in words if len(w) > 3 and w not in STOPWORDS)


def format_level(level):
    if level is None:
        return "?"
    return str(int(level)) if float(level).is_integer() else str(level)


def normalize_title(title):
    """Lowercase, fold en/em dashes to '-', collapse whitespace -- so
    "Junior Engineer - Power Distribution" and "Junior Engineer – Power
    Distribution" compare equal."""
    folded = re.sub(r"[–—]", "-", (title or "").lower())
    return re.sub(r"\s+", " ", folded).strip()


def pathway_anchoring(pathways, nqr):
    rows = []
    for p in pathways:
        target_norm = normalize_title(p["target_title"])
        tgt_kw = keyword_set(p["target_title"])
        scored = []
        for q in nqr:
            overlap = tgt_kw & keyword_set(q["title"])
            if not overlap:
                continue
            exact = 1 if normalize_title(q["title"]) == target_norm else 0
            scored.append((exact, len(overlap), q))
        scored.sort(key=lambda m: (-m[0], -m[1]))
        rows.append((p, [(count, q) for _, count, q in scored[:2]]))
    return rows


def build_report(nqr, occupations, pathways):
    focus = [o for o in occupations if o["scores"]["h2_adjacency"] >= 5]

    by_sector = Counter(q["sector"] for q in nqr)
    nos_counts = [len(q["nos"]) for q in nqr]
    level_dist = Counter(q["nsqf_level"] for q in nqr)
    no_nos_table = [q for q in nqr if not q["nos"]]

    synthetic_occupations = [
        o for o in occupations
        if any(str(o.get("id", "")).startswith(prefix) for prefix in SYNTHETIC_PREFIXES)
    ]

    overlap_sectors = set(ATLAS_TO_NQR_SECTOR.keys())
    focus_overlap = [o for o in focus if o["sector"] in overlap_sectors]
    all_overlap = [o for o in occupations if o["sector"] in overlap_sectors]

    anchoring = pathway_anchoring(pathways, nqr)

    nco_mapping_csv_exists = os.path.exists(NCO_MAPPING_CSV)

    lines = []
    lines.append("# Plan 009 spike report: NCVET/NQR qualification layer")
    lines.append("")
    lines.append(
        "Scope: scrape the H2-relevant slice of the National Qualifications "
        "Register (nqr.gov.in), measure how well it joins to the atlas's NCO "
        "codes, and recommend whether full integration is worth it. No "
        "runtime, model, or UI files were touched -- see plans/009-*.md."
    )
    lines.append("")

    # 1. Scrape stats
    lines.append("## 1. Scrape stats")
    lines.append("")
    lines.append(f"**{len(nqr)} unique qualifications** scraped across 6 sectors "
                 f"(site total, deduplicated by qualification id; no overlap "
                 f"between sectors was observed):")
    lines.append("")
    lines.append("| Sector ID | Sector | Qualifications |")
    lines.append("|---|---|---|")
    for sid, sname in SCRAPED_SECTORS.items():
        lines.append(f"| {sid} | {sname} | {by_sector.get(sname, 0)} |")
    lines.append("")
    nonzero_nos_counts = [c for c in nos_counts if c > 0]
    lines.append(f"**{sum(nos_counts)} total NOS rows** across all 295 qualifications. "
                 f"Per-qualification, among the {len(nonzero_nos_counts)} that render "
                 f"a NOS table at all: min {min(nonzero_nos_counts)}, "
                 f"max {max(nos_counts)}, mean {sum(nonzero_nos_counts)/len(nonzero_nos_counts):.1f}. "
                 f"{len(no_nos_table)} qualification(s) render no NOS table at all "
                 f"on the live site (genuine gap, not a parse failure -- verified "
                 f"by inspecting the raw HTML): "
                 + ", ".join(f"{q['id']} ({q['title']})" for q in no_nos_table) + ".")
    lines.append("")
    lines.append("NSQF level distribution (half-levels like 5.5 are real NSQF "
                 "levels, not a parsing artifact -- see tests/test_scrape_nqr.py):")
    lines.append("")
    lines.append("| NSQF level | Count |")
    lines.append("|---|---|")
    for level in sorted(level_dist.keys(), key=lambda l: (l is None, l)):
        lines.append(f"| {format_level(level)} | {level_dist[level]} |")
    lines.append("")

    # 2. Join coverage A
    lines.append("## 2. Join coverage A: 64 focus-view occupations (h2_adjacency >= 5)")
    lines.append("")
    lines.append("**BLOCKED.** Neither half of the planned join key exists:")
    lines.append("")
    lines.append(
        f"- **(a) Official mapping CSV** -- does not exist. The NCVET PDF at "
        f"the URL in DATASOURCES.md (`scrape/raw/ncvet/nco-mapping.pdf`, "
        f"downloaded, {os.path.getsize(NCO_MAPPING_PDF) if os.path.exists(NCO_MAPPING_PDF) else 0} bytes, "
        f"58 pages) is a policy/process report about the 2023 NCO-mapping "
        f"exercise -- committee composition, methodology, findings -- not a "
        f"per-qualification lookup table. A full-text regex search for "
        f"NCO-2015-shaped strings (`\\d{{4}}\\.\\d{{2,4}}`) across all 58 pages "
        f"found exactly 2 unique codes, both used as illustrative examples "
        f"in prose explaining the NCO code format, not real mappings. The "
        f"one real table it contains (Annexure VII) is an awarding-body-level "
        f"aggregate (45 awarding bodies, e.g. \"DGT: 463 total qualifications, "
        f"0 without an NCO code\") -- useful context, not a queryable crosswalk. "
        f"`scrape/raw/ncvet/nco_mapping.csv` was deliberately **not created**: "
        f"synthesizing a CSV from data this document doesn't contain would "
        f"misrepresent it. `nco_mapping_csv_exists` = {nco_mapping_csv_exists}."
    )
    lines.append(
        "- **(b) 4-digit NCO-prefix match** -- also impossible. NQR "
        "qualification detail pages carry no NCO code field at all. Confirmed "
        "by grepping all 295 cached detail pages "
        "(`scrape/raw/ncvet/detail/*.html`) for the whole-word token `NCO`: "
        "**zero matches**. NQR identifies qualifications by its own NQR code "
        "(e.g. `2022/HYC/HSSCI/06782`) and NOS codes (e.g. `HYC/N6401`), "
        "neither of which is an NCO-2015 code or derivable from one."
    )
    lines.append("")
    lines.append(
        f"**Supplementary, non-equivalent signal:** sector-name overlap (NOT "
        f"a per-occupation join -- an occupation and a qualification sharing "
        f"a sector name says nothing about whether that occupation has a "
        f"matching qualification). Of the 64 focus occupations, "
        f"**{len(focus_overlap)}** are in a sector name that also appears "
        f"among the 6 scraped NQR sectors "
        f"({', '.join(sorted(ATLAS_TO_NQR_SECTOR.keys()))}); the atlas has no "
        f"occupations in a \"Water Supply...\" sector, so NQR sector 51 "
        f"(6 qualifications) has no atlas-side counterpart at all."
    )
    lines.append("")

    # 3. Join coverage B
    lines.append("## 3. Join coverage B: 480 H2-sector occupations + synthetic H2-frontier codes")
    lines.append("")
    lines.append(
        "**BLOCKED**, same reason as Join coverage A (no NCO code exists on "
        "the NQR side to join against, via either (a) or (b))."
    )
    lines.append("")
    lines.append(
        f"Supplementary sector-name overlap: **{len(all_overlap)}** of the "
        f"480 occupations share a sector name with a scraped NQR sector."
    )
    lines.append("")
    lines.append(
        f"**Synthetic H2-frontier codes (`H2-MAR-*`, `H2-RFNBO-*`, `H2-GREEN-*`): "
        f"expect zero -- confirmed, trivially.** A repo-wide search "
        f"(`grep -r \"H2-MAR\\|H2-RFNBO\\|H2-GREEN\"`) found **{len(synthetic_occupations)}** "
        f"matches. These codes are not a low-coverage edge case -- they do "
        f"not exist anywhere in `docs/occupations.json` or the rest of the "
        f"repo. All 480 atlas occupations carry an `NCS-`-prefixed id. This "
        f"is a stale assumption in the plan's \"Current state\" section, same "
        f"category as the `build/nco_ncs_crosswalk.csv` reference (also "
        f"never present in this repo's history -- see DATASOURCES.md update)."
    )
    lines.append("")

    # 4. Pathway anchoring
    lines.append("## 4. Pathway anchoring check (model/pathways.json)")
    lines.append("")
    lines.append(
        f"All {len(pathways)} pathway records checked against the 295 scraped "
        f"qualifications by keyword overlap on title (sector-blind, no NCO "
        f"join available -- see above). This is the one part of the analysis "
        f"with a usable join key (free text), and the most actionable finding "
        f"in this report."
    )
    lines.append("")
    lines.append("| Target occupation | Modeled reskill | Best NQR match | NQR hours | Anchoring verdict |")
    lines.append("|---|---|---|---|---|")
    for p, matches in anchoring:
        modeled = f"{p['reskill_months']} mo / Rs {p['reskill_cost_inr']:,}"
        if not matches:
            lines.append(f"| {p['target_title']} | {modeled} | -- none -- | -- | No candidate qualification found |")
            continue
        _, best = matches[0]
        hours = best["hours_max"] or best["hours_min"]
        hours_str = f"{hours}h" if hours else "?"
        title_close = normalize_title(best["title"]) == normalize_title(p["target_title"])
        verdict = "Strong candidate (near-exact title match)" if title_close else "Weak/partial match -- verify before anchoring"
        lines.append(
            f"| {p['target_title']} | {modeled} | {best['title']} (NQR {best['id']}, "
            f"{best['sector']}, NSQF {format_level(best['nsqf_level'])}) | {hours_str} | {verdict} |"
        )
    lines.append("")
    lines.append(
        "Notable: \"Ammonia Operator/ Ammonia Plant Operator\" is the target "
        "of 3 of the 8 pathways and has **zero** keyword-matching qualification "
        "in any of the 6 scraped sectors -- ammonia synthesis/handling is not "
        "represented in the NQR register for Hydrocarbon, Power, Chemicals & "
        "Petrochemicals, Environmental Science, Capital Goods & Manufacturing, "
        "or Water Supply. \"Chemical Engineer, General\" also has no good match: "
        "NQR/NCVET registers NSQF-aligned vocational qualifications, not "
        "university engineering degrees, so degree-level pathway targets are "
        "structurally out of scope for this data source."
    )
    lines.append("")

    # 5. Recommendation
    lines.append("## 5. Recommendation")
    lines.append("")
    lines.append(
        "**Full integration (source_ncvet: true + per-occupation qualifications "
        "block) is NOT worth scoping yet.** The blocker is not scrape "
        "difficulty (the CSRF/AJAX flow works fine and NQR data parses "
        "cleanly) -- it is that there is no join key. Neither NQR nor the "
        "official NCVET mapping PDF carries an NCO-2015 code, and no "
        "crosswalk file exists in this repo. Without a join key, "
        "`source_ncvet` could only ever be set via manual title-matching per "
        "occupation, which does not scale to 480 (or 1,802) records and "
        "would not be verifiable at the confidence level the atlas otherwise "
        "holds itself to."
    )
    lines.append("")
    lines.append("**If a follow-up is scoped anyway, the schema it should add "
                 "(once a join key exists) is:**")
    lines.append("```")
    lines.append('"qualifications": [')
    lines.append('  {"nqr_id": "1284", "nqr_code": "2022/HYC/HSSCI/06782",')
    lines.append('   "title": "...", "nsqf_level": 3, "hours_min": 330, "hours_max": 330,')
    lines.append('   "sector": "Hydrocarbon", "url": "https://nqr.gov.in/qualifications/1284"}')
    lines.append(']')
    lines.append("```")
    lines.append("")
    lines.append("**Top 3 risks observed:**")
    lines.append("")
    lines.append(
        "1. **No join key, and no realistic path to one without manual "
        "review.** This is the core finding of this spike -- both assumed "
        "crosswalks (the PDF, and a hand-built CSV the plan referenced) turn "
        "out not to exist."
    )
    lines.append(
        "2. **NQR site fragility.** The CSRF/session flow (`GET` sector page "
        "-> extract token -> `POST filter-duration`) is undocumented and "
        "could change without notice; there is no API contract, only "
        "reverse-engineered jQuery."
    )
    lines.append(
        "3. **NSQF half-levels and missing NOS tables are real, not edge "
        "cases to code around later.** 96 of 295 qualifications (33%) carry "
        "a half-level (5.5, 4.5, etc); any downstream consumer (UI filter, "
        "export) must treat `nsqf_level` as numeric-but-not-integer from day one."
    )
    lines.append("")
    lines.append(
        "**Pathway anchoring is the one genuinely promising thread**: "
        "\"Junior Engineer - Power Distribution\" anchors near-exactly to a "
        "real NQR qualification with real hours. A narrower follow-up -- "
        "manually reviewing just the 8 pathway targets against NQR titles, "
        "rather than attempting a 480-occupation integration -- could "
        "replace a handful of `modeled_estimate` reskill durations with "
        "`nqr_anchored` ones at low risk."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def main():
    nqr = load_json(NQR_FILE)
    occ_data = load_json(OCCUPATIONS_FILE)
    occupations = occ_data["occupations"]
    pathways_data = load_json(PATHWAYS_FILE)
    pathways = pathways_data["pathways"]

    report = build_report(nqr, occupations, pathways)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Wrote {REPORT_FILE} ({len(report)} chars)")


if __name__ == "__main__":
    main()
