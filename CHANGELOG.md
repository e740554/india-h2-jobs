# Changelog

All notable changes to this project will be documented in this file.

## [1.1.1.0] - 2026-03-30

### Added
- Test framework: pytest + pytest-cov bootstrapped with 21 unit tests for `build/build.py`
  pipeline functions (`pct`, `merge_scores`, `compute_upskill_paths`, `compute_workforce_gap`,
  `compute_summary_metrics`, `compute_data_quality`)
- GitHub Actions CI workflow (`.github/workflows/test.yml`) running on every push and PR
- `TESTING.md` documenting test conventions, layers, and how to run coverage
- `TODOS.md` tracking planned work: branding polish, DESIGN.md, test coverage expansion,
  and frontend O(n²) optimization
- `VERSION` file initialized at `1.1.1.0`

### Changed
- `CLAUDE.md`: added `## Testing` section with run commands and coverage expectations
- `requirements.txt`: added `pytest` and `pytest-cov` so `pip install -r requirements.txt`
  gives a complete dev environment

### Fixed
- Adversarial review: renamed misleading test `test_compute_workforce_gap_returns_none_when_no_h2_ready_occupations`
  — it actually returns the full target gap when eligible occupations list is empty; added
  explanatory comment documenting the vacuous-true behavior
