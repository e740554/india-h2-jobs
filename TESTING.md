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
python build/build.py --base-url "/workforce-atlas"
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

### Briefing and state summary tests

- `tests/test_briefing.py` and `tests/briefing_check.js`
- `tests/test_state_summary.py`
- load the browser runtime in Node the same way `tests/parity_check.js` does, then cover the pure presentation builders: briefing model shape, demand-row truncation with an honest omitted count, gap-mode gating, dataset version in the citation line, per-state aggregation across clusters, deterministic ordering, and the caveat row that travels inside the state summary CSV
- these builders are presentation logic, not shared model math. They live in the JS runtime only and deliberately have no Python mirror or parity entry

### Release metadata tests

- `tests/test_citation.py`
- asserts `CITATION.cff` carries the same `version` as the `VERSION` file and the same `date-released` as that version's `CHANGELOG.md` heading. It fails by design after a version bump until `CITATION.cff` is updated, which makes citation drift impossible

### QR asset tests

- `tests/test_qr.py`
- split deliberately into two kinds. Generation tests run `scripts/generate_qr.py --output-dir <tmp_path>` and assert both assets are produced; asset tests read `assets/` read-only and check the committed SVG viewBox, the PNG minimum size, and that the committed QR still encodes the Atlas root URL in `URL_FREEZE.md`
- a test run must never rewrite the checked-in assets, and one test asserts exactly that. Regenerate them deliberately with `python scripts/generate_qr.py` when the frozen URL changes
- the drift check compares SVG path geometry, not raw bytes: `qrcode` versions differ in attribute spacing, which would otherwise make the comparison flaky

### Assumptions register tests

- `tests/test_assumptions_register.py`
- checks the exact header, that every archetype `headcount_per_unit` appears exactly once, that each pathway contributes three rows, that no `source_type` cell is empty, and that two consecutive builds produce byte-identical output

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

## CI and deployment verification

GitHub Actions runs `python -m pytest` plus a deterministic production build on
push and pull request. A deployment is not complete until the relevant Actions
run passes and both published URLs serve the page plus its runtime assets:

```powershell
.\scripts\smoke_prod.ps1
.\scripts\smoke_prod.ps1 -BaseUrl "https://e740554.github.io/india-h2-jobs"
```
