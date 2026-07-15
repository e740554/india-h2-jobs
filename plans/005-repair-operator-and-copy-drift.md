# Plan 005: Repair local-preview guidance and retired public copy

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: `plans/003-reproducible-release-integrity.md`
- **Category**: docs
- **Planned at**: commit `273a4c1`, 2026-07-15

## Why this matters

The local runbook opens a `file://` page although runtime JSON is loaded with
`fetch`. The public About metadata and a TODO still describe an Advisory Circle
that a founder decision removed. Both create avoidable operator and credibility
drift.

## Scope

In scope: `RUNBOOK.md`, `tests/test_runbook.py`, `web/about/index.html`,
`TODOS.md`, associated generated About page, and focused tests. Out of scope:
changing URLs in `URL_FREEZE.md`, restoring the Advisory Circle, adding
analytics, or inventing institutional/funding claims without founder text.

## Steps

1. Update the local preview path to build with an empty base URL, serve `docs/`
   with `python -m http.server 8080`, and state the browser URL.
2. Extend runbook tests to assert the usable command/URL, not just headings.
3. Change About page title/description/Open Graph copy to the approved
   contact-only reality, remove dead Advisory Circle-only CSS, and update the
   TODO wording so a later institutional-grounding task starts from reality.
4. Rebuild generated pages and verify frozen paths remain unchanged.

## Verification

- `python -m pytest tests/test_runbook.py tests/test_build.py tests/test_url_freeze.py` passes.
- A local HTTP preview loads `occupations.json` without a browser fetch error.
- No new factual institutional claim appears without founder approval.
