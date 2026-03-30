# India H2 Workforce Atlas

[![Tests](https://github.com/e740554/india-h2-jobs/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/e740554/india-h2-jobs/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source occupation atlas and scenario engine for India's green hydrogen transition. It translates hydrogen production targets into occupation-level workforce demand using NCS occupation records, scored relevance dimensions, archetype staffing coefficients, cluster distribution, timeline phasing, and reskilling pathway mappings.

**Live atlas:** [hygoat.in/workforce-atlas](https://hygoat.in/workforce-atlas)  
**Mirror:** [e740554.github.io/india-h2-jobs](https://e740554.github.io/india-h2-jobs/)

## Current Scope

The current build ships:

- 1,802 scored occupations from the National Career Service source data
- a default atlas view of 480 occupations across 12 H2-relevant sectors
- Atlas / Scenario / Gap modes in a single-page D3 treemap
- multi-archetype scenarios spanning production, downstream ammonia, and dedicated RE
- geography filters across hydrogen clusters and cluster-based state rollups
- annual timeline snapshots with phase-based recoloring
- sidebar reskilling pathways with overlap, duration, cost, and bridging skills
- current-view and full-snapshot CSV exports

## What It Does

1. Scrapes occupation records from India's National Career Service portal.
2. Scores each occupation on six hydrogen-relevance dimensions.
3. Builds a default H2-relevant occupation atlas plus a full all-occupation dataset.
4. Models workforce demand from hydrogen targets through asset archetypes and project phases.
5. Distributes demand across hydrogen clusters and state rollups.
6. Generates year-by-year workforce snapshots from `start_year` to `target_year + 5`.
7. Shows inbound and outbound reskilling pathways for occupations in the sidebar.
8. Exports structured CSVs for downstream policy and planning analysis.

## Core Data And Runtime Model

The scenario engine uses this chain:

```text
target MT
-> archetype units
-> per-coefficient raw demand
-> occupation allocation by relevance weights
-> cluster distribution by archetype affinity
-> annual timeline snapshots by phase
-> optional supply-gap comparison and pathway summaries
```

Primary model/runtime assets:

- `model/archetypes.json`: staffing archetypes and per-phase coefficients
- `model/scenarios.json`: preset scenarios with `start_year` and `target_year`
- `model/clusters.json`: hydrogen clusters and cluster-based state groupings
- `model/pathways.json`: occupation-to-occupation reskilling pathway mappings
- `model/compute.py`: core Python demand engine
- `model/clusters.py`: cluster distribution helpers
- `model/timeline.py`: annual snapshot helpers
- `model/pathways.py`: pathway lookup and reskillable supply helpers
- `web/main.js.template`: browser runtime mirroring the Python model logic

## Quick Start

Prebuilt data ships with the repo.

```bash
git clone https://github.com/e740554/india-h2-jobs.git
cd india-h2-jobs/docs
python -m http.server 8080
# Open http://localhost:8080
```

## Rebuild From Source

To regenerate the published/frontend assets:

```bash
python build/build.py --base-url ""
```

That rebuilds:

- `docs/occupations.json`
- `docs/occupations-all.json`
- `docs/main.js`
- `docs/style.css`
- synced dev copies in `web/`

For a full pipeline rebuild from raw data, see the source directories below plus [DATASOURCES.md](DATASOURCES.md).

## Repository Layout

```text
india-h2-jobs/
|- scrape/          NCS and labour-data ingestion helpers
|- parse/           Raw-to-structured occupation transforms
|- tabulate/        Structured JSON to tabular exports
|- score/           LLM scoring pipeline
|- model/           Demand, cluster, timeline, pathway, and supply engines
|- build/           Static site build and data sync pipeline
|- web/             Frontend source of truth
|- docs/            Generated publish output
|- tests/           Pytest suite and Node parity harness
```

Important files:

- `web/index.html`
- `web/style.css`
- `web/main.js.template`
- `tests/parity_check.js`
- `docs/superpowers/specs/2026-03-30-phase3-geography-timeline-pathways-design.md`

## Testing

Run the full suite:

```bash
python -m pytest
```

Useful targeted checks:

```bash
python -m pytest tests/test_parity.py tests/test_ui_logic.py tests/test_csv_export.py
python build/build.py --base-url ""
node --check web/main.js
node --check docs/main.js
```

See [TESTING.md](TESTING.md) for the current test layers.

## Data Sources

Current production data is built primarily from:

- NCS portal occupation records
- scored occupation relevance dimensions
- archetype staffing coefficients
- scenario presets
- cluster affinity mappings
- pathway mappings

PLFS and NCVET remain enrichment layers rather than fully complete upstream joins in the checked-in build. See [DATASOURCES.md](DATASOURCES.md).

## Documentation

- [CHANGELOG.md](CHANGELOG.md): release-by-release shipped changes
- [CONTRIBUTING.md](CONTRIBUTING.md): contributor workflow, tests, and publish expectations
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md): contributor behavior expectations
- [SECURITY.md](SECURITY.md): how to report vulnerabilities privately
- [TESTING.md](TESTING.md): test layers and verification commands
- [DATASOURCES.md](DATASOURCES.md): upstream source coverage and scraping notes
- [DESIGN.md](DESIGN.md): UI system and visual language
- [TODOS.md](TODOS.md): current backlog and follow-up work

## Release History

| Version | Date | Scope |
|---------|------|-------|
| `v1.4.0.0` | 2026-03-30 | Phase 3: geography filters, timeline phasing, pathways, and expanded exports |
| `v1.3.0.0` | 2026-03-30 | Phase 2: multi-archetype scenarios, supply-gap mode, PLFS baseline, and gap sidebar |
| `v1.2.0.0` | 2026-03-30 | Phase 1: scenario engine, archetypes, parity checks, and demand-mode treemap |
| `v1.1.1.0` | 2026-03-30 | Test framework, CI, `TESTING.md`, `TODOS.md`, and formal version/changelog tracking |
| `v1.0.0.0` | 2026-03-29 | Public OSS atlas baseline with 1,802 scored occupations, GitHub Pages publish layout, and contributor docs |

Historical note: the repo already had a `v1.1` branch marker, but the formal tagged release line starts at `v1.1.1.0`. The README and changelog now reflect that explicitly.

## Roadmap Status

- **Phase 1**: shipped. Single-archetype scenario engine and treemap demand mode.
- **Phase 2**: shipped. Multi-archetype scenarios and supply-gap mode.
- **Phase 3**: shipped. Geography filters, timeline phasing, and reskilling pathways.

Current follow-up work is mainly dataset enrichment and UI polish rather than missing Phase 3 functionality.

## Contributing

- Edit source files in `web/`, `model/`, `build/`, and the pipeline directories.
- Do not hand-edit generated assets in `docs/`.
- Rebuild with `python build/build.py --base-url ""` before opening a PR when published output changes.
- Keep README/spec/testing copy aligned with the checked-in dataset and runtime behavior.
- Use the issue and PR templates for public contributions, and follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- Report security issues privately per [SECURITY.md](SECURITY.md), not through public issues.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor workflow.

## License

MIT. See [LICENSE](LICENSE).

## Credits

Built by [HyGOAT](https://hygoat.in) and [Ekavikalp Pvt Ltd](https://ekavikalp.com).
