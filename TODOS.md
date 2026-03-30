# TODOS

## Frontend

### Post-Phase-3 icon pass

**What:** Assess whether lightweight icons would improve scanability in cluster dropdowns, pathway cards, and phase legends.

**Why:** Phase 3 shipped with a deliberately text-first UI. A small icon layer may help dense controls without changing the interaction model.

**Context:** If adopted, prefer inline SVG or a very small icon subset over a full icon library.

**Effort:** S  
**Priority:** P3  
**Depends on:** None

## Branding

### HyGOAT branding polish

**What:** Add favicons, Open Graph assets, and any agreed footer/hero polish that is still missing from the live atlas.

**Why:** The data and runtime are now ahead of the surrounding presentation polish.

**Context:** Keep this separate from model/runtime work. Brand assets should be copied into this repo rather than referenced from another project.

**Effort:** M  
**Priority:** P2  
**Depends on:** None

## Testing

### Expand coverage for parse/tabulate pipeline

**What:** Add direct pytest coverage for `parse/parse_occupations.py` and `tabulate/tabulate.py`.

**Why:** Build, scenario, supply, cluster, timeline, pathway, parity, UI-helper, and CSV export coverage now exist. The main remaining test gap is earlier-stage parsing/tabulation behavior.

**Context:** Focus on fixture-based transforms and end-to-end shape checks before the build step consumes the outputs.

**Effort:** M  
**Priority:** P2  
**Depends on:** None

## Data

### Add checked-in PLFS source-occupation supply input

**What:** Provide the missing source labour supply input needed for richer gap-mode reskillable supply estimates.

**Why:** The Phase 3 UI is complete, but `reskillable_supply` remains blank whenever upstream source-occupation labour data is absent.

**Context:** The current build still reports no `model/plfs_supply.json` during asset generation.

**Effort:** M  
**Priority:** P2  
**Depends on:** Data availability
