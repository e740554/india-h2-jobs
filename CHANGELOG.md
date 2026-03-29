# Changelog

All notable changes to this project will be documented in this file.

## [1.3.0.0] - 2026-03-30

### Added
- **Supply gap engine (Phase 2)** — 3-way Atlas/Scenario/Gap mode toggle. Gap mode shows
  red (shortage) to green (surplus) treemap with per-occupation supply vs. demand breakdown
- **3 new archetypes** — PEM electrolyser (500 MW), green ammonia synthesis (1 MTPA), and
  dedicated solar+wind hybrid (2 GW) with full coefficient arrays across project phases
- **Multi-archetype scenarios** — composable scenarios with production/downstream/upstream
  chains. 4 new presets: 1 MT pilot, 5 MT mixed, 10 MT ambitious, Adani Kutch Phase 1
- **PLFS supply baseline** — `model/supply.py` loads and allocates PLFS 2023-24 labour
  supply estimates by NCO subdivision to individual occupations
- **Scenario preset dropdown** — select from NGHM scenario presets, slider syncs to target
- **67 new tests** — `test_multi_archetype.py` (18), `test_gap.py` (12), `test_supply.py` (11),
  plus updated `test_compute.py` for backwards compatibility (96 total)
- **Gap sidebar** — per-occupation supply, demand, gap, and percentage breakdown
- **Archetype breakdown** — sidebar shows demand contribution from each archetype

### Changed
- Scenario mode colours use brand palette (green→red) instead of orange gradient
- Footer shows GitHub icon+link instead of plain text attribution
- Logo image removed from header nav
- README rewritten as comprehensive self-explanatory guide
- Scenario bar updated with preset dropdown and expanded MT slider range (0.5-15)
- `build.py` merges PLFS supply data and writes explicit null supply fields

### Fixed
- `decodeEntities()` regression — HTML entities in 22 occupation titles now render correctly
  (DOMParser-based decoder replaces broken textContent pattern)
- JS/Python parity for NCO 9312 — unallocated demand now tracked in JS engine (was silently
  dropped, causing ~12% under-report for RE scenarios)
- Phase bar division-by-zero edge case when demand rounds to 0
- Slider/scenario initial state mismatch on first mode switch

### Removed
- `CLAUDE.md` untracked from git (moved to .gitignore, local-only)

## [1.2.0.0] - 2026-03-30

### Added
- **Scenario engine (Phase 1)** — set an MT hydrogen capacity target on a slider and see
  occupation-level workforce demand cascade across the treemap. One archetype (1 GW alkaline
  electrolyser) with 48 occupation coefficients across construction, commissioning, and operations
- **Atlas/Scenario mode toggle** — switch between the scored occupation atlas and the demand
  scenario model. Scenario mode shows orange demand-intensity tiles, phase breakdown per
  occupation, and coefficient provenance in the sidebar
- **`model/` directory** — `archetypes.json` (asset archetypes with occupation coefficients),
  `scenarios.json` (3 NGHM presets: 1 MT/2027, 5 MT/2030, 10 MT/2035), and `compute.py`
  (Python validation/export engine matching JS logic)
- **Python/JS parity tests** — verify both engines produce identical demand results for the
  same inputs (tested at 1 MT and 5 MT)
- **29 compute engine tests** — comprehensive pytest coverage for the 5-step model chain
  (MT → units → demand → allocation → aggregation)
- **Build pipeline** copies `archetypes.json` and `scenarios.json` to `docs/` and `web/`

### Changed
- **Summary bar** relabels in scenario mode: "Occupations in Demand", "Total Workforce Demand",
  "Plant Units Needed" — restores original labels when switching back to Atlas mode
- **Treemap sizing** uses demand headcount in scenario mode (instead of H2 relevance scores)
- **Sector toggle** is disabled in scenario mode (demand is archetype-scoped, not sector-filtered)

## [1.1.1.0] - 2026-03-30

### Added
- **21 unit tests** for the build pipeline (`pct`, `merge_scores`, `compute_upskill_paths`,
  `compute_workforce_gap`, `compute_summary_metrics`, `compute_data_quality`) — run with
  `python -m pytest`
- **GitHub Actions CI** runs tests on every push and PR
- **`TESTING.md`** — how to run tests, coverage conventions, and test layer descriptions
- **`TODOS.md`** — planned work backlog: branding polish, DESIGN.md, test coverage expansion,
  and treemap O(n²) optimization

### Changed
- `requirements.txt` now includes `pytest` and `pytest-cov` — `pip install -r requirements.txt`
  gives a complete dev environment with tests ready to run
- `CLAUDE.md` documents the test setup and coverage expectations for contributors

### Fixed
- Clarified the `compute_workforce_gap` edge case when no H2-ready occupations exist:
  the function returns the full target gap (not `None`) due to vacuous evaluation on an empty
  list — documented in tests with an explanatory comment
