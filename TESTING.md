# Testing

100% test coverage is the key to great vibe coding. Tests let you move fast, trust your instincts, and ship with confidence — without them, vibe coding is just yolo coding. With tests, it's a superpower.

## Framework

**pytest 9.x** + **pytest-cov 7.x**

## How to Run

```bash
# Run all tests
python -m pytest

# With coverage report
python -m pytest --cov=build --cov=parse --cov=tabulate --cov-report=term-missing

# Verbose output
python -m pytest -v
```

## Test Layers

### Unit tests (`tests/test_build.py`)
Pure function tests — no file I/O, no network. Each test exercises a single function with clear inputs and meaningful assertions about what the code does.

Currently covers `build/build.py` (23 tests):
- `pct()` — percentage calculation including zero-division guard
- `count_present()` / `count_true()` — field counting with None handling
- `merge_scores()` — score attachment with dict format, raw format, and missing occupation
- `compute_upskill_paths()` — top-5 ranking, self-exclusion, sector isolation, missing-score skip
- `compute_workforce_gap()` — gap formula, None-return conditions, zero-clamp
- `compute_summary_metrics()` — h2_ready and fast_upskill counts
- `compute_data_quality()` — labour_market_status (pending/complete), notes generation
- `sync_model_data()` — model JSON copying with missing-file warning

### Scenario engine tests (`tests/test_compute.py`)
29 tests covering `model/compute.py`:
- `load_archetype()` / `load_scenarios()` — file loading and ID lookup
- `compute_demand()` / `compute_demand_for_units()` — 5-step model chain: zero/negative target, single/multiple occupations, equal/unequal weights, missing scores, no matching NCO group, unallocated demand, integer rounding, source field preservation, linear scaling
- `aggregate_demand()` — total/phase/group/occupation summaries, mathematical consistency
- `export_demand_csv()` — file writing, column correctness, unallocated rows
- Full pipeline integration with real archetype data

### Multi-archetype tests (`tests/test_multi_archetype.py`)
18 tests covering multi-archetype demand computation:
- `compute_demand_for_units()` — basic, zero units, archetype_id in records
- Single-archetype fallback — old format compatibility
- Multi-archetype chain — production split, downstream conversion, upstream RE derivation, full chain
- Edge cases — zero target, missing archetypes skipped, upstream with no production

### Gap tests (`tests/test_gap.py`)
12 tests covering `compute_gap()`:
- Surplus, shortage, balanced, no_data status values
- gap_pct formula and zero-demand handling
- Multiple occupations with mixed statuses
- Sorted output, empty inputs, zero supply

### Supply tests (`tests/test_supply.py`)
11 tests covering `model/supply.py`:
- `load_supply()` — missing file, valid JSON
- `allocate_supply()` — weighted distribution, equal split, missing subdivisions, conservation check, source fields, multiple subdivisions

### Parity tests (`tests/test_parity.py`)
3 tests verifying Python `compute.py` and JavaScript `computeScenarioDemand()` produce identical results:
- Demand match at 1 MT and 5 MT targets
- Total workforce demand sum consistency

### Integration tests
Not yet implemented. Key target: full `build.py` run against a small fixture CSV + scores JSON, asserting the shape and content of `occupations.json`.

### E2E / smoke tests
Not yet implemented. Key target: `python build/build.py --base-url ""` succeeds end-to-end on the real data files.

## Conventions

- Test files: `tests/test_<module>.py`
- Test functions: `test_<what_it_tests>()`
- Helper factories: `_make_<thing>()` (leading underscore, no pytest collection)
- No mocking of pure functions — pass real data structures
- Never test implementation details; test what the function returns or changes

## CI

GitHub Actions runs `python -m pytest` on every push and PR. See `.github/workflows/test.yml`.
