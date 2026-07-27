# Plan 009 spike report: NCVET/NQR qualification layer

Scope: scrape the H2-relevant slice of the National Qualifications Register (nqr.gov.in), measure how well it joins to the atlas's NCO codes, and recommend whether full integration is worth it. No runtime, model, or UI files were touched -- see plans/009-*.md.

## 1. Scrape stats

**295 unique qualifications** scraped across 6 sectors (site total, deduplicated by qualification id; no overlap between sectors was observed):

| Sector ID | Sector | Qualifications |
|---|---|---|
| 7 | Capital Goods & Manufacturing | 107 |
| 8 | Chemicals & Petrochemicals | 20 |
| 12 | Environmental Science | 64 |
| 18 | Hydrocarbon | 76 |
| 35 | Power | 22 |
| 51 | Water Supply, Sewerage, Waste Management & Remediation activities | 6 |

**2457 total NOS rows** across all 295 qualifications. Per-qualification, among the 293 that render a NOS table at all: min 1, max 45, mean 8.4. 2 qualification(s) render no NOS table at all on the live site (genuine gap, not a parse failure -- verified by inspecting the raw HTML): 10907 (Jr. Technician – Tool & Die), 13911 (Overhead Crane Operator).

NSQF level distribution (half-levels like 5.5 are real NSQF levels, not a parsing artifact -- see tests/test_scrape_nqr.py):

| NSQF level | Count |
|---|---|
| 2 | 7 |
| 2.5 | 9 |
| 3 | 60 |
| 3.5 | 25 |
| 4 | 85 |
| 4.5 | 46 |
| 5 | 31 |
| 5.5 | 15 |
| 6 | 16 |
| 6.5 | 1 |

## 2. Join coverage A: 64 focus-view occupations (h2_adjacency >= 5)

**BLOCKED.** Neither half of the planned join key exists:

- **(a) Official mapping CSV** -- does not exist. The NCVET PDF at the URL in DATASOURCES.md (`scrape/raw/ncvet/nco-mapping.pdf`, downloaded, 1165809 bytes, 58 pages) is a policy/process report about the 2023 NCO-mapping exercise -- committee composition, methodology, findings -- not a per-qualification lookup table. A full-text regex search for NCO-2015-shaped strings (`\d{4}\.\d{2,4}`) across all 58 pages found exactly 2 unique codes, both used as illustrative examples in prose explaining the NCO code format, not real mappings. The one real table it contains (Annexure VII) is an awarding-body-level aggregate (45 awarding bodies, e.g. "DGT: 463 total qualifications, 0 without an NCO code") -- useful context, not a queryable crosswalk. `scrape/raw/ncvet/nco_mapping.csv` was deliberately **not created**: synthesizing a CSV from data this document doesn't contain would misrepresent it. `nco_mapping_csv_exists` = False.
- **(b) 4-digit NCO-prefix match** -- also impossible. NQR qualification detail pages carry no NCO code field at all. Confirmed by grepping all 295 cached detail pages (`scrape/raw/ncvet/detail/*.html`) for the whole-word token `NCO`: **zero matches**. NQR identifies qualifications by its own NQR code (e.g. `2022/HYC/HSSCI/06782`) and NOS codes (e.g. `HYC/N6401`), neither of which is an NCO-2015 code or derivable from one.

**Supplementary, non-equivalent signal:** sector-name overlap (NOT a per-occupation join -- an occupation and a qualification sharing a sector name says nothing about whether that occupation has a matching qualification). Of the 64 focus occupations, **38** are in a sector name that also appears among the 6 scraped NQR sectors (Capital Goods and Manufacturing, Chemical and Petrochemicals, Environmental Science, Hydrocarbon, Power); the atlas has no occupations in a "Water Supply..." sector, so NQR sector 51 (6 qualifications) has no atlas-side counterpart at all.

## 3. Join coverage B: 480 H2-sector occupations + synthetic H2-frontier codes

**BLOCKED**, same reason as Join coverage A (no NCO code exists on the NQR side to join against, via either (a) or (b)).

Supplementary sector-name overlap: **162** of the 480 occupations share a sector name with a scraped NQR sector.

**Synthetic H2-frontier codes (`H2-MAR-*`, `H2-RFNBO-*`, `H2-GREEN-*`): expect zero -- confirmed, trivially.** A repo-wide search (`grep -r "H2-MAR\|H2-RFNBO\|H2-GREEN"`) found **0** matches. These codes are not a low-coverage edge case -- they do not exist anywhere in `docs/occupations.json` or the rest of the repo. All 480 atlas occupations carry an `NCS-`-prefixed id. This is a stale assumption in the plan's "Current state" section, same category as the `build/nco_ncs_crosswalk.csv` reference (also never present in this repo's history -- see DATASOURCES.md update).

## 4. Pathway anchoring check (model/pathways.json)

All 8 pathway records checked against the 295 scraped qualifications by keyword overlap on title (sector-blind, no NCO join available -- see above). This is the one part of the analysis with a usable join key (free text), and the most actionable finding in this report.

| Target occupation | Modeled reskill | Best NQR match | NQR hours | Anchoring verdict |
|---|---|---|---|---|
| Ammonia Operator/ Ammonia Plant Operator | 6 mo / Rs 85,000 | -- none -- | -- | No candidate qualification found |
| Ammonia Operator/ Ammonia Plant Operator | 5 mo / Rs 70,000 | -- none -- | -- | No candidate qualification found |
| Chemical Engineer, General | 4 mo / Rs 120,000 | CHEMICAL PLANT TECHNOLOGY (CRAFT INSTRUCTOR) (NQR 12675, Chemicals & Petrochemicals, NSQF 4.5) | 1350h | Weak/partial match -- verify before anchoring |
| Chemist, Water Purification/ Water Treatment | 3 mo / Rs 45,000 | Basics of Green Hydrogen Water Treatment Process (NQR 12292, Hydrocarbon, NSQF 5) | 30h | Weak/partial match -- verify before anchoring |
| Junior Engineer - Power Distribution | 4 mo / Rs 60,000 | Junior Engineer – Power Distribution (NQR 14679, Power, NSQF 5) | 600h | Strong candidate (near-exact title match) |
| Mechanic (Electrical Electronics Instrumentation) | 6 mo / Rs 90,000 | Assistant Technician Electrical and Electronics (NQR 9865, Capital Goods & Manufacturing, NSQF 3.5) | 1200h | Weak/partial match -- verify before anchoring |
| Maintenance Supervisor | 5 mo / Rs 65,000 | -- none -- | -- | No candidate qualification found |
| Ammonia Operator/ Ammonia Plant Operator | 8 mo / Rs 95,000 | -- none -- | -- | No candidate qualification found |

Notable: "Ammonia Operator/ Ammonia Plant Operator" is the target of 3 of the 8 pathways and has **zero** keyword-matching qualification in any of the 6 scraped sectors -- ammonia synthesis/handling is not represented in the NQR register for Hydrocarbon, Power, Chemicals & Petrochemicals, Environmental Science, Capital Goods & Manufacturing, or Water Supply. "Chemical Engineer, General" also has no good match: NQR/NCVET registers NSQF-aligned vocational qualifications, not university engineering degrees, so degree-level pathway targets are structurally out of scope for this data source.

## 5. Recommendation

**Full integration (source_ncvet: true + per-occupation qualifications block) is NOT worth scoping yet.** The blocker is not scrape difficulty (the CSRF/AJAX flow works fine and NQR data parses cleanly) -- it is that there is no join key. Neither NQR nor the official NCVET mapping PDF carries an NCO-2015 code, and no crosswalk file exists in this repo. Without a join key, `source_ncvet` could only ever be set via manual title-matching per occupation, which does not scale to 480 (or 1,802) records and would not be verifiable at the confidence level the atlas otherwise holds itself to.

**If a follow-up is scoped anyway, the schema it should add (once a join key exists) is:**
```
"qualifications": [
  {"nqr_id": "1284", "nqr_code": "2022/HYC/HSSCI/06782",
   "title": "...", "nsqf_level": 3, "hours_min": 330, "hours_max": 330,
   "sector": "Hydrocarbon", "url": "https://nqr.gov.in/qualifications/1284"}
]
```

**Top 3 risks observed:**

1. **No join key, and no realistic path to one without manual review.** This is the core finding of this spike -- both assumed crosswalks (the PDF, and a hand-built CSV the plan referenced) turn out not to exist.
2. **NQR site fragility.** The CSRF/session flow (`GET` sector page -> extract token -> `POST filter-duration`) is undocumented and could change without notice; there is no API contract, only reverse-engineered jQuery.
3. **NSQF half-levels and missing NOS tables are real, not edge cases to code around later.** 96 of 295 qualifications (33%) carry a half-level (5.5, 4.5, etc); any downstream consumer (UI filter, export) must treat `nsqf_level` as numeric-but-not-integer from day one.

**Pathway anchoring is the one genuinely promising thread**: "Junior Engineer - Power Distribution" anchors near-exactly to a real NQR qualification with real hours. A narrower follow-up -- manually reviewing just the 8 pathway targets against NQR titles, rather than attempting a 480-occupation integration -- could replace a handful of `modeled_estimate` reskill durations with `nqr_anchored` ones at low risk.

