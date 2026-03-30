# TODOS

## Frontend

*O(n²) recolourTreemap() fix moved to Phase 3 plan (eng decision #10) — no longer deferred.*

## Branding

### HyGOAT branding polish — favicon, OG image, hero, footer

**What:** Ship the branding improvements described in the design doc as a standalone PR, separate from the scenario engine.

**Why:** The atlas is live on GitHub Pages but lacks favicons, Open Graph card, a branded hero section, and a polished footer. These affect credibility with the policy audience (MNRE, MSDE stakeholders).

**Context:** Design doc section "HyGOAT Branding Polish" specifies: (1) favicon set from Pilot repo, (2) OG card image with brand gradient, (3) hero section above treemap, (4) footer with logo + attribution. Brand assets exist at `Pilot\hygoat-nextjs\public\`. This is an external repo dependency — assets must be copied into this repo, not referenced.

**Effort:** M
**Priority:** P2
**Depends on:** None

## Design

*DESIGN.md created during Phase 3 design review (2026-03-30). Covers tokens, components, responsive breakpoints, color semantics, and a11y standards.*

### Evaluate icon usage for Phase 3 UI elements

**What:** Assess whether cluster dropdown items, pathway cards, and phase legend benefit from lightweight icons (e.g., location pin for clusters, arrow for pathway direction, colored circles for phases).

**Why:** The tool is currently text-only. Phase 3 adds dense UI components (pathway cards with 5+ data fields, 10-item cluster dropdown) where icons could improve scanability. The HyGOAT Pilot uses Lucide React icons throughout.

**Context:** Design review flagged this as optional. Pathway cards use overlap-first visual hierarchy with text metadata. Icons could replace "Source → Target" text with a visual arrow, and cluster items could have state abbreviation badges. Evaluate during UI implementation (Phase 3, step 4). If adopted, inline SVG or a lightweight subset of Lucide/Heroicons preferred over a full icon library.

**Effort:** S
**Priority:** P3
**Depends on:** Phase 3 UI integration (step 4)

## Testing

### Retroactive test coverage for existing pipeline

**What:** Add pytest tests for `build/build.py` (merge logic, CSV export, metric computation) and the `parse/tabulate` pipeline.

**Why:** The build output (occupations.json, occupations-all.json) is consumed directly by the live frontend. A regression in build.py corrupts the live site. Currently zero automated tests exist for any part of the pipeline.

**Context:** Phase 1 adds tests for the new scenario engine (compute.py + parity). But the existing pipeline — `parse_occupations.py`, `tabulate.py`, `build.py` — has no coverage. Key functions to test: `merge_scores()`, `compute_upskill_paths()`, `compute_summary_metrics()`, `compute_data_quality()`, `write_h2_csv()`. The scoring pipeline (`score.py`) is less critical since it's run interactively via Claude Code subagents.

**Effort:** M
**Priority:** P2
**Depends on:** Phase 1 test infrastructure (pytest setup, tests/ directory)
