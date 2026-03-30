# Testing

The repo uses `pytest` for Python coverage plus a small Node harness for Python/JS parity checks against the browser runtime.

## Main Commands

Run the full suite:

```bash
python -m pytest
```

Run a focused Phase 3 verification slice:

```bash
python -m pytest tests/test_parity.py tests/test_ui_logic.py tests/test_csv_export.py
```

Rebuild generated assets and syntax-check the browser bundles:

```bash
python build/build.py --base-url ""
node --check web/main.js
node --check docs/main.js
```

## Test Layers

### Build and pipeline tests

- `tests/test_build.py`
- validates score merging, summary metrics, data-quality fields, and model-data sync behavior

### Core demand engine tests

- `tests/test_compute.py`
- covers archetype/scenario loading, demand allocation, aggregation, and CSV export helpers

### Multi-archetype scenario tests

- `tests/test_multi_archetype.py`
- covers production, downstream, and upstream scenario composition

### Gap and supply tests

- `tests/test_gap.py`
- `tests/test_supply.py`
- cover supply-demand status logic and PLFS subdivision allocation helpers

### Phase 3 geography/timeline/pathway tests

- `tests/test_clusters.py`
- `tests/test_timeline.py`
- `tests/test_pathways.py`
- cover cluster affinity validation, cluster distribution, annual timeline snapshots, pathway validation, lookup, and reskillable supply helpers

### Runtime parity tests

- `tests/test_parity.py`
- `tests/parity_check.js`
- load `web/main.js.template` in Node and compare Python and JS outputs for demand, cluster distribution, and timeline snapshots

### UI logic and export tests

- `tests/test_ui_logic.py`
- `tests/test_csv_export.py`
- cover runtime-only helpers such as `dominantPhase()`, cluster suggestion logic, and full-snapshot CSV row generation

## Conventions

- Test files live in `tests/test_<module>.py`
- Helper factories use `_make_<thing>()`
- Test behavior, invariants, and output shape rather than internal implementation details
- Keep Python and JS runtime behavior aligned when changing shared model logic

## When To Add Tests

Add or extend tests whenever you change:

- archetype/scenario schemas
- demand allocation or rounding rules
- cluster distribution logic
- timeline phase behavior
- pathway/export logic
- build output fields consumed by the frontend

## CI

GitHub Actions runs `python -m pytest` on push and pull request.
