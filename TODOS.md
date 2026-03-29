# TODOS

## Frontend

### Optimize recolourTreemap() O(n^2) linear scan

**What:** Replace `data.occupations.find(o => o.id === id)` in `recolourTreemap()` with a pre-built `Map<id, occupation>` lookup.

**Why:** Current implementation is O(n^2) — one linear scan per SVG rect. With 480 occupations this is imperceptible, but Phase 3 may render 1,802 occupations in scenario mode, where the slider triggers frequent recomputes.

**Context:** The `recolourTreemap()` function at `web/main.js.template:369` iterates all `rect[data-id]` elements and calls `data.occupations.find()` for each. Building a `Map` from `id -> occupation` during data load and using `map.get(id)` would make this O(n). The same Map would benefit `selectOccupation()` and upskill path lookups.

**Effort:** S
**Priority:** P3
**Depends on:** None

## Branding

### HyGOAT branding polish — favicon, OG image, hero, footer

**What:** Ship the branding improvements described in the design doc as a standalone PR, separate from the scenario engine.

**Why:** The atlas is live on GitHub Pages but lacks favicons, Open Graph card, a branded hero section, and a polished footer. These affect credibility with the policy audience (MNRE, MSDE stakeholders).

**Context:** Design doc section "HyGOAT Branding Polish" specifies: (1) favicon set from Pilot repo, (2) OG card image with brand gradient, (3) hero section above treemap, (4) footer with logo + attribution. Brand assets exist at `D:\Work\HyGOAT\Pilot\hygoat-nextjs\public\`. This is an external repo dependency — assets must be copied into this repo, not referenced.

**Effort:** M
**Priority:** P2
**Depends on:** None

## Design

### Create DESIGN.md documenting the design system

**What:** Document the project's design system: color palette, typography scale, spacing, component patterns, responsive breakpoints, and the orange=scenario/green=atlas semantic language.

**Why:** The CSS custom properties in `style.css` are comprehensive but undocumented. Future contributors (and the branding PR) need a reference that explains the design decisions — not just the token values, but when to use `--color-hy` vs `--color-goat` and why.

**Context:** The design review established: green (`--color-hy`) for atlas/static elements, orange (`--color-goat`) for scenario/dynamic elements. New components (segmented control, scenario panel, phase bars) extend existing patterns (`.pill`, `.btn-toggle`, `.data-status`). Documenting this prevents drift as features are added. Can be generated from the existing CSS + design review decisions.

**Effort:** S
**Priority:** P3
**Depends on:** None

## Testing

### Retroactive test coverage for existing pipeline

**What:** Add pytest tests for `build/build.py` (merge logic, CSV export, metric computation) and the `parse/tabulate` pipeline.

**Why:** The build output (occupations.json, occupations-all.json) is consumed directly by the live frontend. A regression in build.py corrupts the live site. Currently zero automated tests exist for any part of the pipeline.

**Context:** Phase 1 adds tests for the new scenario engine (compute.py + parity). But the existing pipeline — `parse_occupations.py`, `tabulate.py`, `build.py` — has no coverage. Key functions to test: `merge_scores()`, `compute_upskill_paths()`, `compute_summary_metrics()`, `compute_data_quality()`, `write_h2_csv()`. The scoring pipeline (`score.py`) is less critical since it's run interactively via Claude Code subagents.

**Effort:** M
**Priority:** P2
**Depends on:** Phase 1 test infrastructure (pytest setup, tests/ directory)
