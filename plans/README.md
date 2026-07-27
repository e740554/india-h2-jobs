# Implementation Plans

Plans 001-007 were generated against commit `273a4c1` on 2026-07-15 (audit
hardening and motion pass). Plans 008-012 were generated against commit
`5e754d2` on 2026-07-27 (direction pass: make the atlas useful to skilling
institutions -- NSDC, MSDE, state skill missions). Execute in this order;
each plan is self-contained and must stay within its stated scope.

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
| 008 | Make the atlas citable (CITATION.cff, cite block, sync test) | P1 | S | none (soft: 003) | DONE |
| 009 | Spike the NCVET/NQR qualification layer | P1 | M | none | DONE |
| 010 | Briefing pack -- print-ready, citable one-pager | P1 | M | none (soft: 008) | DONE |
| 011 | Assumptions register: export every coefficient with source | P2 | M | none (soft: 008) | DONE |
| 012 | State views: honest labeling, state summary export, design note | P2 | M | none | DONE |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (with reason) | REJECTED.

## Dependency notes

- Plan 001 is characterization first: it protects the intentionally mirrored
  Python and browser runtime before numerical behavior changes.
- Plan 002 changes published scenario and gap values, so it is a release gate.
- Plan 003 makes generated output deterministic before CI can reject stale
  `docs/` artifacts.
- Plan 007 preserves the dashboard's crisp, institutional character; it must
  not add decorative motion to frequent controls.
- Plan 008 is standalone and cheapest; do it first among the direction plans.
  Plan 003 (reproducible releases) strengthens DOI-per-release later but does
  not block 008.
- Plan 009 is a spike: data + feasibility report only, no runtime or UI
  integration. The integration plan gets scoped from its report.
- Plan 010 reuses Plan 008's citation sentence if 008 landed first; otherwise
  it composes the same sentence itself. Plan 009's qualification data is a
  future enrichment of the briefing table, not a dependency.
- Plan 011's override feature is design-note-only; if it is ever built, Plan
  010's briefing sheet must watermark user-modified runs.
- Plan 012's full state layer (Option C in its design note) depends on the
  `TODOS.md` unit-level PLFS rebuild; only the labeling + export slice is
  buildable now.
- Plans 002 and 006/007 touch `web/main.js.template`; so do 010 and 012.
  Avoid executing them concurrently on the same branch.

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
- (2026-07-27 direction pass) MNRE skilling-proposal alignment as a repo
  feature: rejected as a separate plan -- it is a founder/business action;
  the repo-side enabler is the Plan 010 briefing pack.
- (2026-07-27 direction pass) Adding non-cluster states to the geography
  dropdown: rejected -- they would show zero demand and mislead; Plan 012's
  design note covers the correct path.
- (2026-07-27 direction pass) In-UI coefficient override sliders: deferred to
  a design note (Plan 011 Step 4) -- misattribution risk needs the watermark
  design settled before any build.
- (2026-07-27, Plan 009 spike) Full NQR/NCVET integration (`source_ncvet:
  true` + per-occupation qualifications block): not scoped as a follow-up.
  Neither NQR nor the official NCVET NCO-mapping PDF carries an NCO-2015
  code, and no crosswalk file exists in this repo -- there is no join key to
  integrate on. See `plans/009-spike-report.md`. The one promising thread
  (title-matching the 8 `model/pathways.json` targets against scraped NQR
  qualifications) is narrow enough to revisit later without a full plan.
