# India H2 Workforce Atlas

## What This Is

Open-source Python pipeline + D3.js treemap that maps India's occupational landscape through a green hydrogen lens. Inspired by Karpathy's `jobs` repo.

## Architecture

```
scrape/ -> parse/ -> tabulate/ -> score/ -> build/ -> web/
NCS Portal   normalize   occupations.csv   Claude Code   occupations.json   D3 treemap
PLFS PDF     deduplicate                   6 dimensions  + main.js           + sidebar
NCVET/NQR                                 scores.json   + CSV exports       + CSV download
```

## Key Commands

```bash
# Full pipeline
python scrape/scrape_ncs.py          # Scrape NCS Portal (1.5s delay, resume support)
python parse/parse_occupations.py    # Parse raw data
python tabulate/tabulate.py          # Generate occupations.csv
python score/score.py --dry-run      # Check what needs scoring
python score/merge_results.py        # Merge batch results into scores.json
python build/build.py --base-url ""  # Build occupations.json + web/main.js

# Dev server
cd web && python -m http.server 8080

# Scoring (via Claude Code subagents, not API)
python score/score.py --sector Power  # Create batch files for one sector
python score/merge_results.py         # After subagents write results
```

## Scoring

Scoring is done via Claude Code subagents — no API key needed. The pipeline:
1. `score.py` prepares batch JSON files in `score/batches/`
2. Claude Code subagents read batches and write `*_results.json`
3. `merge_results.py` combines results into `scores.json`

## Data Sources

- **NCS Portal** (ncs.gov.in) — SharePoint inline JSON, no Playwright needed
- **PLFS** (mospi.gov.in) — Annual Report PDF tables
- **NCVET/NQR** (nqr.gov.in) — Server-rendered HTML, open robots.txt

See `DATASOURCES.md` for full documentation.

## Deployment

GitHub Pages from `web/` directory. No CI/CD — manual push.

```bash
python build/build.py --base-url ""   # builds occupations.json + web/main.js + copies to web/
# Push to ekavikalp/india-h2-jobs, enable GitHub Pages on web/ folder
```

## Build Modes

- `--base-url ""` — GitHub Pages (root of repo's Pages site) or local dev
