# India H2 Workforce Atlas

An open-source scored occupation atlas for India's green hydrogen transition. The current checked-in build contains 1,802 scored occupations from the NCS portal, with a default filtered view of 480 occupations across 12 H2-relevant sectors.

Labour-market joins are still incomplete in this release. PLFS employment, wage, and formality fields are not populated in the checked-in dataset yet, so employment-based headline metrics should be treated as unavailable until those joins land.

**Live atlas:** [hygoat.in/workforce-atlas](https://hygoat.in/workforce-atlas) (canonical)  
**Mirror:** [ekavikalp.github.io/india-h2-jobs](https://ekavikalp.github.io/india-h2-jobs)

## Architecture

```text
[ Data Pipeline ]     [ LLM Scoring ]     [ Scenario Engine ]     [ Frontend Atlas ]
  Python scripts        Claude Code         model/archetypes.json   Static HTML/JS/D3
  NCS scraper +         6 H2-centric        model/compute.py        Treemap + scenario mode
  planned PLFS/NCVET    dimensions           MT -> demand chain      + slider + CSV download
  -> occupations.csv    -> scores.json                               -> hygoat.in/workforce-atlas
```

## Data Sources

| Source | Coverage | Access |
|--------|----------|--------|
| **NCS Portal** (ncs.gov.in) | Current checked-in build: 1,802 scored occupations | HTTP scraper over SharePoint inline JSON |
| **PLFS** (NSO 2023-24) | Planned employment, wage, and formalization joins | Download scaffold only in current repo |
| **NCVET / NQR** | Planned qualification and transition-path joins | Not yet merged into checked-in build |

## Scoring Dimensions (0-10)

| Dimension | What it measures |
|-----------|-----------------|
| H2 Value Chain Adjacency | Direct presence in electrolysis, compression, storage, distribution, or fuel cell operations |
| Green Transition Demand | Whether demand should rise as India scales green hydrogen |
| Skill Transferability | How quickly someone in the role can upskill into H2-specific work |
| Digital Automation Exposure | Exposure to AI or robotics over the next 5-10 years |
| Formalization Rate | Expected formality of employment in India |
| H2 Talent Scarcity Risk | Whether the skill is likely to bottleneck scale-up |

## Repository Layout

- `web/` - source for the static shell, styles, logo, and `main.js.template`
- `docs/` - generated GitHub Pages output committed to git
- `model/` - scenario engine: archetype definitions, coefficients, and Python validation engine
- `tests/` - pytest unit tests for the pipeline and Python/JS parity
- `occupations.csv` - checked-in source tabulation for the current build
- `scores.json` - checked-in scoring output for the current build

Generated JSON, CSV, and compiled JS do not belong in the repo root.

## Quick Start

**Pre-built data ships with this repo.** If you only want to inspect the current published build:

```bash
cd docs && python -m http.server 8080
# Open http://localhost:8080
```

To run the test suite (see [TESTING.md](TESTING.md) for details):

```bash
python -m pytest
```

If you are editing the frontend source and want the ignored local-dev copies that mirror the build output:

```bash
python build/build.py --base-url ""
cd web && python -m http.server 8080
```

### Full Pipeline (maintainers only)

```bash
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt && playwright install chromium

python scrape/scrape_ncs.py        # Scrape NCS Portal
python scrape/download_plfs.py     # Download PLFS source PDFs
python parse/parse_occupations.py  # Parse raw data
python tabulate/tabulate.py        # Generate occupations.csv
python score/score.py              # Score via Claude Code
python build/build.py              # Merge -> docs/ publish output + web/ dev copies
```

## Current Build Status

- Scored occupation atlas: available
- NCS sector scrape completeness: pending pagination rerun
- PLFS joins: not populated in checked-in dataset
- NCVET joins: not populated in checked-in dataset

## Open Source Workflow

- Edit source files in `web/`, not generated files in `docs/`
- Run `python build/build.py --base-url ""` before opening a PR
- Commit regenerated `docs/` assets when the published atlas changes
- Do not commit ignored local-dev files in `web/` or generated root artifacts

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor workflow.

## License

MIT - see [LICENSE](LICENSE).

## Credits

Built by [HyGOAT](https://hygoat.in) and [Ekavikalp Pvt Ltd](https://ekavikalp.com)  
Data: NCS Portal (current build), PLFS 2023-24 and NCVET/NQR (planned joins)  
Scoring: Claude AI (open-source prompts in `prompts/`)
