# India H2 Workforce Atlas

## What This Is

Open-source Python pipeline plus D3 treemap for a scored green-hydrogen occupation atlas. Current checked-in build: 1,802 scored NCS occupations, with a default filtered view of 480 occupations across 12 H2-relevant sectors.

## Architecture

```text
scrape/ -> parse/ -> tabulate/ -> score/ -> build/
NCS Portal   normalize   occupations.csv   Claude Code   docs/ publish output
PLFS PDF     dedupe                       6 dimensions   + JSON/CSV + main.js
NCVET/NQR                                  scores.json   web/ ignored dev copies
```

## Key Commands

```bash
# Full pipeline
python scrape/scrape_ncs.py          # Scrape NCS Portal (pagination + resume support)
python parse/parse_occupations.py    # Parse raw data
python tabulate/tabulate.py          # Generate occupations.csv
python score/score.py --dry-run      # Check what needs scoring
python score/merge_results.py        # Merge batch results into scores.json
python build/build.py --base-url ""  # Build docs/ publish output + web/ dev copies

# Published build preview
cd docs && python -m http.server 8080

# Frontend source preview after a build
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

`web/` is the source tree for static assets and `main.js.template`.
`docs/` is the committed GitHub Pages output.
The build also writes ignored dev copies into `web/` so local preview stays simple.

Do not edit generated files in `docs/` by hand. Rebuild from source instead.

```bash
python build/build.py --base-url ""
```

## Testing

```bash
python -m pytest          # Run all tests
python -m pytest -v       # Verbose output
```

Test directory: `tests/`. See `TESTING.md` for full documentation.

- 100% test coverage is the goal — tests make vibe coding safe
- When writing new functions, write a corresponding test
- When fixing a bug, write a regression test
- When adding a conditional (if/else), write tests for BOTH paths
- Never commit code that makes existing tests fail
