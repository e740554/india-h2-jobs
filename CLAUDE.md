# India H2 Workforce Atlas

## What This Is

Open-source Python pipeline plus D3 treemap for a scored green-hydrogen occupation atlas with interactive scenario engine. Current checked-in build: 1,802 scored NCS occupations, with a default filtered view of 480 occupations across 12 H2-relevant sectors. Phase 1 scenario engine ships one archetype (1 GW alkaline electrolyser) with 48 occupation coefficients and a demand slider.

## Architecture

```text
scrape/ -> parse/ -> tabulate/ -> score/ -> build/
NCS Portal   normalize   occupations.csv   Claude Code   docs/ publish output
PLFS PDF     dedupe                       6 dimensions   + JSON/CSV + main.js
NCVET/NQR                                  scores.json   web/ ignored dev copies

model/archetypes.json   (asset archetypes + occupation coefficients)
model/scenarios.json    (NGHM scenario presets)
model/compute.py        (Python validation + CSV export, mirrors JS engine)
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

# Scenario engine validation
python -c "from model.compute import load_archetype, compute_demand; ..."
python -m pytest tests/test_compute.py -v   # 29 compute engine tests
python -m pytest tests/test_parity.py -v    # Python/JS parity verification
```

## Scenario Engine

The scenario engine translates hydrogen capacity targets (MT) into occupation-level workforce demand. The JS engine in `web/main.js.template` is the runtime; `model/compute.py` is a validation mirror.

**Model chain:** MT target → plant units → per-coefficient raw demand → NCO group matching (`nco_code[:4]`) → allocation by `h2_adjacency + transition_demand` weights → rounded integer demand per occupation.

**Files:**
- `model/archetypes.json` — asset archetype with per-NCO-group headcount coefficients by phase
- `model/scenarios.json` — NGHM preset scenarios (1 MT, 5 MT, 10 MT)
- `model/compute.py` — Python engine: `compute_demand()`, `aggregate_demand()`, `export_demand_csv()`
- `web/main.js.template` — JS engine: `computeScenarioDemand()` (must match Python exactly)

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
