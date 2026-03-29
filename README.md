# India H2 Workforce Atlas

An open-source scored occupation atlas and scenario engine for India's green hydrogen transition. Translates national hydrogen capacity targets (in megatonnes) into occupation-level workforce demand estimates using real NCS occupation data, LLM-scored relevance dimensions, and asset-level staffing coefficients.

**Live atlas:** [hygoat.in/workforce-atlas](https://hygoat.in/workforce-atlas) (canonical)
**Mirror:** [e740554.github.io/india-h2-jobs](https://e740554.github.io/india-h2-jobs/)

## What It Does

1. **Scrapes** 1,802 occupations from India's National Career Service (NCS) portal
2. **Scores** each occupation on 6 hydrogen-relevance dimensions (0–10) using Claude AI with open-source prompts
3. **Filters** to 480 occupations across 12 H2-relevant sectors as the default view
4. **Models** workforce demand: set a hydrogen capacity target (MT) on a slider → the scenario engine cascades demand through asset archetypes → per-occupation headcount estimates appear on an interactive D3 treemap
5. **Exports** scored data as CSV for downstream analysis

## Scoring Dimensions (0–10)

| Dimension | What it measures |
|-----------|-----------------|
| H2 Value Chain Adjacency | Direct presence in electrolysis, compression, storage, distribution, or fuel cell operations |
| Green Transition Demand | Whether demand should rise as India scales green hydrogen |
| Skill Transferability | How quickly someone in the role can upskill into H2-specific work |
| Digital Automation Exposure | Exposure to AI or robotics over the next 5–10 years |
| Formalization Rate | Expected formality of employment in India |
| H2 Talent Scarcity Risk | Whether the skill is likely to bottleneck scale-up |

## Scenario Engine

The scenario engine translates hydrogen capacity targets into occupation-level workforce demand:

```
MT target → plant units (via archetype capacity) → per-NCO-group raw headcount
→ allocation by (h2_adjacency + transition_demand) weights → rounded demand per occupation
```

- **Archetypes** (`model/archetypes.json`): asset definitions with per-NCO-group staffing coefficients by project phase (construction, commissioning, operations)
- **Scenarios** (`model/scenarios.json`): NGHM preset scenarios (1 MT, 5 MT, 10 MT)
- **Python engine** (`model/compute.py`): `compute_demand()`, `aggregate_demand()`, `export_demand_csv()` — used for validation and CSV export
- **JS engine** (`web/main.js.template`): `computeScenarioDemand()` — runtime engine in the browser, must match Python exactly

## Quick Start — View the Atlas Locally

Pre-built data ships with this repo. No pipeline run needed.

```bash
git clone https://github.com/e740554/india-h2-jobs.git
cd india-h2-jobs/docs
python -m http.server 8080
# Open http://localhost:8080
```

## Quick Start — Reproduce From Scratch

To regenerate all data from source and rebuild the atlas:

### Prerequisites

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (for LLM scoring step only)

### Steps

```bash
# 1. Set up environment
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 2. Scrape occupations from NCS portal
python scrape/scrape_ncs.py         # Outputs scrape/raw/*.json (supports resume)

# 3. Parse and tabulate
python parse/parse_occupations.py   # Produces parse/parsed_occupations.json
python tabulate/tabulate.py         # Produces occupations.csv

# 4. Score occupations (requires Claude Code CLI)
python score/score.py               # Prepares batch files in score/batches/
# Claude Code subagents read batches and write *_results.json
python score/merge_results.py       # Merges results → scores.json

# 5. Build the atlas
python build/build.py --base-url "" # Outputs to docs/ (publish) and web/ (dev)

# 6. Preview
cd docs && python -m http.server 8080
```

### Scoring Details

Scoring uses Claude Code subagents, not the Anthropic API directly:
1. `score/score.py` prepares batch JSON files in `score/batches/`
2. Claude Code subagents read each batch and produce `*_results.json` files with 0–10 scores across all 6 dimensions
3. `score/merge_results.py` combines all results into `scores.json`

To check what needs scoring without running it: `python score/score.py --dry-run`

To score a single sector: `python score/score.py --sector Power`

## Repository Layout

```
india-h2-jobs/
├── scrape/                  # NCS portal scraper + PLFS download scaffold
│   ├── scrape_ncs.py        # SharePoint inline JSON scraper with pagination + resume
│   └── download_plfs.py     # PLFS PDF download (planned)
├── parse/                   # Raw data → structured JSON
│   └── parse_occupations.py
├── tabulate/                # Structured JSON → occupations.csv
│   └── tabulate.py
├── score/                   # LLM scoring pipeline
│   ├── score.py             # Batch preparation
│   ├── merge_results.py     # Result aggregation → scores.json
│   └── config.py            # Scoring configuration
├── model/                   # Scenario engine
│   ├── archetypes.json      # Asset archetypes + staffing coefficients
│   ├── scenarios.json       # NGHM preset scenarios
│   ├── compute.py           # Python validation engine
│   └── supply.py            # Supply-side computation (Phase 2)
├── build/                   # Static site builder
│   └── build.py             # Merges data + templates → docs/ + web/
├── web/                     # Frontend source
│   ├── index.html           # Atlas shell
│   ├── style.css            # Styles
│   ├── main.js.template     # JS engine (template — build.py fills __BASE_URL__)
│   └── hygoat-logo.svg      # Logo asset
├── docs/                    # Generated GitHub Pages output (committed)
├── tests/                   # Pytest suite (96 tests)
│   ├── test_compute.py      # 29 scenario engine tests
│   ├── test_multi_archetype.py # 18 multi-archetype demand tests
│   ├── test_gap.py          # 12 supply-demand gap tests
│   ├── test_supply.py       # 11 supply allocation tests
│   ├── test_parity.py       # Python/JS parity verification
│   └── parity_check.js      # Node.js JS engine mirror for parity tests
├── occupations.csv          # Checked-in source tabulation
├── scores.json              # Checked-in scoring output
└── requirements.txt         # Python dependencies
```

## Data Sources

| Source | Coverage | Access Method | Status |
|--------|----------|---------------|--------|
| **NCS Portal** (ncs.gov.in) | 1,802 scored occupations | HTTP scraper over SharePoint inline JSON | ✅ Current build |
| **PLFS** (NSO 2023–24) | Employment, wage, formalization | PDF table extraction | 🔲 Planned |
| **NCVET / NQR** (nqr.gov.in) | Qualification and transition paths | Server-rendered HTML | 🔲 Planned |

See [DATASOURCES.md](DATASOURCES.md) for full documentation.

## Testing

```bash
python -m pytest           # Run all tests
python -m pytest -v        # Verbose output
python -m pytest --cov     # With coverage report
```

See [TESTING.md](TESTING.md) for full documentation.

## Adapting This for Another Country or Sector

The pipeline is designed to be reusable. To build a similar atlas for a different context:

1. **Replace the scraper** — write a new `scrape/scrape_*.py` that outputs occupation data in the same JSON schema (see `parse/parsed_occupations.json` for the expected structure)
2. **Adjust scoring prompts** — the scoring dimensions in `score/config.py` are hydrogen-specific; modify them for your sector
3. **Define archetypes** — edit `model/archetypes.json` with your asset types and staffing coefficients per NCO occupation group
4. **Rebuild** — run the pipeline from step 3 onward

## Roadmap

- **Phase 1** (shipped v1.2): One archetype (alkaline electrolyser), 48 coefficients, interactive slider, demand treemap
- **Phase 2** (shipped v1.3): 4 archetypes (alkaline, PEM, ammonia, solar+wind), multi-archetype scenarios, supply gap engine with PLFS baseline, 3-way Atlas/Scenario/Gap mode
- **Phase 3** (planned): Geography/cluster distribution, time phasing, reskilling pathway estimates

## Contributing

- Edit source files in `web/`, not generated files in `docs/`
- Run `python build/build.py --base-url ""` before opening a PR
- Commit regenerated `docs/` assets when the published atlas changes
- Do not commit ignored local-dev files in `web/` or generated root artifacts

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor workflow.

## License

MIT — see [LICENSE](LICENSE).

## Credits

Built by [HyGOAT](https://hygoat.in) and [Ekavikalp Pvt Ltd](https://ekavikalp.com)
Data: NCS Portal (current build), PLFS 2023–24 and NCVET/NQR (planned joins)
Scoring: Claude AI — [open-source prompts and pipeline](https://github.com/e740554/india-h2-jobs)
