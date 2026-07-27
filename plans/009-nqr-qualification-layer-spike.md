# Plan 009: Spike the NCVET/NQR qualification layer -- scrape, crosswalk coverage, feasibility report

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report -- do not improvise. When done, update the status row for this plan
> in `plans/README.md` -- unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 5e754d2..HEAD -- scrape/ DATASOURCES.md model/pathways.json build/nco_ncs_crosswalk.csv`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M (spike -- investigation and data, NOT UI integration)
- **Risk**: LOW (adds data and a report; touches no runtime or published page)
- **Depends on**: none
- **Category**: direction (spike/design)
- **Planned at**: commit `5e754d2`, 2026-07-27

## Why this matters

The atlas tells a planner "you need N workers in occupation X, cluster Y, by
year Z" -- but a skilling institution (NSDC, a Sector Skill Council, a state
skill mission) operationalizes *qualifications*: NSQF levels, Qualification
Packs, NOS hours. The occupation schema already reserves a `source_ncvet`
field (currently `false` on all 1,802 records), `DATASOURCES.md` fully specs
the NQR scraping strategy, and `scrape/raw/ncvet/` exists but is empty. This
spike closes the evidence gap: scrape the H₂-relevant slice of the National
Qualifications Register, measure how well it joins to the atlas's NCO codes,
and produce a written feasibility report so the follow-up integration plan can
be scoped on facts instead of hope. Reskilling pathways currently cite
`"training_provider": "NSDC / Skill India"` as modeled estimates; this layer
is what would anchor them to real qualifications.

## Current state

- `docs/occupations.json` -- every record carries `"source_ncvet": false` and
  an `nco_code` like `"8131.8000"` (NCO-2015, 4-digit + 4-digit).
- `scrape/raw/ncvet/` -- exists, empty (0 files).
- `scrape/scrape_ncs.py` -- the exemplar scraper: plain HTTP GET, regex
  extraction, 1.5 s politeness delay, raw responses saved under
  `scrape/raw/ncs/`. Match its structure, logging style, and delay.
- `tests/test_scrape_ncs.py` -- the exemplar scraper test (fixture-based, no
  live network in tests). Match it.
- `build/nco_ncs_crosswalk.csv` -- hand-built NCO/NCS crosswalk.
- `model/pathways.json` -- pathway records with `reskill_months`,
  `reskill_cost_inr`, `training_type`, `training_provider`,
  `source_type: "modeled_estimate"`.
- `DATASOURCES.md:89-138` -- the NQR source spec. Key facts, inlined so you do
  not need to rediscover them:
  - Primary source `https://nqr.gov.in` (Laravel, server-rendered HTML +
    jQuery AJAX). robots.txt: `User-agent: * allow: /` -- fully open. Do NOT
    use `skillindiadigital.gov.in` (Angular SPA, `Disallow: /`).
  - `nqr.gov.in/qualificationfile` -- qualification search (GET).
  - `nqr.gov.in/qualifications/{id}` -- detail page with the NOS table
    (server-rendered): NOS code, title, mandatory/optional, estimated hours,
    credits, NSQF level.
  - `nqr.gov.in/filter-duration` -- AJAX POST needing a CSRF `_token`
    scraped from the sector page first.
  - H₂-relevant sector IDs: 18 Hydrocarbon, 35 Power, 8 Chemicals &
    Petrochemicals, 12 Environmental Science, 7 Capital Goods &
    Manufacturing, 51 Water Supply/Sewerage/Waste.
  - Official NCO-2015 -> qualification mapping PDF:
    `ncvet.gov.in/wp-content/uploads/2025/05/Report-on-Mapping-of-Qualifications-with-NCO-Codes.pdf`.
- Data licensing note in `DATASOURCES.md`: Government of India public
  resources, used for open research with explicit credit.

**Repo conventions that apply:**

- Python, no heavyweight scraping frameworks; `requests`-style HTTP as in
  `scrape/scrape_ncs.py`. Check `requirements.txt` before adding anything.
- Raw scrape output goes under `scrape/raw/ncvet/` (mirrors `scrape/raw/ncs/`).
- 1.5 s minimum delay between requests (self-imposed politeness, same as NCS).
- Tests never hit the live network; use checked-in HTML fixtures.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python -m pytest` | all pass |
| Focused tests | `python -m pytest tests/test_scrape_nqr.py` | all pass |
| Live spike run | `python scrape/scrape_nqr.py --sectors 18,35,8,12,7,51` | writes JSON under `scrape/raw/ncvet/`, prints per-sector counts |
| Coverage report run | `python scrape/nqr_coverage.py` | writes `plans/009-spike-report.md` coverage tables |

(The last two commands are what you will create.)

## Scope

**In scope** (create or modify only these):

- `scrape/scrape_nqr.py` (create)
- `scrape/nqr_coverage.py` (create -- join analysis script)
- `scrape/raw/ncvet/` (scraped JSON/HTML artifacts)
- `tests/test_scrape_nqr.py` + `tests/fixtures/` additions (create)
- `plans/009-spike-report.md` (create -- the deliverable)
- `DATASOURCES.md` (update the NCVET section with what the spike actually found)
- `plans/README.md` (status row)

**Out of scope** (do NOT touch):

- `model/*.json`, `web/`, `docs/`, `build/build.py` -- NO integration into the
  dataset, runtime, or UI in this spike. That is the follow-up plan, scoped
  from your report.
- `model/pathways.json` -- do not rewrite pathway costs/durations here.
- The official mapping PDF parse beyond extraction of the NCO->qualification
  table (no re-modeling).

## Git workflow

- Branch: `advisor/009-nqr-spike`
- Commit style: `feat(scrape): ...` / `docs: ...` as in `git log`
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Recon the live NQR site (read-only, small)

Fetch `nqr.gov.in/qualificationfile` and ONE detail page
(`nqr.gov.in/qualifications/{id}` for any id found on the search page). Save
both raw HTML files under `scrape/raw/ncvet/recon/`. Confirm the NOS-table
fields listed in "Current state" are present in the detail HTML.

**Verify**: `ls scrape/raw/ncvet/recon` -> 2 files;
`grep -c -i "NSQF" scrape/raw/ncvet/recon/<detail file>` -> >= 1.

### Step 2: Write `scrape/scrape_nqr.py`

Model on `scrape/scrape_ncs.py` (structure, logging, delay, raw persistence).
Behavior: for each sector id passed via `--sectors`, GET the sector page,
extract the CSRF `_token`, POST `filter-duration` to list qualification ids,
then GET each `qualifications/{id}` detail page; parse qualification title,
sector, NSQF level, total hours, credits, and the NOS rows; write one JSON
file per sector to `scrape/raw/ncvet/sector_{id}.json` plus a combined
`scrape/raw/ncvet/qualifications.json`. 1.5 s delay between requests, resume
tolerance (skip already-saved detail pages on rerun).

**Verify**: `python -m pytest tests/test_scrape_nqr.py` -> pass (fixture-based
parse tests, Step 4 writes them -- during this step run the script's
`--limit 5` mode against the live site and confirm 5 parsed records print).

### Step 3: Run the sector sweep

Run the scraper for sector ids `18,35,8,12,7,51`. Expect minutes-to-hours at
1.5 s per request depending on qualification counts.

**Verify**: `python -c "import json;d=json.load(open('scrape/raw/ncvet/qualifications.json',encoding='utf-8'));print(len(d))"`
-> a positive count; record the number in the report.

### Step 4: Fixture-based tests

Save two truncated real detail pages as fixtures under `tests/fixtures/` and
write `tests/test_scrape_nqr.py` covering: NOS table parse (happy path),
missing-NSQF-level handling, and CSRF token extraction from the sector page
fixture. Model on `tests/test_scrape_ncs.py`.

**Verify**: `python -m pytest tests/test_scrape_nqr.py` -> all pass;
`python -m pytest` -> no regressions.

### Step 5: Download and extract the official NCO mapping

Download the NCVET mapping PDF (URL in "Current state") to
`scrape/raw/ncvet/nco-mapping.pdf`. Extract its NCO-code -> qualification
table to `scrape/raw/ncvet/nco_mapping.csv` (use `tabula-py` or `camelot` if
present in `requirements.txt`; if neither is installed, extract with
`pdfplumber` if available; if none of the three exists, STOP -- do not add a
new dependency without reporting first).

**Verify**: `python -c "import csv;rows=list(csv.reader(open('scrape/raw/ncvet/nco_mapping.csv',encoding='utf-8')));print(len(rows))"`
-> > 50 (if far lower, note extraction quality in the report instead of
retrying indefinitely).

### Step 6: Coverage analysis and report

Write `scrape/nqr_coverage.py` that joins, and writes
`plans/009-spike-report.md` containing:

1. Scrape stats: qualifications per sector, NOS rows, NSQF level distribution.
2. Join coverage A: fraction of the atlas's 64 focus-view occupations
   (`h2_adjacency >= 5` in `docs/occupations.json`) with >= 1 qualification
   via (a) the official mapping CSV and (b) any 4-digit NCO-prefix match.
3. Join coverage B: same for the 480-occupation H₂-sector set and for the
   H₂-frontier synthetic codes (`H2-MAR-*`, `H2-RFNBO-*`, `H2-GREEN-*` --
   expect zero; state it explicitly).
4. Pathway anchoring check: for the pathway targets in `model/pathways.json`,
   which have a real qualification with hours (i.e. could replace the modeled
   `reskill_months`/`reskill_cost_inr` with anchored data)?
5. A recommendation section: is full integration worth it, what schema the
   integration plan should add (e.g. `qualifications: [{nqr_id, title, nsqf_level, hours}]`
   per occupation), and the top 3 risks observed.

Update `DATASOURCES.md`'s NCVET section with observed reality (counts, quirks,
pagination behavior).

**Verify**: `python scrape/nqr_coverage.py` -> exits 0 and
`grep -c "Join coverage" plans/009-spike-report.md` -> >= 2.

## Test plan

- `tests/test_scrape_nqr.py` (Step 4): NOS parse happy path, missing NSQF
  level, CSRF extraction -- fixtures only, no network.
- Full suite green: `python -m pytest`.

## Done criteria

- [ ] `scrape/raw/ncvet/qualifications.json` exists with > 0 records
- [ ] `scrape/raw/ncvet/nco_mapping.csv` exists (or report documents why not)
- [ ] `plans/009-spike-report.md` exists with scrape stats, both coverage
      tables, pathway anchoring check, and a recommendation
- [ ] `python -m pytest` exits 0 including new fixture tests
- [ ] `git status` shows no modifications outside the in-scope list
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `nqr.gov.in` robots.txt no longer allows crawling, or the site now requires
  auth -- report; do not work around access controls.
- The `filter-duration` CSRF flow does not work as described after two
  attempts -- capture the raw responses to `scrape/raw/ncvet/recon/` and
  report what the site actually does.
- The mapping PDF URL 404s -- search `ncvet.gov.in` for a successor document,
  and if none is found in 15 minutes, write the report without it (note the
  gap prominently).
- Any parsing requires a dependency not in `requirements.txt`.
- Total request volume would exceed ~2,000 pages -- report the projected count
  first.

## Maintenance notes

- The follow-up integration plan (not this one) will: set `source_ncvet: true`
  where a join exists, add a qualifications block to occupation records, and
  surface NSQF/QP data in the sidebar and CSV exports. Scope it from the
  report's recommendation section.
- Anchoring `model/pathways.json` costs/durations to real qualification hours
  is a second follow-up; the report's pathway table is its input.
- Reviewer should scrutinize: politeness delay actually enforced, fixtures
  small (truncated pages, not full dumps), and no scraped content committed
  that exceeds what the analysis needs.
