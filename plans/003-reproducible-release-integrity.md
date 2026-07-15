# Plan 003: Make the published release reproducible and self-contained

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: `plans/001-shared-model-contracts.md`
- **Category**: dx
- **Planned at**: commit `273a4c1`, 2026-07-15

## Why this matters

GitHub Pages serves committed `docs/`, while CI currently runs only pytest.
The build duplicates the version string and injects `date.today()`, so a clean
rebuild of the same commit is not byte-stable. The production page also executes
a mutable third-party D3 URL without integrity protection.

## Current state

~~~python
# build/build.py:49 and :529-530
DATASET_VERSION = "1.4.3.0"
"last_updated": date.today().isoformat(),
~~~

~~~yaml
# .github/workflows/test.yml:15-18
- run: pip install -r requirements.txt
- run: python -m pytest
~~~

`VERSION` is the release source of truth by repository convention.
`web/index.html:183` loads `https://d3js.org/d3.v7.min.js`.

## Scope

In scope: `VERSION`, `build/build.py`, `web/index.html`, dependency manifests,
CI workflow, tests, and generated output. Out of scope: framework migration,
unrelated visual redesign, deploying/pushing, and changing frozen URLs.

## Steps

1. Add failing tests that require build metadata to derive from `VERSION` and
require a deterministic build-date input rather than wall-clock time.
2. Implement one release-metadata source and a documented build-date mechanism
that defaults to an intentional checked-in release value or explicit argument.
3. Vendor a reviewed exact D3 v7 build as a same-origin static asset, update
`web/index.html`, and add an assertion that forbids executable unpinned CDN
scripts. Preserve current D3 API compatibility.
4. Inventory Python/Node workflows, remove no-consumer dependencies only after
their documented manual paths are checked, split optional browser/scrape tools
from CI requirements, and pin the CI-resolved dependency set.
5. Add `setup-node` with the documented Node 18+ baseline and a CI job that
builds using `/workforce-atlas`, syntax-checks output, and fails on unexpected
tracked generated drift.

## Verification

- `python -m pytest` passes.
- `python build/build.py --base-url "/workforce-atlas"` twice with the same
  declared metadata produces no second-run diff.
- `node --check web/main.js` and `node --check docs/main.js` exit 0.
- CI checks generated artifact drift without hand-editing `docs/`.

## STOP conditions

Stop if a pinned dependency or D3 asset cannot be acquired from an approved
source, or if changing a frozen URL is required.
