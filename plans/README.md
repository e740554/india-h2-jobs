# Implementation Plans

Generated against commit `273a4c1` on 2026-07-15. The active goal covers every
vetted audit finding and the motion pass. Execute in this order; each plan is
self-contained and must stay within its stated scope.

## Execution order and status

| Plan | Title | Priority | Effort | Depends on | Status |
|---|---|---|---|---|---|
| 001 | Characterize shared model contracts | P1 | M | none | TODO |
| 002 | Conserve demand and timeline totals | P1 | M | 001 | TODO |
| 003 | Make releases reproducible and self-contained | P1 | M | 001 | TODO |
| 004 | Harden data ingestion and CSV boundaries | P1 | M | 001 | TODO |
| 005 | Repair operator and public-copy drift | P2 | S | 003 | TODO |
| 006 | Defer click-only score detail payloads | P2 | M | 001 | TODO |
| 007 | Make high-frequency interaction motion crisp | P2 | M | 001 | TODO |
| 010 | Briefing pack -- print-ready, citable one-pager | P1 | M | none | DONE |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with reason) | REJECTED.

## Dependency notes

- Plan 001 is characterization first: it protects the intentionally mirrored
  Python and browser runtime before numerical behavior changes.
- Plan 002 changes published scenario and gap values, so it is a release gate.
- Plan 003 makes generated output deterministic before CI can reject stale
  `docs/` artifacts.
- Plan 007 preserves the dashboard's crisp, institutional character; it must
  not add decorative motion to frequent controls.

## Findings considered and rejected

- Missing-archetype records are intentionally skipped and covered by existing
  tests; do not convert that behavior into a validation failure without a
  separate product decision.
- The 3.32 MB all-occupation payload is lazy loaded. Plan 006 targets the
  initial 909 KB payload instead.
- Slider jank needs a browser trace before an incremental-D3 rewrite. Plan 007
  limits the fix to coalescing high-frequency updates.
- Founder-owned uncommitted deletion of the Phase 3 design document is outside
  this backlog; do not restore, stage, or remove it.
