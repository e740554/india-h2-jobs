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

### Automate MoSPI PLFS portal download

**What:** Write a registered-download script for the MoSPI microdata portal so PLFS unit-level files can be refreshed without manual portal interaction.

**Why:** The WHS 2026 sprint shipped the unit-level pipeline with a manual download step. When PLFS 2024-25 ships (annual cadence), repeating the manual flow is friction that delays state-level Phase 2 work and any NGHM-proposal refresh cycle.

**Context:** Portal uses registration + session-bound downloads. Investigate whether a service-account / API path exists or whether scripted form-fill via a headless browser is the realistic path. Captured from /plan-eng-review on 2026-05-11.

**Effort:** M  
**Priority:** P2  
**Depends on:** WHS-2026 unit-level pipeline shipped and stable

### Unit-level PLFS microdata pipeline (post-WHS rebuild)

**What:** Rebuild T0.2 from subdivision-level (Annual Report Statement 16/17) to unit-level (MoSPI microdata portal) PLFS pipeline. Cut from WHS sprint via ER-10 to free capacity for methodology hardening.

**Why:** Subdivision-level is sufficient for WHS demo narrative but unit-level is the correct long-term architecture — it enables state-level supply analysis, occupation-code granularity, and meaningful integration of future PLFS waves. Captured from /plan-eng-review on 2026-05-11 (DeepSeek peer review reversal of ER-1).

**Context:** Existing ~1,802 legacy occupations are the only beneficiaries until NCO-2015 extension is codified (separate TODO). Pair with the "Automate MoSPI PLFS portal download" TODO so the rebuild ships with scripted refresh from day one.

**Effort:** L (4-8 person-days)  
**Priority:** P2  
**Depends on:** "Automate MoSPI PLFS portal download" preferred but not blocking

### Eval suite for LLM occupation scoring reproducibility

**What:** Pin a score baseline (`scores.json` at a specific commit) and write a delta-check that flags any dimension score drifting more than 0.5 on re-run.

**Why:** Phase 2 of RFNBO and Green Iron will re-run `score/score.py`. Without an eval, score drift between LLM runs is invisible and the methodology page's reproducibility claim weakens silently. Captured from /plan-eng-review on 2026-05-11.

**Context:** Eval should run against the existing `prompts/*.txt` and known occupations. Output should be JSON suitable for CI gating. Optional: add to GitHub Actions when occupation set additions are committed.

**Effort:** M  
**Priority:** P2  
**Depends on:** None

## Accessibility

### A11y audit for /methodology and /about pages

**What:** WCAG 2.1 AA audit and fixes for the new `/methodology/` and `/about/` static pages shipped at WHS 2026.

**Why:** Methodology page is the credibility instrument for institutional readers (MNRE, GIZ, EU delegation). Some may use screen readers; failing basic accessibility is a credibility regression. Captured from /plan-eng-review on 2026-05-11.

**Context:** Audit with axe-core or WAVE. Focus on landmark structure, heading hierarchy, link text, and color contrast. Atlas itself is out of scope for v1 audit; focus is on the new credibility-surface pages.

**Effort:** S  
**Priority:** P2  
**Depends on:** /methodology and /about pages shipped (post-WHS 2026)

### /about/ institutional grounding (post-WHS)

**What:** Expand `/about/` beyond the WHS-minimal scope (mailto + Advisory Circle) to include the institutional grounding a hostile credibility-instrument reader expects.

**Why:** The WHS launch ships a deliberately minimal `/about/` (chrome + Advisory Circle + mailto). DeepSeek V4 Pro outside voice flagged this as a credibility liability for a research-grade tool: a hostile labour economist looking for "who built this" finds only a mailto. Captured during /plan-design-review on 2026-05-11.

**Context:** Three concrete additions:
1. Institutional affiliation paragraph for Ekavikalp (India base, one-sentence org description).
2. Funding/sponsorship disclosure (`Independently developed by Ekavikalp. No external funding.` if true).
3. Methodology version + last-update pointer (link or surface the same freshness-badge data shown on /methodology/).

Keep the rest of /about/ as shipped at WHS — minimal, no hero, single column. These additions slot into the existing structure.

**Effort:** S
**Priority:** P2
**Depends on:** Post-WHS bandwidth; nothing technical blocking.

### Telemetry referrer dimension on page-load events

**What:** Tag analytics events with `source=nav:atlas` (when `document.referrer` contains the atlas domain) or `source=direct` (otherwise) on page-load events for `/methodology/` and `/about/`.

**Why:** Lets you measure independent discovery (search, link share, citations) of the methodology/about pages vs nav clicks from the atlas. Critical for evaluating credibility-instrument reach over the WHS week and beyond. Captured during /plan-design-review on 2026-05-11.

**Context:** One extra line in the analytics config. Plausible and Cloudflare's built-in referrer dashboards cover ~80% of this, but a custom dimension lets you slice "WHS-window direct hits to methodology" specifically. Deferred from the WHS sprint because built-in referrer view is acceptable for the launch window.

**Effort:** XS
**Priority:** P3
**Depends on:** None.

## Standards

### NCO-2015 extension proposal for H2-frontier occupations

**What:** Draft a formal proposal to NSO / SSCGJ for codified additions to NCO-2015 covering the H2-frontier occupations the atlas currently ships with synthetic codes (`H2-MAR-*`, `H2-RFNBO-*`, `H2-GREEN-*`).

**Why:** Synthetic codes are honest in the short term but are a long-term maintenance burden and a credibility ceiling on the atlas. Codification by the standards body would also make PLFS supply integration meaningful for these occupations in future PLFS waves. Captured from /plan-eng-review on 2026-05-11.

**Context:** Likely requires advisor input post-WHS (labour economist, SSCGJ contact). Draft can be done internally; submission requires institutional channel. Coordinate with the advisory circle established at WHS.

**Effort:** M  
**Priority:** P3  
**Depends on:** Advisor input from advisory circle (post-WHS 2026)
