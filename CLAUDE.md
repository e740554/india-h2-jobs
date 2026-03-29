# India H2 Workforce Atlas

## What This Is

Open-source Python pipeline plus D3 treemap for a scored green-hydrogen occupation atlas. Current checked-in build: 1,802 scored NCS occupations, with a default filtered view of 480 occupations across 12 H2-relevant sectors.

## Architecture

```text
scrape/ -> parse/ -> tabulate/ -> score/ -> build/ -> web/ + docs/
NCS Portal   normalize   occupations.csv   Claude Code   occupations.json   D3 treemap
PLFS PDF     dedupe                       6 dimensions  + main.js           + sidebar
NCVET/NQR                                  scores.json  + CSV exports       + CSV download
```

## Key Commands

```bash
# Full pipeline
python scrape/scrape_ncs.py          # Scrape NCS Portal (pagination + resume support)
python parse/parse_occupations.py    # Parse raw data
python tabulate/tabulate.py          # Generate occupations.csv
python score/score.py --dry-run      # Check what needs scoring
python score/merge_results.py        # Merge batch results into scores.json
python build/build.py --base-url ""  # Build JSON + public assets

# Dev server
cd web && python -m http.server 8080

# Scoring (via Claude Code subagents, not API)
python score/score.py --sector Power
python score/merge_results.py
```

## Scoring

Scoring is done via Claude Code subagents, not the API:
1. `score.py` prepares batch JSON files in `score/batches/`
2. Claude Code subagents read batches and write `*_results.json`
3. `merge_results.py` combines results into `scores.json`

## Data Sources

- **NCS Portal** (ncs.gov.in) - SharePoint inline JSON, no Playwright needed
- **PLFS** (mospi.gov.in) - Annual Report PDF tables, not yet populated in the checked-in dataset
- **NCVET/NQR** (nqr.gov.in) - Server-rendered HTML, not yet populated in the checked-in dataset

See `DATASOURCES.md` for full documentation.

## Deployment

GitHub Pages mirror from `docs/` plus local/dev assets in `web/`. No CI/CD; manual push.

```bash
python build/build.py --base-url ""
```
