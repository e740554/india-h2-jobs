# Plan 006: Defer click-only score detail payloads

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: `plans/001-shared-model-contracts.md`
- **Category**: perf
- **Planned at**: commit `273a4c1`, 2026-07-15

## Why this matters

The initial `docs/occupations.json` is 909 KB. About 281 KB of its compact
representation is `score_details`, which the runtime reads only when an
occupation is selected. The app cannot first-render until that entire payload
has been fetched and parsed.

## Scope

In scope: `build/build.py`, `web/main.js.template`, associated tests and
generated assets. Out of scope: score semantics, CSV column definitions,
all-occupation lazy-loading behavior, and any network/API backend.

## Steps

1. Add a build test that produces a compact occupation index without
`score_details` and a keyed detail sidecar with every rationale.
2. Update the runtime to load/cache detail data on first sidebar selection and
show a clear non-blocking state on a failed detail fetch.
3. Keep numeric scores in the initial index so treemap, scenario, gap, filters,
and exports preserve current behavior.
4. Establish a payload-budget assertion for the initial index and an
index-to-detail join test.

## Verification

- Initial atlas render still works when detail sidecar loading is delayed.
- Score rationale appears after selection once the detail sidecar resolves.
- `python -m pytest`, JS syntax checks, and a manual local HTTP preview pass.

## STOP conditions

Stop if a rationale is used by scenario, gap, or CSV logic; retain it in the
initial payload rather than breaking data behavior for a size target.
